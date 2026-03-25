# RAG与推荐系统设计详解

> 深入剖析RAG检索增强生成和混合推荐系统实现

## 一、什么是RAG？

### 1.1 概念解释

**RAG** = **R**etrieval-**A**ugmented **G**eneration（检索增强生成）

**通俗理解**：

想象你在开卷考试：
- **传统LLM**：闭卷考试，只能凭记忆回答
- **RAG**：开卷考试，先查资料再回答

```
传统LLM:                    RAG:
问题 ──────> LLM ──────> 回答    问题 ───> 检索资料 ───> 上下文 + 问题 ───> LLM ───> 回答
                              ↑______________|
                              (检索到的相关内容)
```

### 1.2 RAG的优势

| 优势 | 说明 |
|-----|------|
| 解决幻觉 | LLM基于检索到的真实资料回答，减少编造 |
| 知识时效性 | 可以检索最新资料，不受训练数据时间限制 |
| 可溯源 | 回答基于具体资料，可以给出引用来源 |
| 领域适配 | 通过构建领域知识库，适配特定领域 |

---

## 二、本项目的RAG实现

### 2.1 应用场景

面试结束后，根据评估结果推荐学习资源：

```
面试评估结果
    │
    ├── 专业知识: 60分 (薄弱)
    ├── 逻辑思维: 85分 (良好)
    └── 语言表达: 70分 (一般)
    │
    ▼
RAG推荐系统
    │
    ├── 向量化查询: "专业知识60分 逻辑思维85分 Python基础薄弱..."
    │
    ├── 向量检索 ───> 找到相关学习资源(算法/数据结构/Python教程)
    │
    └── LLM生成推荐理由 ───> "根据您的评估，建议在Python基础上加强学习..."
```

### 2.2 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RAG推荐流程                                  │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │  面试评估结果  │
  │ (8维度分数)   │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐     识别薄弱领域
  │  构建查询文本  │◄──── (分数<60)
  │ (Query Text) │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐     sentence-transformers
  │   文本向量化   │◄──── all-MiniLM-L6-v2
  │  (384维向量)  │      多语言支持
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐     余弦相似度
  │  向量相似度检索 │◄──── Top-K召回
  │  (Milvus)    │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐     通义千问
  │  LLM生成推荐  │◄---- 生成推荐理由
  │  (Qwen)      │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │  个性化推荐结果 │
  │ (资源+理由)   │
  └──────────────┘
```

### 2.3 核心代码解析

文件：`app/recommenders/rag_recommender.py`

#### Step 1: 识别薄弱领域

```python
def _identify_weak_areas(self, evaluation: dict) -> list[str]:
    """识别薄弱领域 - 分数低于阈值的维度"""
    weak_areas = []
    threshold = WEAK_AREA_THRESHOLD  # 60分

    # 8个评估维度
    dimensions = {
        "professional_knowledge": "专业知识",
        "skill_match": "技能匹配",
        "language_expression": "语言表达",
        "logical_thinking": "逻辑思维",
        "stress_response": "抗压能力",
        "personality": "性格特质",
        "motivation": "求职动机",
        "value": "价值观匹配",
    }

    for key, name in dimensions.items():
        score = evaluation.get(key, 0)
        if score < threshold:
            weak_areas.append(name)

    return weak_areas
```

#### Step 2: 构建查询文本

```python
def _build_query_text(self, evaluation: dict, weak_areas: list) -> str:
    """构建用于向量搜索的查询文本"""
    parts = []

    # 总体评价
    if evaluation.get("overall_evaluation"):
        parts.append(evaluation["overall_evaluation"])

    # 薄弱领域
    if weak_areas:
        parts.append("薄弱领域: " + ", ".join(weak_areas))

    # 维度分数
    parts.append(f"总分: {evaluation.get('overall_score', 0)}")
    parts.append(f"专业知识: {evaluation.get('professional_knowledge', 0)}")
    parts.append(f"逻辑思维: {evaluation.get('logical_thinking', 0)}")

    return " ".join(parts)
```

#### Step 3: 向量检索

```python
async def _vector_search(
    self,
    query_text: str,
    resources: list[dict],
    k: int = 10
) -> list[dict]:
    """向量搜索 - 找到最相关的学习资源"""

    # 1. 查询文本向量化
    query_embedding = self.embedding_service.get_embedding(query_text)

    # 2. 资源批量向量化
    resource_texts = [
        self.embedding_service.build_resource_text(r)
        for r in resources
    ]
    resource_embeddings = self.embedding_service.get_embeddings_batch(resource_texts)

    # 3. 计算相似度，返回Top-K
    top_results = self.embedding_service.get_top_k_similar(
        query_embedding,
        resource_embeddings,
        resource_ids=[r["id"] for r in resources],
        k=k
    )

    return top_results
```

#### Step 4: LLM生成推荐理由

```python
async def _generate_llm_recommendations(
    self,
    evaluation: dict,
    resources: list[dict]
) -> dict:
    """使用LLM生成个性化推荐理由"""

    # 构建Prompt
    prompt = RAG_PROMPT_TEMPLATE.format(
        professional_knowledge=evaluation.get("professional_knowledge", 0),
        logical_thinking=evaluation.get("logical_thinking", 0),
        # ... 其他维度
        resources=resources_text,
    )

    # 调用LLM
    messages = [{"role": "user", "content": prompt}]
    raw = await qwen_chat_json(messages)

    # 解析结果
    return {
        "weak_areas": raw.get("weak_areas", []),
        "recommendations": raw.get("recommendations", []),
        "overall_advice": raw.get("overall_advice", ""),
    }
```

---

## 三、向量化服务

### 3.1 Embedding模型

文件：`app/recommenders/embedding_service.py`

```python
class EmbeddingService:
    """文本向量化服务"""

    # 使用多语言模型，支持中文
    DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(self):
        self._model = None  # 懒加载
        self._embedding_dim = None

    @property
    def model(self) -> SentenceTransformer:
        """懒加载模型"""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
            self._embedding_dim = self._model.get_sentence_embedding_dimension()
        return self._model
```

**模型选择理由**：

| 模型 | 维度 | 特点 |
|-----|------|------|
| all-MiniLM-L6-v2 | 384 | 英文，轻量 |
| **paraphrase-multilingual-MiniLM-L12-v2** | 384 | **多语言，支持中文** |
| all-mpnet-base-v2 | 768 | 精度更高，但 heavier |

### 3.2 相似度计算

```python
def compute_similarity(self, emb1: list[float], emb2: list[float]) -> float:
    """计算余弦相似度"""
    vec1 = np.array(emb1)
    vec2 = np.array(emb2)

    # 余弦相似度 = (A·B) / (|A| * |B|)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(np.dot(vec1, vec2) / (norm1 * norm2))
```

**余弦相似度范围**：
- 1.0：完全相同方向（最相似）
- 0.0：正交（不相关）
- -1.0：相反方向（完全不相关）

### 3.3 资源文本构建

```python
def build_resource_text(self, resource: dict) -> str:
    """构建资源的文本表示，用于向量化"""
    parts = []

    # 资源名称
    if resource.get("name"):
        parts.append(resource["name"])

    # 标签
    tags = resource.get("tags", [])
    if tags:
        if isinstance(tags, str):
            parts.append(tags)
        else:
            parts.extend(tags)

    # 难度和类型
    if resource.get("difficulty"):
        parts.append(f"难度:{resource['difficulty']}")
    if resource.get("resource_type"):
        parts.append(f"类型:{resource['resource_type']}")

    return " ".join(parts)
```

---

## 四、Milvus向量数据库

### 4.1 为什么选择Milvus？

| 特性 | Milvus | Chroma | Pinecone |
|-----|--------|--------|----------|
| 开源 | ✅ | ✅ | ❌ |
| 水平扩展 | ✅ | ❌ | ✅ |
| 混合搜索 | ✅ | ❌ | ✅ |
| 自托管 | ✅ | ✅ | ❌ |

**本项目选择Milvus的原因**：
1. 开源可自托管
2. 支持大规模向量检索
3. 与Python生态集成好

### 4.2 集合设计

文件：`app/core/milvus_client.py`

```python
async def create_collection(self, dim: int = 384):
    """创建资源向量集合"""

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="resource_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
        FieldSchema(name="resource_type", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="difficulty", dtype=DataType.VARCHAR, max_length=16),
        FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="created_at", dtype=DataType.INT64),
    ]

    schema = CollectionSchema(fields, description="Learning resources vectors")
    collection = Collection(name=self.collection_name, schema=schema)

    # 创建HNSW索引
    index_params = {
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {"M": 16, "efConstruction": 64}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
```

**HNSW索引**：
- 全称：Hierarchical Navigable Small World
- 特点：近似最近邻搜索，速度快，内存占用适中
- 参数：
  - `M`：每个节点的最大连接数
  - `efConstruction`：构建时的搜索范围

### 4.3 向量搜索

```python
async def search(
    self,
    query_embedding: list[float],
    top_k: int = 100,
    filters: str = None
) -> list[dict]:
    """向量相似度搜索"""

    collection = await self.get_collection()

    search_params = {"metric_type": "COSINE", "params": {"ef": 64}}

    results = collection.search(
        data=[query_embedding],           # 查询向量
        anns_field="embedding",           # 向量字段
        param=search_params,              # 搜索参数
        limit=top_k,                      # 返回数量
        expr=filters,                     # 过滤条件
        output_fields=["resource_id", "resource_type", "difficulty", "tags"]
    )

    # 格式化结果
    hits = []
    for result in results[0]:
        hits.append({
            "resource_id": result.entity.get("resource_id"),
            "score": result.score,  # 相似度分数
            # ...
        })

    return hits
```

---

## 五、混合推荐系统

### 5.1 为什么需要混合推荐？

单一推荐策略有局限：

| 策略 | 优点 | 缺点 |
|-----|------|------|
| 规则推荐 | 可解释性强 | 不够个性化 |
| 内容推荐 | 发现相似内容 | 冷启动问题 |
| 协同过滤 | 发现新内容 | 需要大量用户数据 |
| RAG推荐 | 个性化强 | 计算成本高 |

**混合推荐**：取长补短，综合多种策略

### 5.2 混合推荐架构

```
用户请求
    │
    ├──→ 规则推荐 ──┐
    │   (50%权重)   │
    │               │
    ├──→ 内容推荐 ──┼──→ 加权融合 ──→ 多样性重排 ──→ 结果
    │   (30%权重)   │
    │               │
    └──→ 协同过滤 ──┘
        (20%权重)
```

### 5.3 代码实现

文件：`app/recommenders/hybrid.py`

```python
class HybridRecommender(BaseRecommender):
    """混合推荐器 - 融合多种推荐策略"""

    WEIGHTS = {
        "rule_based": 0.5,
        "content_based": 0.3,
        "collaborative": 0.2,
    }

    async def recommend(self, user_id: int, limit: int = 10):
        """生成混合推荐"""

        # 多路召回
        all_recommendations = []

        # 1. 规则推荐 (50%)
        rule_recs = await self.rule_based.recommend(user_id, limit)
        for rec in rule_recs:
            rec["weighted_score"] = rec["score"] * self.WEIGHTS["rule_based"]
            rec["source"] = "rule_based"
            all_recommendations.append(rec)

        # 2. 内容推荐 (30%)
        content_recs = await self.content_based.recommend(user_id, limit)
        for rec in content_recs:
            rec["weighted_score"] = rec["score"] * self.WEIGHTS["content_based"]
            rec["source"] = "content_based"
            all_recommendations.append(rec)

        # 3. 协同过滤 (20%)
        collab_recs = await self.collaborative.recommend(user_id, limit)
        for rec in collab_recs:
            rec["weighted_score"] = rec["score"] * self.WEIGHTS["collaborative"]
            rec["source"] = "collaborative"
            all_recommendations.append(rec)

        # 按资源ID聚合分数
        resource_scores = {}
        for rec in all_recommendations:
            rid = rec["resource_id"]
            if rid in resource_scores:
                resource_scores[rid]["weighted_score"] += rec["weighted_score"]
            else:
                resource_scores[rid] = rec.copy()

        # 排序并应用多样性
        sorted_resources = sorted(
            resource_scores.values(),
            key=lambda x: x["weighted_score"],
            reverse=True
        )

        return self._apply_diversity(sorted_resources[:limit])
```

### 5.4 多样性控制

```python
def _apply_diversity(
    self,
    resources: list[dict],
    max_per_type: int = 2
) -> list[dict]:
    """多样性控制 - 避免推荐结果过于单一"""

    seen_types = {}
    diverse_recommendations = []

    for rec in resources:
        resource_type = rec.get("resource_type", "unknown")
        type_count = seen_types.get(resource_type, 0)

        # 每种类型最多2个
        if type_count < max_per_type:
            diverse_recommendations.append(rec)
            seen_types[resource_type] = type_count + 1

    return diverse_recommendations
```

---

## 六、各推荐策略详解

### 6.1 规则推荐

文件：`app/recommenders/rule_based.py`

**原理**：基于用户评估分数，匹配对应标签的资源

```python
# 推荐规则配置
RECOMMENDATION_RULES = {
    "professional_knowledge": {
        "threshold": 60,
        "tags": ["Python", "Java", "Go", "Django", "Spring"],
    },
    "logical_thinking": {
        "threshold": 60,
        "tags": ["算法", "数据结构", "LeetCode", "刷题"],
    },
    # ...
}
```

**适用场景**：
- 新用户冷启动
- 需要强可解释性的场景

### 6.2 内容推荐

文件：`app/recommenders/content_based.py`

**原理**：基于用户历史行为，推荐相似内容

```python
async def _build_user_interest_embedding(self, resource_ids: list) -> list[float]:
    """构建用户兴趣向量"""

    # 获取用户浏览过的资源
    resource_texts = []
    for rid in resource_ids:
        text = self.embedding_service.build_resource_text(resource)
        resource_texts.append(text)

    # 计算Embedding并取平均
    embeddings = self.embedding_service.get_embeddings_batch(resource_texts)
    avg_embedding = np.mean(embeddings, axis=0)

    return avg_embedding.tolist()
```

**适用场景**：
- 用户有历史行为数据
- 需要发现相似内容

### 6.3 协同过滤

文件：`app/recommenders/collaborative_filtering.py`

**原理**：找到行为相似的用户，推荐他们喜欢的内容

```python
async def _build_interaction_matrix(self, db: AsyncSession):
    """构建用户-物品交互矩阵"""

    # 查询用户交互数据
    result = await db.execute(
        select(user_resource_interactions)
    )

    # 构建资源 -> 用户集合 的映射
    interaction_matrix = {}
    for row in result:
        resource_id = row.resource_id
        user_id = row.user_id

        if resource_id not in interaction_matrix:
            interaction_matrix[resource_id] = set()
        interaction_matrix[resource_id].add(user_id)

    return interaction_matrix


def _compute_jaccard_similarity(self, set1: set, set2: set) -> float:
    """计算Jaccard相似度"""
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0
```

**适用场景**：
- 用户量足够大
- 需要发现意想不到的内容

---

## 七、面试常见问题

### Q1: RAG和传统检索有什么区别？

> RAG在检索后还会使用LLM生成回答，可以整合多个检索结果，生成连贯的回复。传统检索只是返回相关文档。

### Q2: 为什么选择384维的Embedding？

> 平衡性能和精度。维度越高表达能力越强，但计算成本和存储成本也越高。384维在中文场景下已经足够表达语义，同时计算效率高。

### Q3: 混合推荐的权重是如何确定的？

> 根据业务场景和实验结果调整。规则推荐权重高(50%)是因为面试场景需要可解释性；内容推荐(30%)提供个性化；协同过滤(20%)用于发现新内容。

### Q4: 如何处理冷启动问题？

> 多策略组合解决：
> 1. 规则推荐：不依赖历史数据
> 2. 热门资源：作为兜底策略
> 3. 用户画像：注册时收集基础信息

### Q5: 向量数据库如何选型？

> 选型考虑因素：
> 1. 是否开源 - 我们选择Milvus因为开源可自托管
> 2. 性能 - HNSW索引支持快速近似搜索
> 3. 生态 - Milvus与Python/FastAPI集成好

---

*下一篇：[核心概念小白指南](04-core-concepts-for-beginners.md)*
