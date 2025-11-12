# 向量搜索降级机制详解

## 📋 目录

1. [降级触发条件](#降级触发条件)
2. [代码流程分析](#代码流程分析)
3. [实际触发场景](#实际触发场景)
4. [日志追踪示例](#日志追踪示例)
5. [threshold 调整机制](#threshold-调整机制)
6. [常见问题排查](#常见问题排查)

---

## 降级触发条件

### 🎯 核心问题：什么时候会降级到"整篇文档向量搜索"？

**简单答案**：当段落向量搜索失败时，会自动降级到整篇文档向量搜索。

### 📊 降级触发的两种情况

```python
# 代码位置：library/common/knowledge_base/base_search_service.py
# 方法：search_with_vectors() (line 99-157)

def search_with_vectors(self, query, limit=5, threshold=0.7):
    try:
        # ========================================
        # 步骤 1：优先尝试段落向量搜索
        # ========================================
        try:
            section_service = SectionSearchService()
            section_results = section_service.search_sections(...)
            
            # ✅ 条件 1：段落搜索成功（有结果）
            if section_results:
                return section_results  # ← 成功返回，不会降级
        
        except Exception as section_error:
            # ❌ 条件 2：段落搜索抛出异常
            self.logger.warning("⚠️ 段落向量搜尋失敗，使用整篇文檔搜尋")
            # → 继续执行步骤 2，触发降级
        
        # ========================================
        # 步骤 2：降级到整篇文档向量搜索
        # ========================================
        # 🔄 只有在以下情况才会执行到这里：
        #   1. 段落搜索抛出异常（Exception）
        #   2. 段落搜索返回空结果（section_results 为 None 或空列表）
        
        doc_threshold = max(threshold * 0.85, 0.5)
        results = search_with_vectors_generic(...)
        return results
        
    except Exception as e:
        return []
```

### 🔍 详细触发条件表

| # | 段落搜索状态 | section_results 值 | 是否降级？ | 说明 |
|---|------------|-------------------|----------|------|
| 1 | ✅ 成功找到结果 | `[{...}, {...}]` (非空列表) | ❌ 不降级 | 直接返回段落结果 |
| 2 | ⚠️ 未找到结果 | `[]` (空列表) | ✅ **降级** | 继续执行文档搜索 |
| 3 | ⚠️ 返回 None | `None` | ✅ **降级** | 继续执行文档搜索 |
| 4 | ❌ 抛出异常 | 异常被捕获 | ✅ **降级** | 记录警告并降级 |

---

## 代码流程分析

### 📝 完整的执行流程图

```
用户查询: "Cup 如何测试?"
threshold: 0.75
limit: 3
    ↓
┌═════════════════════════════════════════════════════════┐
║ search_with_vectors() 开始执行                          ║
╚═════════════════════════════════════════════════════════╝
    ↓
┌─────────────────────────────────────────────────────────┐
│ 🎯 步骤 1：尝试段落向量搜索                              │
├─────────────────────────────────────────────────────────┤
│ try:                                                    │
│     section_service = SectionSearchService()            │
│     section_results = section_service.search_sections(  │
│         query="Cup 如何测试?",                          │
│         source_table='protocol_guide',                  │
│         limit=3,                                        │
│         threshold=0.75                                  │
│     )                                                   │
│                                                         │
│     # 🔍 检查点 1：是否有结果？                          │
│     if section_results:  # ← 关键判断                  │
│         # ✅ 有结果 → 返回，不降级                      │
│         logger.info("✅ 段落向量搜尋成功")               │
│         return section_results                          │
│     else:                                               │
│         # ⚠️ 空结果 → 继续执行，触发降级                │
│         # (不抛出异常，直接跳过 return)                 │
│         pass                                            │
│                                                         │
│ except Exception as section_error:                      │
│     # ❌ 异常 → 记录并继续，触发降级                    │
│     logger.warning(                                     │
│         f"⚠️ 段落向量搜尋失敗: {str(section_error)}"    │
│     )                                                   │
└─────────────────────────────────────────────────────────┘
    ↓ (未 return，继续执行)
┌═════════════════════════════════════════════════════════┐
║ 🔄 步骤 2：降级到整篇文档向量搜索                        ║
╠═════════════════════════════════════════════════════════╣
║ # 📉 降低 threshold（更宽松）                           ║
║ doc_threshold = max(threshold * 0.85, 0.5)              ║
║ # 0.75 * 0.85 = 0.6375                                 ║
║                                                         ║
║ from .vector_search_helper import \                     ║
║     search_with_vectors_generic                         ║
║                                                         ║
║ results = search_with_vectors_generic(                  ║
║     query="Cup 如何测试?",                              ║
║     model_class=ProtocolGuide,                          ║
║     source_table='protocol_guide',                      ║
║     limit=3,                                            │
║     threshold=0.6375,  # ← 降低的阈值                   ║
║     use_1024=True      # 使用 document_embeddings 表   ║
║ )                                                       ║
║                                                         ║
║ logger.info(                                            ║
║     f"📄 整篇文檔向量搜尋返回 {len(results)} 個結果"     ║
║     f"(threshold={doc_threshold:.2f})"                  ║
║ )                                                       ║
║                                                         ║
║ return results  # ← 返回文档级结果                     ║
╚═════════════════════════════════════════════════════════╝
```

### 🔑 关键代码解析

#### 判断点 1：`if section_results:`

```python
if section_results:
    # ✅ 条件为 True 的情况：
    #   - section_results = [{...}, {...}]  (非空列表)
    #   - section_results = [{}]             (单个结果)
    #   - 任何 truthy 的值
    
    return section_results  # ← 成功返回，不会降级
```

```python
# ⚠️ 条件为 False 的情况（会触发降级）：
#   - section_results = []      (空列表)
#   - section_results = None
#   - section_results = 0
#   - section_results = False
#   - section_results = ""

# 这些情况下，不会执行 return
# 继续执行后面的代码 → 触发降级
```

#### 判断点 2：`except Exception as section_error:`

```python
try:
    section_results = section_service.search_sections(...)
    
except Exception as section_error:
    # ❌ 捕获所有异常（会触发降级）
    
    # 常见异常类型：
    # 1. DatabaseError: 数据库连接失败
    # 2. ProgrammingError: SQL 语法错误
    # 3. OperationalError: 表不存在
    # 4. ImportError: 模块导入失败
    # 5. AttributeError: 对象属性错误
    # ... 等等
    
    logger.warning(f"⚠️ 段落搜索失败: {str(section_error)}")
    
    # 不 return，继续执行 → 触发降级
```

---

## 实际触发场景

### 场景 1：数据库表不存在 ⭐ 最常见

**触发条件**：`document_section_embeddings` 表不存在

**执行流程**：
```
1. 尝试段落搜索
2. 执行 SQL: SELECT ... FROM document_section_embeddings
3. ❌ 抛出异常: relation "document_section_embeddings" does not exist
4. 捕获异常，记录警告
5. 🔄 降级到整篇文档搜索
6. 执行 SQL: SELECT ... FROM document_embeddings
7. ✅ 返回文档结果
```

**日志输出**：
```log
[WARNING] library.common.knowledge_base.base_search_service:
  ⚠️ 段落向量搜尋失敗，使用整篇文檔搜尋: 
  relation "document_section_embeddings" does not exist

[INFO] library.common.knowledge_base.base_search_service:
  📄 整篇文檔向量搜尋返回 1 個結果 (threshold=0.64)
```

**实际命令测试**：
```bash
# 检查段落表是否存在
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'document_section_embeddings'
);
"
```

**预期结果**：
- 如果返回 `f`（false）→ 会触发降级
- 如果返回 `t`（true）→ 不会因为表不存在而降级

---

### 场景 2：段落表为空（无数据）

**触发条件**：表存在，但没有对应的段落向量数据

**执行流程**：
```
1. 尝试段落搜索
2. 执行 SQL: SELECT ... FROM document_section_embeddings
3. ✅ SQL 执行成功（无异常）
4. ⚠️ 返回空列表: section_results = []
5. 检查 if section_results: → False
6. 🔄 不执行 return，继续执行
7. 降级到整篇文档搜索
8. ✅ 返回文档结果
```

**日志输出**：
```log
[INFO] library.common.knowledge_base.section_search_service:
  📊 段落搜索: source=protocol_guide, 查詢='Cup 如何测试', threshold=0.75

[INFO] library.common.knowledge_base.section_search_service:
  ⚠️ 未找到匹配的段落

[INFO] library.common.knowledge_base.base_search_service:
  📄 整篇文檔向量搜尋返回 1 個結果 (threshold=0.64)
```

**验证方法**：
```bash
# 检查段落表的数据量
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    source_table,
    COUNT(*) as section_count
FROM document_section_embeddings
WHERE source_table = 'protocol_guide'
GROUP BY source_table;
"
```

**结果判断**：
- `section_count = 0` → 会触发降级（空结果）
- `section_count > 0` → 可能不降级（取决于查询是否匹配）

---

### 场景 3：threshold 过高（无匹配结果）

**触发条件**：段落向量相似度都低于 threshold

**执行流程**：
```
1. 尝试段落搜索 (threshold=0.95)
2. 执行 SQL: ... WHERE similarity >= 0.95
3. ✅ SQL 执行成功（无异常）
4. ⚠️ 所有段落相似度 < 0.95
5. 返回空列表: section_results = []
6. 检查 if section_results: → False
7. 🔄 降级到整篇文档搜索 (threshold=0.8075)
8. 可能找到文档结果（因为 threshold 更低）
```

**示例数据**：
```
查询: "Cup 如何测试?"
threshold: 0.95

段落搜索结果：
- 段落 1: similarity = 0.86 ❌ (< 0.95)
- 段落 2: similarity = 0.82 ❌ (< 0.95)
→ 返回空列表 → 触发降级

文档搜索结果 (threshold=0.8075):
- 文档 1: similarity = 0.88 ✅ (>= 0.8075)
→ 返回文档结果
```

**日志输出**：
```log
[INFO] library.common.knowledge_base.section_search_service:
  📊 段落搜索: 找到 2 個候選段落，但相似度都低於 threshold=0.95

[INFO] library.common.knowledge_base.base_search_service:
  📄 整篇文檔向量搜尋返回 1 個結果 (threshold=0.81)
```

---

### 场景 4：数据库连接失败

**触发条件**：无法连接到 PostgreSQL 数据库

**执行流程**：
```
1. 尝试段落搜索
2. 尝试连接数据库
3. ❌ 抛出异常: could not connect to server
4. 捕获异常，记录警告
5. 🔄 降级到整篇文档搜索
6. ❌ 同样无法连接
7. 返回空列表
```

**日志输出**：
```log
[WARNING] library.common.knowledge_base.base_search_service:
  ⚠️ 段落向量搜尋失敗，使用整篇文檔搜尋: 
  could not connect to server: Connection refused

[ERROR] library.common.knowledge_base.base_search_service:
  向量搜索錯誤: could not connect to server: Connection refused
```

---

### 场景 5：向量维度不匹配

**触发条件**：查询向量维度与表中向量维度不一致

**执行流程**：
```
1. 尝试段落搜索
2. 生成查询向量 (1024 维)
3. 执行 SQL: ... WHERE embedding <=> query_vector
4. ❌ 抛出异常: expected 384 dimensions, not 1024
5. 捕获异常，记录警告
6. 🔄 降级到整篇文档搜索
7. ✅ 文档表使用正确的维度
8. 返回文档结果
```

**日志输出**：
```log
[WARNING] library.common.knowledge_base.base_search_service:
  ⚠️ 段落向量搜尋失敗，使用整篇文檔搜尋: 
  expected 384 dimensions, not 1024

[INFO] library.common.knowledge_base.base_search_service:
  📄 整篇文檔向量搜尋返回 1 個結果 (threshold=0.64)
```

**诊断方法**：
```bash
# 检查段落表的向量维度
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    column_name,
    format_type(a.atttypid, a.atttypmod) as data_type
FROM pg_catalog.pg_attribute a
WHERE a.attrelid = 'document_section_embeddings'::regclass
  AND a.attname = 'embedding'
  AND NOT a.attisdropped;
"
```

---

## 日志追踪示例

### 示例 1：正常情况（不降级）

```log
2025-11-12 14:30:15,123 [INFO] library.common.knowledge_base.section_search_service:
  📊 段落搜索: source=protocol_guide, 查詢='Cup 如何测试', threshold=0.75

2025-11-12 14:30:15,145 [INFO] library.common.knowledge_base.section_search_service:
  ✅ 找到 2 個段落，相似度範圍: 0.86 ~ 0.82

2025-11-12 14:30:15,156 [INFO] library.common.knowledge_base.base_search_service:
  ✅ 段落向量搜尋成功: 2 個結果 (threshold=0.75)

2025-11-12 14:30:15,167 [INFO] library.common.knowledge_base.base_search_service:
  向量搜索返回 2 條結果 (threshold=0.75)

# 🎯 分析：
# - 段落搜索成功找到 2 个结果
# - 没有 "⚠️ 段落向量搜尋失敗" 警告
# - 没有 "📄 整篇文檔向量搜尋" 日志
# → 结论：未触发降级
```

---

### 示例 2：降级情况（表不存在）

```log
2025-11-12 14:35:20,234 [INFO] library.common.knowledge_base.section_search_service:
  📊 段落搜索: source=protocol_guide, 查詢='Cup 如何测试', threshold=0.75

2025-11-12 14:35:20,245 [WARNING] library.common.knowledge_base.base_search_service:
  ⚠️ 段落向量搜尋失敗，使用整篇文檔搜尋: 
  relation "document_section_embeddings" does not exist

2025-11-12 14:35:20,312 [INFO] library.common.knowledge_base.base_search_service:
  📄 整篇文檔向量搜尋返回 1 個結果 (threshold=0.64)

2025-11-12 14:35:20,323 [INFO] library.common.knowledge_base.base_search_service:
  向量搜索返回 1 條結果 (threshold=0.75)

# 🎯 分析：
# - 出现 "⚠️ 段落向量搜尋失敗" 警告
# - 异常原因：表不存在
# - 出现 "📄 整篇文檔向量搜尋" 日志
# - threshold 从 0.75 降低到 0.64
# → 结论：触发降级（原因：表不存在）
```

---

### 示例 3：降级情况（无匹配结果）

```log
2025-11-12 14:40:30,456 [INFO] library.common.knowledge_base.section_search_service:
  📊 段落搜索: source=protocol_guide, 查詢='非常罕见的查询', threshold=0.75

2025-11-12 14:40:30,478 [INFO] library.common.knowledge_base.section_search_service:
  ⚠️ 未找到匹配的段落

2025-11-12 14:40:30,512 [INFO] library.common.knowledge_base.base_search_service:
  📄 整篇文檔向量搜尋返回 0 個結果 (threshold=0.64)

2025-11-12 14:40:30,523 [INFO] library.common.knowledge_base.base_search_service:
  向量搜索返回 0 條結果 (threshold=0.75)

# 🎯 分析：
# - 段落搜索未找到匹配结果
# - 没有异常，但返回空列表
# - 自动降级到整篇文档搜索
# - 文档搜索也没找到结果
# → 结论：触发降级（原因：无匹配结果）
```

---

## threshold 调整机制

### 📉 降级时的 threshold 计算

```python
# 原始 threshold（段落搜索）
threshold = 0.75

# 降级后的 threshold（文档搜索）
doc_threshold = max(threshold * 0.85, 0.5)
# doc_threshold = max(0.75 * 0.85, 0.5)
# doc_threshold = max(0.6375, 0.5)
# doc_threshold = 0.6375
```

### 🎯 为什么要降低 threshold？

1. **补偿机制**：段落搜索失败，需要更宽松的条件
2. **匹配率提升**：降低阈值增加找到结果的可能性
3. **避免无结果**：至少保证 threshold ≥ 0.5

### 📊 threshold 对比表

| 原始 threshold | 段落搜索 threshold | 文档搜索 threshold | 降低幅度 |
|---------------|-------------------|-------------------|----------|
| 0.90 | 0.90 | max(0.765, 0.5) = **0.765** | -15% |
| 0.80 | 0.80 | max(0.680, 0.5) = **0.680** | -15% |
| 0.75 | 0.75 | max(0.6375, 0.5) = **0.6375** | -15% |
| 0.70 | 0.70 | max(0.595, 0.5) = **0.595** | -15% |
| 0.60 | 0.60 | max(0.510, 0.5) = **0.510** | -15% |
| 0.55 | 0.55 | max(0.4675, 0.5) = **0.5** | 兜底 |
| 0.50 | 0.50 | max(0.425, 0.5) = **0.5** | 兜底 |

**关键点**：
- ✅ 文档搜索 threshold 永远不会低于 0.5
- ✅ 降低幅度固定为 15%（乘以 0.85）
- ✅ 兜底机制：`max(threshold * 0.85, 0.5)`

---

## 常见问题排查

### Q1: 如何判断系统是否触发了降级？

**方法 1：查看日志**
```bash
# 查看最近的搜索日志
docker logs ai-django --tail 100 | grep -A 5 "段落向量搜尋"

# 关键标志：
# ✅ 未降级：只看到 "✅ 段落向量搜尋成功"
# ⚠️ 降级：看到 "⚠️ 段落向量搜尋失敗，使用整篇文檔搜尋"
```

**方法 2：检查日志文件**
```bash
# 在日志文件中搜索降级警告
grep "段落向量搜尋失敗" logs/django.log

# 统计降级次数
grep -c "整篇文檔向量搜尋" logs/django.log
```

---

### Q2: 如何避免触发降级？

**解决方案 1：确保段落表存在并有数据**
```bash
# 1. 检查表是否存在
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT tablename 
FROM pg_tables 
WHERE tablename = 'document_section_embeddings';
"

# 2. 检查数据量
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT source_table, COUNT(*) 
FROM document_section_embeddings 
GROUP BY source_table;
"

# 3. 如果没有数据，生成段落向量
docker exec ai-django python manage.py shell
>>> from api.services.section_generation_service import generate_all_sections
>>> generate_all_sections('protocol_guide')
```

**解决方案 2：调整 threshold**
```bash
# 在 Dify Studio 中降低 score_threshold
# 从 0.75 → 0.65
# 增加匹配成功率
```

**解决方案 3：优化查询文本**
```python
# 使用更具体的查询
# ❌ 差的查询："测试"
# ✅ 好的查询："Cup 测试步骤"
```

---

### Q3: 降级会影响结果质量吗？

**答案：会，但有利有弊**

| 方面 | 段落搜索 | 文档搜索（降级） | 影响 |
|------|---------|----------------|------|
| **精准度** | 高（只返回相关段落） | 低（返回整篇文档） | ⚠️ 可能包含无关内容 |
| **上下文** | 少（只有段落） | 多（完整文档） | ✅ 更完整的信息 |
| **相似度** | threshold 0.75 | threshold 0.6375 | ⚠️ 匹配标准降低 |
| **匹配率** | 中（可能无结果） | 高（更容易匹配） | ✅ 减少无结果情况 |
| **响应大小** | 小（段落） | 大（完整文档） | ⚠️ 增加 token 消耗 |

**建议**：
- 优先解决段落搜索失败的根本原因
- 降级是保底机制，不是最优方案
- 监控降级频率，频繁降级说明有问题

---

### Q4: 如何测试降级机制？

**测试方法 1：临时删除段落表**
```bash
# ⚠️ 危险操作，仅限测试环境！
docker exec postgres_db psql -U postgres -d ai_platform -c "
DROP TABLE IF EXISTS document_section_embeddings;
"

# 发送测试查询
curl -X POST "http://localhost/api/dify/knowledge/retrieval" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_database",
    "query": "Cup 如何测试?",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.75}
  }'

# 预期：触发降级，使用文档搜索
```

**测试方法 2：使用高 threshold**
```bash
# 使用非常高的 threshold，确保段落搜索无结果
curl -X POST "http://localhost/api/dify/knowledge/retrieval" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_database",
    "query": "Cup",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.99}
  }'

# 预期：段落搜索无结果，触发降级
```

**测试方法 3：查询不存在的内容**
```bash
curl -X POST "http://localhost/api/dify/knowledge/retrieval" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_database",
    "query": "这是一个完全不存在的查询内容 zzzzzz",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.75}
  }'

# 预期：段落搜索无结果，降级到文档搜索
```

---

## 总结

### 🎯 核心要点

1. **降级触发条件**（2 种）：
   - ❌ 段落搜索抛出异常
   - ⚠️ 段落搜索返回空结果

2. **降级机制**：
   - 自动执行（无需人工干预）
   - 降低 threshold（0.85 倍率）
   - 切换到 document_embeddings 表

3. **常见触发原因**（按频率排序）：
   1. 段落表不存在（最常见）
   2. 段落表为空（无数据）
   3. threshold 过高（无匹配）
   4. 查询内容不存在
   5. 数据库连接失败
   6. 向量维度不匹配

4. **如何判断降级**：
   - 查看日志关键词：`"⚠️ 段落向量搜尋失敗"`
   - 查看日志关键词：`"📄 整篇文檔向量搜尋"`
   - threshold 值降低：0.75 → 0.6375

5. **优化建议**：
   - 确保段落表存在并有数据
   - 监控降级频率
   - 调整合理的 threshold
   - 优化查询文本

---

**文档版本**：v1.0  
**创建日期**：2025-11-12  
**作者**：AI Platform Team  
**相关文档**：
- `docs/architecture/search-mode-switching-mechanism.md`
- `docs/architecture/search_with_vectors-call-flow.md`
