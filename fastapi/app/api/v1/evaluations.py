"""Evaluation API endpoints"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.evaluation import (
    AnswerEvaluationResponse,
    ResumeEvaluationResponse,
    OverallInterviewEvaluationCreate,
    OverallInterviewEvaluationResponse,
    FacialAnalysisRequest,
    FacialAnalysisResponse
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.evaluation_service import (
    get_answer_evaluation,
    get_overall_evaluation,
    get_user_overall_evaluations,
    create_overall_evaluation,
    create_response_analysis,
    create_resume_evaluation,
    get_resume_evaluation
)
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


# ============ Answer Evaluations ============

@router.get("/answers/{evaluation_id}", response_model=AnswerEvaluationResponse)
async def get_answer_evaluation_endpoint(
    evaluation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get answer evaluation by ID"""
    evaluation = await get_answer_evaluation(db, evaluation_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer evaluation not found"
        )
    return evaluation


# ============ Overall Interview Evaluations ============

@router.get("/reports/{report_id}", response_model=OverallInterviewEvaluationResponse)
async def get_evaluation_report(
    report_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get evaluation report by ID (report_id = session_id for overall evaluation)"""
    evaluation = await get_overall_evaluation(db, report_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation report not found"
        )
    return evaluation


@router.get("/reports", response_model=PaginatedResponse[OverallInterviewEvaluationResponse])
async def list_evaluation_reports(
    skip: int = 0,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's evaluation reports"""
    evaluations = await get_user_overall_evaluations(
        db, current_user["id"], skip, limit
    )
    total = len(evaluations)
    page_size = limit if limit > 0 else 20
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    page = (skip // page_size) + 1 if page_size > 0 else 1
    return {
        "items": evaluations,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post("/reports", response_model=OverallInterviewEvaluationResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation_report(
    evaluation_data: OverallInterviewEvaluationCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create evaluation report (typically called by backend after interview)"""
    # Verify user ID matches
    if evaluation_data.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create evaluation for another user"
        )
    
    try:
        evaluation = await create_overall_evaluation(db, evaluation_data)
        return evaluation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create evaluation report: {str(e)}"
        )


# ============ Resume Analysis ============

# Allowed file types for resume upload
ALLOWED_RESUME_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}
MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10MB


def _extract_text_from_resume(file_content: bytes, filename: str) -> str:
    """
    Extract text from resume file.
    Supports: .txt (direct), others (placeholder - needs proper parser)
    """
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "txt":
        # Try UTF-8 first, then fallback to other encodings
        for encoding in ["utf-8", "gbk", "gb2312", "latin-1"]:
            try:
                return file_content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return file_content.decode("utf-8", errors="ignore")

    elif ext == "pdf":
        # PDF text extraction requires PyPDF2 or pdfplumber
        # Return placeholder for now - production should use proper library
        try:
            import io
            from PyPDF2 import PdfReader

            pdf_file = io.BytesIO(file_content)
            reader = PdfReader(pdf_file)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
            return "\n".join(text_parts)
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PDF parsing library not available. Please install PyPDF2."
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse PDF: {str(e)}"
            )

    elif ext in ["doc", "docx"]:
        # Word document parsing
        try:
            import io
            from docx import Document

            doc_file = io.BytesIO(file_content)
            doc = Document(doc_file)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Word parsing library not available. Please install python-docx."
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse Word document: {str(e)}"
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: .{ext}. Supported: {', '.join(ALLOWED_RESUME_EXTENSIONS)}"
        )


async def _analyze_resume_with_llm(resume_text: str, user_info: dict) -> dict:
    """
    Analyze resume using LLM.
    Returns: {"score": str, "summary": str}
    """
    from app.core.qwen_client import qwen_chat_json

    # Prepare user context
    major = user_info.get("major", "未提供")
    university = user_info.get("university", "未提供")

    # Build analysis prompt
    system_prompt = """你是一位资深的简历评估专家。请对以下简历进行专业评估，并以JSON格式返回结果。

评估维度：
1. 完整性：个人信息、教育背景、技能、项目/实习经历是否完整
2. 匹配度：简历内容与目标岗位的匹配程度
3. 亮点：是否有突出的技术能力、项目经验或成就
4. 改进空间：简历存在的问题和不足

返回格式：
{
    "score": "数字评分(1-10，如7.5)",
    "summary": "详细的评估总结，包括优势、不足和改进建议，200-300字"
}"""

    user_prompt = f"""用户信息：
- 专业：{major}
- 学校：{university}

简历内容：
{resume_text[:5000]}  # Limit to 5000 chars to avoid token limit

请评估这份简历。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        result = await qwen_chat_json(messages)

        # Extract score and summary
        score = result.get("score", "6.0")
        summary = result.get("summary", "")

        # Ensure score is in valid format
        try:
            float(score)
        except (ValueError, TypeError):
            score = "6.0"

        if not summary:
            summary = "简历分析完成，但未生成详细总结。"

        return {"score": str(score), "summary": summary}

    except Exception as e:
        # LLM analysis failed - return error instead of mock data
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"简历分析服务暂时不可用: {str(e)}"
        )


@router.post("/resumes/analyze", response_model=ResumeEvaluationResponse, status_code=status.HTTP_201_CREATED)
async def analyze_resume(
    file: UploadFile = File(..., description="Resume file (PDF, DOC, DOCX, or TXT)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze resume file using AI.

    - Accepts PDF, DOC, DOCX, or TXT files (max 10MB)
    - Extracts text content from the file
    - Uses LLM to analyze and score the resume
    - Returns score (1-10) and detailed summary with suggestions

    Requires: Authentication
    """
    # Validate file extension
    filename = file.filename or ""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if f".{ext}" not in ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: .{ext}. Allowed: {', '.join(ALLOWED_RESUME_EXTENSIONS)}"
        )

    # Read file content
    try:
        file_content = await file.read()
        if len(file_content) > MAX_RESUME_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Max size: {MAX_RESUME_SIZE / 1024 / 1024}MB"
            )

        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )

    # Extract text from resume
    try:
        resume_text = _extract_text_from_resume(file_content, filename)
        if not resume_text or not resume_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from resume file"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume parsing failed: {str(e)}"
        )

    # Analyze with LLM
    try:
        analysis = await _analyze_resume_with_llm(resume_text, current_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Resume analysis failed: {str(e)}"
        )

    # Save to database
    try:
        evaluation = await create_resume_evaluation(
            db,
            user_id=current_user["id"],
            resume_score=analysis["score"],
            resume_summary=analysis["summary"]
        )
        return evaluation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save evaluation: {str(e)}"
        )


@router.get("/resumes/me", response_model=ResumeEvaluationResponse)
async def get_my_resume_evaluation(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's resume evaluation"""
    evaluation = await get_resume_evaluation(db, current_user["id"])
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume evaluation not found"
        )
    return evaluation


# ============ Facial Analysis ============

import base64
from io import BytesIO


def _analyze_image_basic(image_data: bytes) -> dict:
    """
    Basic image analysis without external ML libraries.
    Analyzes image properties to infer potential emotional state.
    """
    try:
        from PIL import Image, ImageStat

        img = Image.open(BytesIO(image_data))
        stat = ImageStat.Stat(img)

        # Calculate image statistics
        brightness = sum(stat.mean) / len(stat.mean) / 255.0  # 0-1
        contrast = sum(stat.stddev) / len(stat.stddev) / 255.0  # 0-1

        # Simple heuristic-based emotion inference
        # Bright images -> more positive emotions
        # High contrast -> more engaged/expressive
        if brightness > 0.7 and contrast > 0.3:
            expression = "smile"
            emotion = "happy"
            confidence = 0.6 + (brightness - 0.7) * 0.3
        elif brightness > 0.5:
            expression = "neutral"
            emotion = "calm"
            confidence = 0.5 + (brightness - 0.5) * 0.4
        elif brightness > 0.3:
            expression = "neutral"
            emotion = "serious"
            confidence = 0.4 + (0.5 - brightness) * 0.5
        else:
            expression = "neutral"
            emotion = "tired"
            confidence = 0.4 + (0.5 - brightness) * 0.4

        # Adjust confidence based on image quality (contrast)
        confidence = min(0.95, confidence + contrast * 0.1)

        return {
            "expression": expression,
            "emotion": emotion,
            "confidence": round(confidence, 2),
            "brightness": round(brightness, 2),
            "contrast": round(contrast, 2),
        }

    except ImportError:
        # PIL not available, return basic response
        return {
            "expression": "neutral",
            "emotion": "unknown",
            "confidence": 0.5,
            "brightness": None,
            "contrast": None,
        }
    except Exception as e:
        # Image analysis failed
        return {
            "expression": "neutral",
            "emotion": "unknown",
            "confidence": 0.5,
            "brightness": None,
            "contrast": None,
            "error": str(e),
        }


@router.post("/facial/analyze", response_model=FacialAnalysisResponse)
async def analyze_facial_expression(
    request: FacialAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze facial expression from base64 encoded image.

    - Accepts base64 encoded image data
    - Analyzes image brightness and contrast as proxy for emotional state
    - Returns expression, emotion, and confidence score

    Note: This is a simplified implementation. For production use with actual
    facial expression recognition, integrate with cloud vision APIs or
    deploy local ML models (OpenCV + face_recognition / deepface).
    """
    from datetime import datetime, timezone

    try:
        # Decode base64 image
        try:
            image_data = base64.b64decode(request.image_data)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid base64 image data"
            )

        if len(image_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty image data"
            )

        # Perform basic image analysis
        analysis = _analyze_image_basic(image_data)

        return {
            "expression": analysis["expression"],
            "emotion": analysis["emotion"],
            "confidence": analysis["confidence"],
            "timestamp": datetime.now(timezone.utc),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Facial analysis failed: {str(e)}"
        )
