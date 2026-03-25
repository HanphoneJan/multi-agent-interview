"""Evaluation related Celery tasks"""
import asyncio

from celery import Task

from app.config import get_settings
from app.core.qwen_client import qwen_chat_json
from app.core.prompts import EVALUATION_PROMPT, REPORT_PROMPT
from app.core.constants import (
    DEFAULT_EVALUATION_SCORE,
    DEFAULT_STRENGTHS,
    DEFAULT_WEAKNESSES,
    DEFAULT_EVALUATION_UNAVAILABLE,
    DEFAULT_OVERALL_EVALUATION,
    DEFAULT_IMPROVEMENT_ADVICE,
    DEFAULT_REPORT_SCORE,
    QWEN_NOT_CONFIGURED_EVAL,
    NO_RECORDS_EVALUATION,
    NO_RECORDS_ADVICE,
    QWEN_NOT_CONFIGURED_REPORT,
    QWEN_CONFIG_ADVICE,
)
from app.tasks.celery_app import celery_app
from app.utils.log_helper import get_logger

logger = get_logger("tasks.evaluation")


class AsyncTask(Task):
    """Base class for async tasks"""

    _loop = None

    @property
    def loop(self):
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop


async def _evaluate_answer_with_qwen(answer_text: str) -> dict:
    """使用 Qwen 评估面试回答。"""
    prompt = EVALUATION_PROMPT.format(answer_text=answer_text or "（未提供回答内容）")
    messages = [{"role": "user", "content": prompt}]
    raw = await qwen_chat_json(messages)

    evaluation_text = raw.get("evaluation_text") or DEFAULT_EVALUATION_UNAVAILABLE
    score = raw.get("score")
    if score is not None:
        try:
            score = float(score)
            score = max(0.0, min(1.0, score))
        except (TypeError, ValueError):
            score = DEFAULT_EVALUATION_SCORE
    else:
        score = DEFAULT_EVALUATION_SCORE

    strengths = raw.get("strengths")
    if not isinstance(strengths, list):
        strengths = DEFAULT_STRENGTHS if evaluation_text else []

    weaknesses = raw.get("weaknesses")
    if not isinstance(weaknesses, list):
        weaknesses = DEFAULT_WEAKNESSES if evaluation_text else []

    return {
        "evaluation_text": evaluation_text,
        "score": score,
        "strengths": strengths[:5],
        "weaknesses": weaknesses[:5],
    }


@celery_app.task(base=AsyncTask, bind=True, name="evaluate_answer")
def evaluate_answer_task(self, question_id: int, answer_text: str):
    """
    Evaluate a user's answer asynchronously using Qwen LLM.

    Args:
        question_id: ID of the question being evaluated
        answer_text: User's answer text

    Returns:
        Evaluation result with score and feedback
    """
    if not get_settings().QWEN_API_KEY:
        logger.warning("QWEN_API_KEY 未配置，使用占位评估")
        return {
            "question_id": question_id,
            "evaluation_text": QWEN_NOT_CONFIGURED_EVAL,
            "score": DEFAULT_EVALUATION_SCORE,
            "strengths": [],
            "weaknesses": [],
        }

    try:
        result = self.loop.run_until_complete(_evaluate_answer_with_qwen(answer_text))
        result["question_id"] = question_id
        return result
    except Exception as e:
        logger.exception(f"Qwen 评估失败: {e}")
        return {
            "question_id": question_id,
            "evaluation_text": f"评估暂时失败: {str(e)}",
            "score": DEFAULT_EVALUATION_SCORE,
            "strengths": [],
            "weaknesses": [],
        }


async def _generate_report_with_qwen(session_id: int, user_id: int) -> dict:
    """使用 Qwen 生成面试整体报告。"""
    from sqlalchemy import select

    from app.database import async_session_factory
    from app.models.interview import interview_questions, interview_sessions
    from app.models.evaluation import (
        answer_evaluations,
        response_analysis,
        response_metadata,
    )

    async with async_session_factory() as db:
        # 获取该 session 下所有问题及其评估
        q = (
            select(
                interview_questions.c.question_text,
                response_analysis.c.speech_text,
                answer_evaluations.c.evaluation_text,
                answer_evaluations.c.score,
            )
            .select_from(interview_questions)
            .outerjoin(
                response_metadata,
                response_metadata.c.question_id == interview_questions.c.id,
            )
            .outerjoin(
                response_analysis,
                response_analysis.c.metadata_id == response_metadata.c.id,
            )
            .outerjoin(
                answer_evaluations,
                (answer_evaluations.c.question_id == interview_questions.c.id)
                & (answer_evaluations.c.analysis_id == response_analysis.c.id),
            )
            .where(interview_questions.c.session_id == session_id)
        )
        result = await db.execute(q)
        rows = result.all()

        if user_id <= 0:
            r = await db.execute(
                select(interview_sessions.c.user_id).where(
                    interview_sessions.c.id == session_id
                )
            )
            u = r.scalar_one_or_none()
            if u is not None:
                user_id = u

    if not rows:
        return {
            "session_id": session_id,
            "user_id": user_id,
            "overall_score": "0",
            "overall_evaluation": NO_RECORDS_EVALUATION,
            "help": NO_RECORDS_ADVICE,
            "recommendation": "",
        }

    lines = []
    for i, row in enumerate(rows, 1):
        q_text = row.question_text or ""
        a_text = row.speech_text or ""
        eval_text = row.evaluation_text or ""
        score = row.score if row.score is not None else 0
        lines.append(
            f"问题{i}: {q_text}\n回答: {a_text[:200]}...\n评估: {eval_text[:150]}... 得分: {score}"
        )
    qa_text = "\n\n".join(lines)

    if not get_settings().QWEN_API_KEY:
        return {
            "session_id": session_id,
            "user_id": user_id,
            "overall_score": str(int(DEFAULT_REPORT_SCORE)),
            "overall_evaluation": QWEN_NOT_CONFIGURED_REPORT,
            "help": QWEN_CONFIG_ADVICE,
            "recommendation": "",
        }

    prompt = REPORT_PROMPT.format(qa_evaluations=qa_text)
    messages = [{"role": "user", "content": prompt}]
    raw = await qwen_chat_json(messages)

    def _score(val, default: float = DEFAULT_REPORT_SCORE) -> str:
        if val is None:
            return str(int(default))
        try:
            return str(int(min(100, max(0, float(val)))))
        except (TypeError, ValueError):
            return str(int(default))

    return {
        "session_id": session_id,
        "user_id": user_id,
        "overall_score": _score(raw.get("overall_score"), 75),
        "overall_evaluation": raw.get("overall_evaluation") or DEFAULT_OVERALL_EVALUATION,
        "help": raw.get("help") or DEFAULT_IMPROVEMENT_ADVICE,
        "recommendation": raw.get("recommendation") or "",
        "professional_knowledge": _score(raw.get("professional_knowledge"), DEFAULT_REPORT_SCORE),
        "skill_match": _score(raw.get("skill_match"), DEFAULT_REPORT_SCORE),
        "language_expression": _score(raw.get("language_expression"), DEFAULT_REPORT_SCORE),
        "logical_thinking": _score(raw.get("logical_thinking"), DEFAULT_REPORT_SCORE),
        "stress_response": _score(raw.get("stress_response"), DEFAULT_REPORT_SCORE),
        "personality": _score(raw.get("personality"), DEFAULT_REPORT_SCORE),
        "motivation": _score(raw.get("motivation"), DEFAULT_REPORT_SCORE),
        "value": _score(raw.get("value"), DEFAULT_REPORT_SCORE),
    }


@celery_app.task(base=AsyncTask, bind=True, name="generate_report")
def generate_report_task(self, session_id: int, user_id: int = 0):
    """
    Generate interview evaluation report asynchronously using Qwen LLM.

    Args:
        session_id: ID of the interview session
        user_id: User ID (optional, for session lookup)

    Returns:
        Generated report data
    """
    try:
        return self.loop.run_until_complete(
            _generate_report_with_qwen(session_id, user_id)
        )
    except Exception as e:
        logger.exception(f"报告生成失败: {e}")
        return {
            "session_id": session_id,
            "user_id": user_id,
            "overall_score": "0",
            "overall_evaluation": f"报告生成失败: {str(e)}",
            "help": "",
            "recommendation": "",
        }


@celery_app.task(base=AsyncTask, bind=True, name="analyze_resume")
def analyze_resume_task(self, user_id: int, resume_file_path: str):
    """
    Analyze resume asynchronously.

    Args:
        user_id: ID of the user
        resume_file_path: Path to the resume file

    Returns:
        Resume analysis result
    """
    # TODO: Integrate with resume parsing engine
    return {
        "user_id": user_id,
        "resume_score": "80",
        "resume_summary": "Resume summary placeholder",
        "skills": ["Python", "Django", "SQL"],
    }
