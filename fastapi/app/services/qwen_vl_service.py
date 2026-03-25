"""Qwen-VL service used for recorded interview video evaluation."""

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

import dashscope
import structlog
from openai import AsyncOpenAI

from app.config import get_settings

logger = structlog.get_logger()


@dataclass
class VideoEvaluationResult:
    """Structured result returned from Qwen-VL video analysis."""

    language_expression_score: float
    logical_thinking_score: float
    professional_knowledge_score: float
    communication_skills_score: float
    overall_impression_score: float
    language_expression: str
    logical_thinking: str
    professional_knowledge: str
    communication_skills: str
    overall_impression: str
    overall_score: float
    strengths: List[str]
    weaknesses: List[str]
    suggestions: str
    raw_response: str


class QwenVLService:
    """Qwen-VL service for async video-based interview analysis."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.DASHSCOPE_API_KEY or os.getenv("DASHSCOPE_API_KEY", "")
        self.base_url = getattr(
            settings,
            "DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = "qwen-vl-max-latest"
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

        logger.info(
            "QwenVLService initialized",
            model=self.model,
            base_url=self.base_url,
        )

    def _get_video_url(self, video_path_or_url: str) -> str:
        """Resolve a usable video URL for DashScope/Qwen-VL."""
        if video_path_or_url.startswith(("http://", "https://")):
            return video_path_or_url

        if video_path_or_url.startswith("/uploads/"):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            local_path = os.path.join(base_dir, video_path_or_url.lstrip("/"))
        elif os.path.isfile(video_path_or_url):
            local_path = video_path_or_url
        else:
            raise ValueError(f"Invalid video path: {video_path_or_url}")

        if not os.path.isfile(local_path):
            raise FileNotFoundError(f"Video file not found: {local_path}")

        logger.info("Uploading video to DashScope OSS", local_path=local_path)
        try:
            dashscope.api_key = self.api_key
            response = dashscope.files.Files.upload(
                file_path=local_path,
                purpose=dashscope.files.FilePurpose.assistants,
                api_key=self.api_key,
            )

            if response.status_code == 200:
                uploaded_files = response.output.get("uploaded_files", [])
                if uploaded_files:
                    file_id = uploaded_files[0].get("file_id")
                else:
                    file_id = response.output.get("file_id")

                if not file_id:
                    raise ValueError(f"DashScope upload succeeded but no file_id returned: {response.output}")

                logger.info("Video uploaded successfully", file_id=file_id)
                return file_id

            raise Exception(f"Upload failed: {response.message}")
        except Exception as exc:
            logger.error("Failed to upload video", error=str(exc), local_path=local_path)
            raise

    async def analyze_interview_video(
        self,
        video_url: str,
        scenario_name: str = "技术面试",
        conversation_history: Optional[List[Dict]] = None,
    ) -> VideoEvaluationResult:
        """Analyze an interview video with optional conversation context."""
        try:
            logger.info(
                "Analyzing interview video",
                video_url=video_url[:100] + "..." if len(video_url) > 100 else video_url,
                scenario=scenario_name,
            )

            actual_video_url = self._get_video_url(video_url)
            prompt = self._build_evaluation_prompt(scenario_name, conversation_history)

            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "video",
                                "video": actual_video_url,
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            raw_response = completion.choices[0].message.content
            result = self._parse_evaluation_response(raw_response)

            logger.info(
                "Video analysis completed",
                scenario=scenario_name,
                score=result.overall_score,
            )

            return result
        except Exception as exc:
            logger.error("Error analyzing video", error=str(exc), video_url=video_url)
            return self._create_fallback_result(str(exc))

    def _build_evaluation_prompt(
        self,
        scenario_name: str,
        conversation_history: Optional[List[Dict]] = None,
    ) -> str:
        """Build the evaluation prompt for Qwen-VL."""
        history_text = ""
        if conversation_history:
            history_lines = []
            for msg in conversation_history[-10:]:
                role = "面试官" if msg.get("role") == "assistant" else "候选人"
                history_lines.append(f"{role}: {msg.get('content', '')}")
            history_text = "\n\n面试对话记录：\n" + "\n".join(history_lines)

        return f"""你是一位专业的面试评估专家。请观看这段{scenario_name}的视频，并结合候选人与面试官的对话记录，对候选人的整体表现进行评估。{history_text}

请从以下维度评估候选人：
1. 语言表达能力
2. 逻辑思维能力
3. 专业知识掌握
4. 沟通技巧
5. 整体印象

请严格按照下面的结构输出：

【评分】X/100

【维度评分】
- 语言表达能力：X/100
- 逻辑思维能力：X/100
- 专业知识掌握：X/100
- 沟通技巧：X/100
- 整体印象：X/100

【语言表达能力】
具体评价内容

【逻辑思维能力】
具体评价内容

【专业知识掌握】
具体评价内容

【沟通技巧】
具体评价内容

【整体印象】
具体评价内容

【优点】
- 优点1
- 优点2

【待改进】
- 待改进1
- 待改进2

【建议】
给候选人的具体改进建议"""

    def _parse_evaluation_response(self, response: str) -> VideoEvaluationResult:
        """Parse the Qwen-VL response into a structured result."""
        overall_score = self._extract_main_score(response)
        dimension_scores = self._extract_dimension_scores(response, overall_score)
        sections = self._extract_sections(response)
        strengths = self._extract_list_items(response, "优点", "待改进")
        weaknesses = self._extract_list_items(response, "待改进", "建议")

        return VideoEvaluationResult(
            language_expression_score=dimension_scores["language_expression_score"],
            logical_thinking_score=dimension_scores["logical_thinking_score"],
            professional_knowledge_score=dimension_scores["professional_knowledge_score"],
            communication_skills_score=dimension_scores["communication_skills_score"],
            overall_impression_score=dimension_scores["overall_impression_score"],
            language_expression=sections.get("语言表达能力", ""),
            logical_thinking=sections.get("逻辑思维能力", ""),
            professional_knowledge=sections.get("专业知识掌握", ""),
            communication_skills=sections.get("沟通技巧", ""),
            overall_impression=sections.get("整体印象", ""),
            overall_score=overall_score,
            strengths=strengths or ["表达较自然", "配合面试节奏较好"],
            weaknesses=weaknesses or ["仍可进一步强化细节论证"],
            suggestions=sections.get("建议", "继续加强结构化表达，并针对关键问题补充细节。"),
            raw_response=response,
        )

    def _extract_main_score(self, response: str) -> float:
        match = re.search(r"【评分】\s*(\d+(?:\.\d+)?)\s*/\s*100", response)
        if match:
            return float(match.group(1))
        return 75.0

    def _extract_dimension_scores(self, response: str, fallback_score: float) -> Dict[str, float]:
        def find_score(label: str) -> float:
            patterns = [
                rf"{re.escape(label)}[：:]\s*(\d+(?:\.\d+)?)\s*/\s*100",
                rf"{re.escape(label)}\s*(\d+(?:\.\d+)?)\s*/\s*100",
            ]
            for pattern in patterns:
                match = re.search(pattern, response)
                if match:
                    return float(match.group(1))
            return fallback_score

        return {
            "language_expression_score": find_score("语言表达能力"),
            "logical_thinking_score": find_score("逻辑思维能力"),
            "professional_knowledge_score": find_score("专业知识掌握"),
            "communication_skills_score": find_score("沟通技巧"),
            "overall_impression_score": find_score("整体印象"),
        }

    def _extract_sections(self, response: str) -> Dict[str, str]:
        sections: Dict[str, str] = {}
        pattern = r"【([^】]+)】\s*\n(.*?)(?=\n【|\Z)"
        for title, content in re.findall(pattern, response, re.DOTALL):
            sections[title.strip()] = content.strip()
        return sections

    def _extract_list_items(self, response: str, start_marker: str, end_marker: str) -> List[str]:
        pattern = rf"【{re.escape(start_marker)}】(.*?)【{re.escape(end_marker)}】"
        match = re.search(pattern, response, re.DOTALL)
        if not match:
            return []

        items = []
        for item in re.findall(r"[-•]\s*(.+?)(?=\n|$)", match.group(1)):
            text = item.strip()
            if text:
                items.append(text)
        return items

    def _create_fallback_result(self, error_message: str) -> VideoEvaluationResult:
        """Return a safe fallback result when model analysis fails."""
        return VideoEvaluationResult(
            language_expression_score=0.0,
            logical_thinking_score=0.0,
            professional_knowledge_score=0.0,
            communication_skills_score=0.0,
            overall_impression_score=0.0,
            language_expression="视频分析过程中出现错误，暂时无法给出语言表达评估。",
            logical_thinking="视频分析过程中出现错误，暂时无法给出逻辑思维评估。",
            professional_knowledge="视频分析过程中出现错误，暂时无法给出专业知识评估。",
            communication_skills="视频分析过程中出现错误，暂时无法给出沟通技巧评估。",
            overall_impression="视频分析过程中出现错误，暂时无法给出整体印象。",
            overall_score=0.0,
            strengths=["暂无法评估"],
            weaknesses=["视频分析失败"],
            suggestions=f"视频分析出现问题：{error_message}。请稍后重试或联系技术支持。",
            raw_response=f"Error: {error_message}",
        )

    async def batch_analyze_videos(
        self,
        video_urls: List[str],
        scenario_name: str = "技术面试",
    ) -> List[VideoEvaluationResult]:
        """Batch analyze multiple videos."""
        results = []
        for url in video_urls:
            results.append(await self.analyze_interview_video(url, scenario_name))
        return results


_qwen_vl_service: Optional[QwenVLService] = None


def get_qwen_vl_service() -> QwenVLService:
    """Return the shared Qwen-VL service instance."""
    global _qwen_vl_service
    if _qwen_vl_service is None:
        _qwen_vl_service = QwenVLService()
    return _qwen_vl_service
