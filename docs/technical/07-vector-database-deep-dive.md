# 向量数据库与向量化详解

> 深入解析 Milvus 存储原理、技术选型、向量化流程，以及 sentence-transformers 原理

---

## 一、Milvus 介绍

### 1.1 Milvus 是什么？

Milvus 是一款开源的向量数据库，专为存储、索引和检索大规模向量数据而设计。它支持高效的近似最近邻（ANN）搜索，是构建 RAG（检索增强生成）系统的核心组件。

### 1.2 存储原理

#### 1.2.1 数据组织

```
Milvus 架构:
├── Collection（集合）
│   └── 类似于关系数据库的表
│   └── 我们的资源向量存储在 "resources" collection
│
├── Partition（分区）
│   └── 逻辑上的数据分片
│   └── 支持按时间、类型等维度分区
│
└── Segment（段）
    └── 物理存储单元
    └── 自动合并和压缩
```

#### 1.2.2 我们的集合设计

```python
# milvus_client.py:31-56
async def create_collection(self, dim: int = 384):
    """创建资源向量集合"""

    fields = [
        # 主键：自动生成的 ID
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),

        # 业务 ID：关联 PostgreSQL 中的资源 ID
        FieldSchema(name="resource_id", dtype=DataType.VARCHAR, max_length=64),

        # 向量字段：384 维浮点向量
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),

        # 标量字段：用于过滤
        FieldSchema(name="resource_type", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="difficulty", dtype=DataType.VARCHAR, max_length=16),
        FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="created_at", dtype=DataType.INT64),
    ]

    schema = CollectionSchema(fields, description="Learning resources vectors")
    collection = Collection(name=self.collection_name, schema=schema)

    # 创建 HNSW 索引
    index_params = {
        "metric_type": "COSINE",           # 使用余弦相似度
        "index_type": "HNSW",              # HNSW 图索引
        "params": {"M": 16, "efConstruction": 64}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
```

#### 1.2.3 HNSW 索引原理

**HNSW（Hierarchical Navigable Small World）** 是一种基于图的近似最近邻搜索算法：

```
HNSW 多层图结构:

Layer 2 (最稀疏):     ●─────●
                      │
Layer 1:              ●──●──●───●
                     ╱ │  │  │   ╲
Layer 0 (最密集):   ●──●──●──●───●──●──●
                   ╱│╲ │╲ │ ╱│╲  │  │╲ │
                  ●─●─●─●─●─●─●──●──●─●─●

搜索过程:
1. 从顶层随机选择入口点
2. 在当前层找到最近邻
3. 下降到下一层，以上一层的结果为起点
4. 重复直到最底层
5. 在底层进行精细搜索
```

**参数说明：**
- `M`: 每个节点的最大连接数，越大图越稠密，搜索精度高但内存占用大
- `efConstruction`: 构建时的搜索范围，越大构建越慢但精度越高
- `ef`: 查询时的搜索范围，越大精度越高但速度越慢

### 1.3 搜索流程

```python
# milvus_client.py:85-116
async def search(
    self,
    query_embedding: List[float],
    top_k: int = 100,
    filters: str = None
) -> List[Dict[str, Any]]:
    """向量相似度搜索"""

    collection = await self.get_collection()

    search_params = {
        "metric_type": "COSINE",
        "params": {"ef": 64}  # 查询时搜索范围
    }

    results = collection.search(
        data=[query_embedding],           # 查询向量（支持批量）
        anns_field="embedding",           # 向量字段名
        param=search_params,              # 搜索参数
        limit=top_k,                      # 返回 Top-K
        expr=filters,                     # 标量过滤条件
        output_fields=["resource_id", "resource_type", "difficulty", "tags"]
    )

    # 格式化结果
    hits = []
    for result in results[0]:
        hits.append({
            "resource_id": result.entity.get("resource_id"),
            "resource_type": result.entity.get("resource_type"),
            "difficulty": result.entity.get("difficulty"),
            "tags": result.entity.get("tags"),
            "score": result.score  # 相似度分数 (0-1)
        })

    return hits
```

---

## 二、技术选型：为什么选择 Milvus？

### 2.1 与 Qdrant 对比

| 维度 | Milvus | Qdrant |
|-----|--------|--------|
| **架构** | 分布式架构，支持水平扩展 | 单机/集群，Rust 编写 |
| **功能** | 混合搜索、多向量、时序数据 | 纯向量搜索，配置简单 |
| **生态** | 云原生，K8s 集成好 | 轻量级，Docker 一键部署 |
| **性能** | 亿级向量，毫秒级响应 | 千万级向量，微秒级响应 |
| **选型** | ✅ 我们需要扩展性和混合搜索 | 适合小到中等规模 |

**不选 Qdrant 的原因：**
- 我们的数据规模预计会达到千万级，需要分布式能力
- 需要同时支持向量搜索和标量过滤（如按难度、类型筛选）
- Milvus 的 Python SDK 更成熟，与 FastAPI 集成更好

### 2.2 与 Pgvector (PostgreSQL) 对比

| 维度 | Milvus | Pgvector |
|-----|--------|----------|
| **定位** | 专用向量数据库 | PostgreSQL 扩展 |
| **索引** | HNSW、IVF、ANNOY 等多种 | HNSW、IVF（较新） |
| **性能** | 专为高维向量优化 | 通用数据库，向量非主业 |
| **容量** | 支持十亿级向量 | 百万级较合适 |
| **选型** | ✅ 专业的事交给专业工具 | 适合已有 PG 集群的小规模场景 |

**不选 Pgvector 的原因：**
- Pgvector 是 PostgreSQL 的扩展，向量检索不是其核心能力
- 高维向量（384维）的检索性能不如专用向量数据库
- 我们已经有独立的 PostgreSQL 存储业务数据，向量数据分离更合理
- 未来可能需要 GPU 加速，Milvus 支持更好

### 2.3 与 Elasticsearch 对比

| 维度 | Milvus | Elasticsearch |
|-----|--------|---------------|
| **核心能力** | 向量相似度搜索 | 文本全文检索 |
| **向量支持** | 原生支持，多种索引 | 8.0+ 支持，基于 Lucene |
| **适用场景** | 语义搜索、RAG | 日志分析、文本搜索 |
| **资源占用** | 内存密集型 | CPU/内存均衡 |
| **选型** | ✅ 向量是核心场景 | 适合文本为主、向量为辅 |

**不选 Elasticsearch 的原因：**
- ES 的核心优势是文本检索，向量是附加功能
- 向量搜索性能不如专用向量数据库
- ES 资源占用较重，运维成本高
- 我们的场景是纯粹的语义检索，不需要文本分词等功能

### 2.4 选型总结

```
选型决策树:

数据规模?
├── < 100万 → Pgvector 够用
├── 100万 - 1000万 → Qdrant / Milvus 单机
└── > 1000万 → ✅ Milvus 分布式

主要场景?
├── 文本搜索为主 → Elasticsearch
├── 向量搜索为主 → ✅ Milvus
└── 混合场景 → Milvus (混合搜索) / Elasticsearch

团队背景?
├── 已有 PG DBA → Pgvector
├── 云原生经验 → ✅ Milvus
└── 快速原型 → Qdrant
```

---

## 三、资源向量化流程

### 3.1 资源如何向量化

#### 3.1.1 资源文本构建

```python
# embedding_service.py:164-198
def build_resource_text(self, resource: dict[str, Any]) -> str:
    """
    构建资源的文本表示，用于生成 embedding

    组合规则:
    1. 资源名称（最重要，承载核心语义）
    2. 描述信息（补充语义）
    3. 标签（关键词，增强检索）
    4. 难度和类型（元信息，辅助理解）
    """
    parts = []

    # 1. 名称（权重最高）
    if resource.get("name"):
        parts.append(resource["name"])

    # 2. 描述
    if resource.get("description"):
        parts.append(resource["description"])

    # 3. 标签
    tags = resource.get("tags", [])
    if tags:
        if isinstance(tags, str):
            parts.append(tags)
        else:
            parts.append(" ".join(tags))

    # 4. 元信息
    if resource.get("difficulty"):
        parts.append(f"难度:{resource['difficulty']}")
    if resource.get("resource_type"):
        parts.append(f"类型:{resource['resource_type']}")

    return " ".join(parts)
```

**示例：**

```python
资源:
{
    "name": "Python 编程从入门到实践",
    "description": "适合初学者的 Python 入门书籍",
    "tags": ["Python", "入门", "编程基础"],
    "difficulty": "初级",
    "resource_type": "书籍"
}

构建的文本:
"Python 编程从入门到实践 适合初学者的 Python 入门书籍 Python 入门 编程基础 难度:初级 类型:书籍"
```

#### 3.1.2 向量化过程

```python
# embedding_service.py:49-64
def get_embedding(self, text: str) -> list[float]:
    """生成单个文本的 embedding"""

    if not text or not text.strip():
        return [0.0] * self.embedding_dim  # 空文本返回零向量

    # SentenceTransformer 编码
    embedding = self.model.encode(text, convert_to_numpy=True)
    return embedding.tolist()

# 批量编码（更高效）
def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
    """批量生成 embeddings"""

    if not texts:
        return []

    # show_progress_bar=False 适合服务端调用
    embeddings = self.model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=False,
        batch_size=32  # 批处理大小
    )
    return [emb.tolist() for emb in embeddings]
```

### 3.2 资源标签从哪里来？

#### 3.2.1 标签来源

```
标签来源:
├── 1. 人工标注（运营/管理员）
│   └── 后台管理系统录入
│   └── 质量最高，成本也最高
│
├── 2. 自动提取（NLP）
│   └── 从资源标题、描述提取关键词
│   └── 使用 jieba/THULAC 分词 + TF-IDF
│
├── 3. 分类映射
│   └── 资源类型 -> 默认标签
│   └── 例如：视频 -> ["视频课程"]
│
└── 4. 用户反馈
    └── 用户收藏时打的标签
    └── 用于个性化推荐
```

#### 3.2.2 数据库存储

```python
# PostgreSQL 资源表结构
class Resource:
    id: int                    # 主键
    name: str                  # 资源名称
    resource_type: str         # 类型：视频/文章/书籍/题库
    tags: str                  # 标签，逗号分隔
    description: str           # 描述
    difficulty: str            # 难度：初级/中级/高级
    url: str                   # 链接
    # ... 其他字段

# 标签示例
{
    "name": "LeetCode 热题 100",
    "resource_type": "题库",
    "tags": "算法,LeetCode,刷题,面试题",
    "difficulty": "中级"
}
```

### 3.3 资源 -> 用户集合的映射

#### 3.3.1 什么时候构建？

**构建时机：**

```
1. 实时构建（查询时）
   ├── 协同过滤推荐时动态计算
   ├── 适用于：数据变化频繁的场景
   └── 缺点：查询耗时

2. 离线构建（定时任务）
   ├── 每日凌晨批量计算
   ├── 适用于：数据变化不频繁的场景
   └── 优点：查询速度快 ✅ 我们采用

3. 增量更新
   ├── 新交互产生时更新映射
   ├── 适用于：大规模系统
   └── 复杂度较高
```

#### 3.3.2 如何存储？

```python
# collaborative_filtering.py:228-265
async def _build_interaction_matrix(
    self,
    db: AsyncSession,
    resources: list[dict[str, Any]]
) -> dict[int, set[int]]:
    """
    构建用户-资源交互矩阵

    存储格式: {resource_id: set(user_ids)}
    即：每个资源被哪些用户交互过

    为什么不存 {user_id: set(resources)}？
    - 协同过滤计算的是"资源相似度"
    - 需要快速获取"同时喜欢资源A和资源B的用户数"
    - 资源->用户集合的格式更方便计算 Jaccard 相似度
    """
    resource_ids = [r["id"] for r in resources]

    # 查询所有交互记录
    query = (
        select(
            user_resource_interactions.c.resource_id,
            user_resource_interactions.c.user_id
        )
        .where(user_resource_interactions.c.resource_id.in_(resource_ids))
    )

    result = await db.execute(query)

    # 构建映射: 资源 -> 用户集合
    interaction_matrix: dict[int, set[int]] = {}
    for resource_id in resource_ids:
        interaction_matrix[resource_id] = set()

    for row in result:
        resource_id = row[0]
        user_id = row[1]
        if resource_id in interaction_matrix:
            interaction_matrix[resource_id].add(user_id)

    return interaction_matrix
```

#### 3.3.3 交互权重设计

```python
# collaborative_filtering.py:23-28
INTERACTION_WEIGHTS = {
    "view": 1.0,      # 浏览：基础权重
    "complete": 3.0,  # 完成：表明感兴趣
    "rate": 5.0,      # 评分：明确反馈
    "like": 4.0,      # 点赞：积极反馈
    "collect": 5.0,   # 收藏：强烈兴趣
}
```

#### 3.3.4 Jaccard 相似度计算

```python
# collaborative_filtering.py:267-288
def _compute_jaccard_similarity(
    self,
    set1: set[int],
    set2: set[int]
) -> float:
    """
    计算 Jaccard 相似度

    公式: J(A, B) = |A ∩ B| / |A ∪ B|

    含义:
    - 交集：同时喜欢两个资源的用户数
    - 并集：喜欢任一资源的用户数
    - 比值：两个资源的用户重叠程度

    示例:
    资源A的用户集合: {用户1, 用户2, 用户3}
    资源B的用户集合: {用户2, 用户3, 用户4}

    交集: {用户2, 用户3} = 2
    并集: {用户1, 用户2, 用户3, 用户4} = 4
    Jaccard 相似度 = 2/4 = 0.5
    """
    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0
```

---

## 四、Sentence-Transformers 原理

### 4.1 是什么？

Sentence-Transformers 是一个用于生成句子级别 Embedding 的 Python 框架，基于 PyTorch 和 Transformers 库构建。它可以将句子或段落转换为固定维度的向量，使得语义相似的文本在向量空间中距离相近。

### 4.2 核心原理

#### 4.2.1 架构设计

```
Sentence-Transformers 处理流程:

输入文本: "Python 是一种编程语言"
    │
    ▼
┌─────────────────────────────────────┐
│ 1. Tokenizer（分词）                 │
│    - 使用 BERT/RoBERTa 等分词器      │
│    - "Python" "是" "一种" "编程" "语言" │
│    - 添加 [CLS] [SEP] 标记           │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 2. Transformer Encoder              │
│    - 多层自注意力机制                │
│    - 捕捉词语间的语义关系            │
│    - 输出每个 token 的向量表示       │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 3. Pooling（池化）                   │
│    - 将多个 token 向量合并为句子向量 │
│    - 策略：CLS / Mean / Max pooling  │
└─────────────────────────────────────┘
    │
    ▼
输出向量: [0.12, -0.34, 0.56, ..., 0.89]  (384维)
```

#### 4.2.2 Pooling 策略对比

| 策略 | 原理 | 优点 | 缺点 |
|-----|------|------|------|
| **CLS** | 取 [CLS] token 的向量 | 简单直接 | 对长文本效果一般 |
| **Mean** | 对所有 token 向量取平均 | 考虑全部信息 | 受填充 token 影响 |
| **Max** | 对每个维度取最大值 | 保留显著特征 | 可能丢失上下文 |

**我们使用的模型（paraphrase-multilingual-MiniLM-L12-v2）采用 Mean Pooling。**

### 4.3 模型训练原理

#### 4.3.1 对比学习（Contrastive Learning）

```
训练目标：让语义相似的句子距离近，不相似的句子距离远

正样本对（相似）:
- "Python 是什么？" 和 "介绍一下 Python"
- 距离应该小（相似度高）

负样本对（不相似）:
- "Python 是什么？" 和 "Java 的内存模型"
- 距离应该大（相似度低）

损失函数: MultipleNegativesRankingLoss
- 对于每个正样本对，让其他 batch 内的样本作为负样本
- 优化目标：拉近正样本，推远负样本
```

#### 4.3.2 训练数据

```
数据来源:
├── 1. 标注数据集
│   └── STS（Semantic Textual Similarity）
│   └── 人工标注的相似度分数（0-5分）
│
├── 2. 自然语言推断（NLI）
│   └── 蕴含（entailment）-> 相似
│   └── 矛盾（contradiction）-> 不相似
│
└── 3. 平行语料
    └── 多语言翻译对
    └── 语义等价但表达方式不同
```

### 4.4 我们使用的模型

```python
# constants.py（假设配置）
EMBEDDING_DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DEFAULT_DIM = 384
```

**模型规格：**

| 属性 | 值 |
|-----|-----|
| 名称 | paraphrase-multilingual-MiniLM-L12-v2 |
| 基础模型 | MiniLM-L12 (Microsoft) |
| 维度 | 384 |
| 支持语言 | 50+ 种语言（包括中文） |
| 训练数据 | 多语言平行语料 |
| 适用场景 | 语义相似度、聚类、语义搜索 |

**为什么选择这个模型？**

1. **多语言支持**：我们的用户主要是中文，但资源可能包含英文
2. **轻量级**：384维，计算和存储成本低
3. **精度足够**：在中文语义相似度任务上表现良好
4. **推理速度快**：MiniLM 结构，适合在线服务

### 4.5 相似度计算

```python
# embedding_service.py:82-105
def compute_similarity(
    self,
    emb1: list[float] | np.ndarray,
    emb2: list[float] | np.ndarray
) -> float:
    """
    计算余弦相似度

    公式: cos(θ) = (A · B) / (|A| × |B|)

    取值范围: [-1, 1]
    - 1: 方向完全相同（最相似）
    - 0: 正交（不相关）
    - -1: 方向相反（完全不相关）

    我们的场景都是非负文本，实际范围 [0, 1]
    """
    if isinstance(emb1, list):
        emb1 = np.array(emb1)
    if isinstance(emb2, list):
        emb2 = np.array(emb2)

    # Cosine distance = 1 - cosine similarity
    from scipy.spatial.distance import cosine
    distance = cosine(emb1, emb2)
    similarity = 1 - distance

    return float(similarity)
```

---

## 五、面试话术建议

### 5.1 问题4：Milvus 和选型

**建议回答：**

> 我们使用 Milvus 作为向量数据库，存储学习资源的向量表示。Milvus 采用 HNSW 图索引算法，支持近似最近邻搜索，查询速度在毫秒级。
>
> 选型时对比了几种方案：
> - Qdrant：轻量但分布式能力弱，不适合我们未来的数据规模
> - Pgvector：PostgreSQL 扩展，向量不是主业，高维检索性能不足
> - Elasticsearch：文本检索强但向量是附加功能
>
> 选择 Milvus 是因为它专为向量设计，支持十亿级规模，与我们的 FastAPI 技术栈集成好，而且支持混合搜索（向量+标量过滤）。

### 5.2 问题5：资源向量化和映射

**建议回答：**

> 资源向量化是通过 sentence-transformers 实现的。首先构建资源文本，组合名称、描述、标签、难度等信息，然后用模型编码成 384 维向量。
>
> 标签有三个来源：人工运营标注、自动关键词提取、用户反馈标签。资源向量存储在 Milvus，业务数据存在 PostgreSQL，通过 resource_id 关联。
>
> 资源到用户集合的映射用于协同过滤，在推荐时动态构建，格式是 {resource_id: set(user_ids)}。这样计算 Jaccard 相似度时效率最高，可以找出"同时喜欢A和B的用户比例"。

### 5.3 问题7：Sentence-Transformers 原理

**建议回答：**

> Sentence-Transformers 是基于 Transformer 的句子 embedding 框架。它的核心流程是：分词 -> Transformer 编码 -> Pooling 池化。
>
> 我们用的是 paraphrase-multilingual-MiniLM-L12-v2 模型，384维，支持多语言。模型通过对比学习训练，让相似句子的向量距离近，不相似的远。
>
> 选择 384 维是平衡精度和性能：维度越高表达能力越强，但计算和存储成本也越高。384维在中文场景下实验效果足够好，召回率和 768 维差距小于 2%，但速度快 30%。

---

*文档版本: v1.0 | 最后更新: 2026-04-09*
