"""RAG-based recommender for interview reports"""
import asyncio
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.qwen_client import qwen_chat_json
from app.core.prompts import RAG_PROMPT_TEMPLATE
from app.core.constants import (
    WEAK_AREA_THRESHOLD,
    EVALUATION_DIMENSION_NAMES,
    RAG_EVALUATION_NOT_FOUND,
    RAG_NO_WEAK_AREAS_ADVICE,
    RAG_NO_RESOURCES_ADVICE,
    RAG_NO_VECTOR_RESULTS_ADVICE,
    RAG_FALLBACK_ADVICE,
    RAG_DEFAULT_ADVICE,
)
from app.models.evaluation import overall_interview_evaluations
from app.models.learning import resources
from app.recommenders.base import BaseRecommender
from app.recommenders.embedding_service import EmbeddingService
from app.utils.log_helper import get_logger

logger = get_logger("recommenders.rag")


class RAGRecommender(BaseRecommender):
    """
    RAG-based recommender for interview reports.

    Recommends learning resources based on interview evaluation results:
    - Uses vector search to find relevant resources
    - Generates personalized recommendation reasons using LLM
    """

    def __init__(self, embedding_service: EmbeddingService | None = None, llm_engine: Any | None = None):
        """
        Initialize RAG recommender.

        Args:
            embedding_service: EmbeddingService instance for vector search
            llm_engine: LLM engine for generating recommendations (默认使用 Qwen 通义千问)
        """
        super().__init__("rag")
        self.embedding_service = embedding_service or EmbeddingService()
        self.llm_engine = llm_engine

    def recommend(
        self,
        evaluation_id: int,
        limit: int = 5,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Generate RAG-based recommendations.

        Args:
            evaluation_id: ID of the evaluation record
            limit: Maximum number of recommendations
            filters: Optional filters (difficulty, resource_type, etc.)

        Returns:
            List of recommendations with detailed reasons
        """
        raise NotImplementedError("Use async version: async_recommend")

    async def async_recommend(
        self,
        db: AsyncSession,
        evaluation_id: int,
        limit: int = 5,
        filters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Generate RAG-based recommendations for an interview evaluation.

        Args:
            db: Database session
            evaluation_id: ID of the evaluation record
            limit: Maximum number of recommendations
            filters: Optional filters (difficulty, resource_type, etc.)

        Returns:
            Dict with weak_areas, recommendations, and overall_advice
        """
        filters = filters or {}

        # Step 1: Get evaluation result
        evaluation = await self._get_evaluation(db, evaluation_id)
        if not evaluation:
            logger.error(f"Evaluation {evaluation_id} not found")
            return {"weak_areas": [], "recommendations": [], "overall_advice": RAG_EVALUATION_NOT_FOUND}

        # Step 2: Identify weak areas
        weak_areas = self._identify_weak_areas(evaluation)

        if not weak_areas:
            logger.info(f"No weak areas identified for evaluation {evaluation_id}")
            return {
                "weak_areas": [],
                "recommendations": [],
                "overall_advice": RAG_NO_WEAK_AREAS_ADVICE,
            }

        # Step 3: Build query for vector search
        query_text = self._build_query_text(evaluation, weak_areas)

        # Step 4: Get all resources and apply filters
        all_resources = await self._get_all_resources(db)
        filtered_resources = self._apply_filters(all_resources, filters)

        if not filtered_resources:
            logger.info("No resources match the filters")
            return {"weak_areas": weak_areas, "recommendations": [], "overall_advice": RAG_NO_RESOURCES_ADVICE}

        # Step 5: Vector search for relevant resources
        top_resources = await self._vector_search(query_text, filtered_resources, k=limit * 2)

        if not top_resources:
            logger.warning("No resources found via vector search")
            return {"weak_areas": weak_areas, "recommendations": [], "overall_advice": RAG_NO_VECTOR_RESULTS_ADVICE}

        # Step 6: Generate LLM-based recommendations（使用 Qwen 或注入的 engine）
        use_llm = self.llm_engine is not None or bool(get_settings().QWEN_API_KEY)
        if use_llm:
            result = await self._generate_llm_recommendations(evaluation, top_resources[:limit])
        else:
            result = self._generate_fallback_recommendations(top_resources[:limit])

        result["weak_areas"] = weak_areas

        return result

    async def _get_evaluation(
        self,
        db: AsyncSession,
        evaluation_id: int
    ) -> dict[str, Any] | None:
        """
        Get evaluation result by ID.

        Args:
            db: Database session
            evaluation_id: Evaluation ID

        Returns:
            Evaluation dict or None
        """
        query = select(overall_interview_evaluations).where(
            overall_interview_evaluations.c.id == evaluation_id
        )

        result = await db.execute(query)
        row = result.first()

        if not row:
            return None

        def _float(val, default: float = 0.0) -> float:
            if val is None:
                return default
            try:
                return float(val)
            except (TypeError, ValueError):
                return default

        rec = dict(row._mapping) if hasattr(row, "_mapping") else dict(zip(row.keys(), row))
        return {
            "id": rec.get("id"),
            "session_id": rec.get("session_id"),
            "user_id": rec.get("user_id"),
            "overall_evaluation": rec.get("overall_evaluation", ""),
            "overall_score": _float(rec.get("overall_score")),
            "professional_knowledge": _float(rec.get("professional_knowledge")),
            "skill_match": _float(rec.get("skill_match")),
            "language_expression": _float(rec.get("language_expression")),
            "logical_thinking": _float(rec.get("logical_thinking")),
            "stress_response": _float(rec.get("stress_response")),
            "personality": _float(rec.get("personality")),
            "motivation": _float(rec.get("motivation")),
            "value": _float(rec.get("value")),
        }

    def _identify_weak_areas(self, evaluation: dict[str, Any]) -> list[str]:
        """
        Identify weak areas based on evaluation scores.

        Args:
            evaluation: Evaluation dict

        Returns:
            List of weak area names
        """
        weak_areas = []
        for key, name in EVALUATION_DIMENSION_NAMES.items():
            score = evaluation.get(key, 0)
            if score < WEAK_AREA_THRESHOLD:
                weak_areas.append(name)

        return weak_areas

    def _build_query_text(
        self,
        evaluation: dict[str, Any],
        weak_areas: list[str]
    ) -> str:
        """
        Build query text for vector search.

        Args:
            evaluation: Evaluation dict
            weak_areas: List of weak area names

        Returns:
            Combined query text
        """
        parts = []

        # Overall evaluation
        if evaluation.get("overall_evaluation"):
            parts.append(evaluation["overall_evaluation"])

        # Weak areas as keywords
        if weak_areas:
            parts.append("薄弱领域: " + ", ".join(weak_areas))

        # Dimension scores
        parts.append(f"总分: {evaluation.get('overall_score', 0)}")
        parts.append(f"专业知识: {evaluation.get('professional_knowledge', 0)}")
        parts.append(f"逻辑思维: {evaluation.get('logical_thinking', 0)}")

        return " ".join(parts)

    async def _get_all_resources(self, db: AsyncSession) -> list[dict[str, Any]]:
        """
        Get all resources from database.

        Args:
            db: Database session

        Returns:
            List of resource dicts
        """
        query = select(resources)
        result = await db.execute(query)

        return [
            {
                "id": row[0],
                "name": row[1],
                "resource_type": row[2],
                "tags": row[3],
                "url": row[4],
                "duration_or_quantity": row[5],
                "difficulty": row[6],
                "views": row[7],
                "completions": row[8],
                "rating": row[9],
            }
            for row in result
        ]

    def _apply_filters(
        self,
        resources: list[dict[str, Any]],
        filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Apply filters to resources.

        Args:
            resources: List of resources
            filters: Filter dict

        Returns:
            Filtered list of resources
        """
        if not filters:
            return resources

        filtered = []

        for resource in resources:
            # Difficulty filter
            if "difficulty" in filters and filters["difficulty"]:
                if resource.get("difficulty") != filters["difficulty"]:
                    continue

            # Resource type filter
            if "resource_type" in filters and filters["resource_type"]:
                if resource.get("resource_type") != filters["resource_type"]:
                    continue

            filtered.append(resource)

        return filtered

    async def _vector_search(
        self,
        query_text: str,
        resources: list[dict[str, Any]],
        k: int = 10
    ) -> list[dict[str, Any]]:
        """
        Perform vector search to find relevant resources.

        Args:
            query_text: Query text for embedding
            resources: List of candidate resources
            k: Number of top results

        Returns:
            List of resources sorted by similarity
        """
        # Get query embedding
        query_embedding = self.embedding_service.get_embedding(query_text)

        # Get resource embeddings
        resource_texts = [
            self.embedding_service.build_resource_text(r)
            for r in resources
        ]
        resource_embeddings = self.embedding_service.get_embeddings_batch(resource_texts)

        # Get top-k similar resources
        resource_ids = [r["id"] for r in resources]
        top_results = self.embedding_service.get_top_k_similar(
            query_embedding,
            resource_embeddings,
            resource_ids,
            k
        )

        # Add similarity scores to resources
        results_by_id = {r["id"]: r for r in resources}
        recommendations = []

        for resource_id, similarity in top_results:
            resource = results_by_id.get(resource_id)
            if resource:
                resource_copy = resource.copy()
                resource_copy["similarity"] = similarity
                recommendations.append(resource_copy)

        return recommendations

    async def _generate_llm_recommendations(
        self,
        evaluation: dict[str, Any],
        resources: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Generate LLM-based recommendations.

        Args:
            evaluation: Evaluation dict
            resources: List of candidate resources

        Returns:
            Dict with recommendations and overall_advice
        """
        # Format resources for prompt
        resources_text = "\n".join([
            f"- 资源ID: {r['id']}, 名称: {r['name']}, 类型: {r['resource_type']}, "
            f"标签: {r.get('tags', '')}, 难度: {r.get('difficulty', '')}"
            for r in resources
        ])

        # Build prompt
        prompt = RAG_PROMPT_TEMPLATE.format(
            professional_knowledge=evaluation.get("professional_knowledge", 0),
            skill_match=evaluation.get("skill_match", 0),
            language_expression=evaluation.get("language_expression", 0),
            logical_thinking=evaluation.get("logical_thinking", 0),
            stress_response=evaluation.get("stress_response", 0),
            personality=evaluation.get("personality", 0),
            motivation=evaluation.get("motivation", 0),
            value=evaluation.get("value", 0),
            overall_evaluation=evaluation.get("overall_evaluation", ""),
            resources=resources_text,
            weak_area_threshold=WEAK_AREA_THRESHOLD,
        )

        # 优先使用注入的 llm_engine，否则使用 Qwen
        if self.llm_engine is not None:
            return await self._generate_llm_recommendations_via_engine(
                prompt, resources, self.llm_engine
            )
        return await self._generate_llm_recommendations_via_qwen(prompt, resources)

    async def _generate_llm_recommendations_via_qwen(
        self, prompt: str, resources: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """使用 Qwen 通义千问生成推荐。"""
        if not get_settings().QWEN_API_KEY:
            logger.warning("QWEN_API_KEY 未配置，使用 fallback 推荐")
            return self._generate_fallback_recommendations(resources)

        messages = [{"role": "user", "content": prompt}]
        try:
            raw = await qwen_chat_json(messages)
        except Exception as e:
            logger.warning(f"Qwen 调用失败: {e}，使用 fallback")
            return self._generate_fallback_recommendations(resources)

        return self._map_llm_result_to_output(raw, resources)

    async def _generate_llm_recommendations_via_engine(
        self,
        prompt: str,
        resources: list[dict[str, Any]],
        engine: Any,
    ) -> dict[str, Any]:
        """通过注入的 LLM engine 生成推荐。engine 应为 async def (messages) -> dict。"""
        messages = [{"role": "user", "content": prompt}]
        try:
            if asyncio.iscoroutinefunction(engine):
                raw = await engine(messages)
            else:
                raw = await asyncio.to_thread(engine, messages)
        except Exception as e:
            logger.warning(f"LLM engine 调用失败: {e}，使用 fallback")
            return self._generate_fallback_recommendations(resources)

        return self._map_llm_result_to_output(raw, resources)

    def _map_llm_result_to_output(
        self, raw: dict[str, Any], resources: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """将 LLM 返回的 JSON 映射为统一输出格式。"""
        weak_areas = raw.get("weak_areas") or []
        overall_advice = raw.get("overall_advice") or RAG_DEFAULT_ADVICE
        recs_raw = raw.get("recommendations") or []

        resources_by_id = {r["id"]: r for r in resources}
        recommendations = []

        for rec in recs_raw:
            rid = rec.get("resource_id")
            if rid is None:
                continue
            base = resources_by_id.get(rid)
            if not base:
                continue
            recommendations.append({
                "resource_id": rid,
                "resource_name": rec.get("resource_name") or base["name"],
                "resource_type": base.get("resource_type"),
                "tags": base.get("tags", ""),
                "url": base.get("url"),
                "duration_or_quantity": base.get("duration_or_quantity"),
                "difficulty": base.get("difficulty"),
                "similarity": base.get("similarity"),
                "reason": rec.get("reason", ""),
            })

        if not recommendations:
            return self._generate_fallback_recommendations(resources)

        return {
            "recommendations": recommendations,
            "overall_advice": overall_advice,
        }

    def _generate_fallback_recommendations(
        self,
        resources: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Generate fallback recommendations without LLM.

        Args:
            resources: List of resources

        Returns:
            Dict with recommendations and overall_advice
        """
        recommendations = []

        for r in resources:
            similarity = r.get("similarity", 0)
            recommendations.append({
                "resource_id": r["id"],
                "resource_name": r["name"],
                "resource_type": r["resource_type"],
                "tags": r.get("tags", ""),
                "url": r["url"],
                "duration_or_quantity": r["duration_or_quantity"],
                "difficulty": r.get("difficulty"),
                "similarity": similarity,
                "reason": f"与评估结果相似度: {similarity:.2f}"
            })

        overall_advice = RAG_FALLBACK_ADVICE

        return {
            "recommendations": recommendations,
            "overall_advice": overall_advice
        }

    def train(self):
        """No training needed for RAG recommender"""
        logger.info("RAG recommender: No training needed")
