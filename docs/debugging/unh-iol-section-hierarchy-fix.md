# 🔧 UNH-IOL 文档段落层级关系修正方案

## 📋 问题概述

**影响文档**：UNH-IOL (protocol_guide id=10)

**问题描述**：
Section 4, 5, 6, 7 的标题明确显示它们是**顶级段落**（如 "4.IOL 版本對應"），但在数据库中被错误标记为：
- `heading_level = 2`（应该是 1）
- `parent_section_id = 'sec_3'`（应该是 NULL）

这导致这些段落被误认为是 Section 3 的子段落。

---

## 🔍 问题详情

### 数据库实际情况

```sql
-- 当前错误的数据结构
id  | section_id | heading_text                  | level | parent_section_id
----+------------+-------------------------------+-------+-------------------
151 | sec_3      | 3. IOL 放測 SOP               | 1     | NULL              ✅
152 | sec_4      | 3.1 以右圖上步選...            | 2     | sec_3             ✅ 正确
153 | sec_5      | 3.2 執行指令                   | 2     | sec_3             ✅ 正确
154 | sec_6      | 3.2.1 如下圖示...              | 3     | sec_5             ✅ 正确
155 | sec_7      | 4.IOL 版本對應NVMe SPEC版本    | 2     | sec_3             ❌ 错误！
156 | sec_8      | 5.IOL 安裝需求                 | 2     | sec_3             ❌ 错误！
157 | sec_9      | 6.全新 Ubuntu 18.04...        | 2     | sec_3             ❌ 错误！
158 | sec_10     | 7. 常見問題                    | 2     | sec_3             ❌ 错误！
```

### 应该的正确结构

```sql
-- 正确的数据结构
id  | section_id | heading_text                  | level | parent_section_id
----+------------+-------------------------------+-------+-------------------
151 | sec_3      | 3. IOL 放測 SOP               | 1     | NULL              
152 | sec_4      | 3.1 以右圖上步選...            | 2     | sec_3             
153 | sec_5      | 3.2 執行指令                   | 2     | sec_3             
154 | sec_6      | 3.2.1 如下圖示...              | 3     | sec_5             
155 | sec_7      | 4.IOL 版本對應NVMe SPEC版本    | 1     | NULL              ✅ 修正
156 | sec_8      | 5.IOL 安裝需求                 | 1     | NULL              ✅ 修正
157 | sec_9      | 6.全新 Ubuntu 18.04...        | 1     | NULL              ✅ 修正
158 | sec_10     | 7. 常見問題                    | 1     | NULL              ✅ 修正
```

---

## 💥 问题影响

### 1. Child Expansion 功能影响

**当前行为**：
```python
# 用户查询 "IOL 放測 SOP"
results = service.search_knowledge("IOL 放測 SOP")

# 系统检测到 Section 3 内容为空，展开子段落
# 查询到 6 个"子段落"：
[
    "3.1 以右圖上步選...",      # ✅ 正确的子段落
    "3.2 執行指令",             # ✅ 正确的子段落
    "4.IOL 版本對應...",        # ❌ 不应该在这里！
    "5.IOL 安裝需求",           # ❌ 不应该在这里！
    "6.全新 Ubuntu...",         # ❌ 不应该在这里！
    "7. 常見問題"               # ❌ 不应该在这里！
]

# 结果：用户看到混合的内容（2 个正确 + 4 个不相关）
```

**修正后行为**：
```python
# 查询到 2 个真正的子段落：
[
    "3.1 以右圖上步選...",      # ✅ 
    "3.2 執行指令",             # ✅
]
# 其中 3.2 还会展开其子段落 3.2.1
```

### 2. Hierarchical Mode 影响

**当前行为**：
```python
# 用户搜索时，Section 4-7 会错误地显示为 Section 3 的兄弟段落
results = service.search_with_context(
    query="IOL 版本",
    context_mode='hierarchical',
    include_siblings=True
)

# Section 7 (4.IOL 版本對應) 的上下文会包含：
{
    'parent': 'Section 3',        # ❌ 错误！
    'siblings': [                 # ❌ 错误的兄弟段落
        '3.1 以右圖上步選...',
        '3.2 執行指令',
        '5.IOL 安裝需求',
        '6.全新 Ubuntu...',
        '7. 常見問題'
    ]
}
```

**修正后行为**：
```python
# Section 7 (4.IOL 版本對應) 的上下文：
{
    'parent': None,               # ✅ 顶级段落
    'siblings': [                 # ✅ 正确的兄弟段落
        'Section 1',
        'Section 2', 
        'Section 3',
        'Section 5',
        'Section 6',
        'Section 7'
    ]
}
```

---

## 🛠️ 修正方案

### 方案 A：SQL 直接修正（推荐）⭐⭐⭐⭐⭐

**优点**：
- ✅ 快速（< 1 分钟）
- ✅ 精准（只修正错误的 4 个段落）
- ✅ 不影响其他数据
- ✅ 可回滚

**步骤**：

#### 步骤 1：备份数据（可选但推荐）

```bash
# 备份受影响的记录
docker exec postgres_db psql -U postgres -d ai_platform -c "
CREATE TABLE document_section_embeddings_backup_20251110 AS
SELECT * FROM document_section_embeddings
WHERE source_table = 'protocol_guide'
  AND source_id = 10
  AND section_id IN ('sec_7', 'sec_8', 'sec_9', 'sec_10');
"
```

#### 步骤 2：修正 heading_level 和 parent_section_id

```sql
-- 修正 Section 4, 5, 6, 7 的层级和父段落关系
UPDATE document_section_embeddings
SET 
    heading_level = 1,              -- 改为顶级段落
    parent_section_id = NULL,       -- 移除错误的父段落关系
    updated_at = CURRENT_TIMESTAMP
WHERE source_table = 'protocol_guide'
  AND source_id = 10
  AND section_id IN ('sec_7', 'sec_8', 'sec_9', 'sec_10');
```

#### 步骤 3：验证修正结果

```sql
-- 验证：Section 3 现在应该只有 2 个子段落
SELECT COUNT(*) as child_count
FROM document_section_embeddings
WHERE parent_section_id = 'sec_3';
-- 预期结果：2 (sec_4 和 sec_5)

-- 验证：Section 4-7 现在是顶级段落
SELECT section_id, heading_text, heading_level, parent_section_id
FROM document_section_embeddings
WHERE section_id IN ('sec_7', 'sec_8', 'sec_9', 'sec_10');
-- 预期：level = 1, parent_section_id = NULL
```

#### 步骤 4：更新 is_parent 标记（如果存在此字段）

```sql
-- 如果 is_parent 字段存在，更新 Section 3 的标记
UPDATE document_section_embeddings
SET is_parent = true
WHERE section_id = 'sec_3'
  AND source_table = 'protocol_guide'
  AND source_id = 10;

-- Section 4-7 不再是父段落（因为它们可能没有子段落）
-- 这需要根据实际情况判断
```

---

### 方案 B：重新生成向量（备选）⭐⭐⭐

**优点**：
- ✅ 完全重建，确保数据一致性
- ✅ 如果有其他隐藏问题也会一并解决

**缺点**：
- ❌ 耗时较长（5-10 分钟）
- ❌ 需要重新生成所有向量
- ❌ 可能影响现有搜索结果

**步骤**：

```bash
# 1. 删除旧的向量数据
docker exec postgres_db psql -U postgres -d ai_platform -c "
DELETE FROM document_section_embeddings
WHERE source_table = 'protocol_guide'
  AND source_id = 10;
"

# 2. 重新生成向量（假设有此脚本）
docker exec ai-django python manage.py regenerate_section_vectors \
    --source-table protocol_guide \
    --source-id 10

# 或使用现有的脚本
docker exec ai-django python regenerate_section_multi_vectors.py \
    --doc-id 10
```

---

## 🚀 推荐执行方案（方案 A）

### 完整的修正脚本

创建一个 SQL 脚本文件：

```sql
-- fix_unh_iol_hierarchy.sql
-- 修正 UNH-IOL 文档的段落层级关系

BEGIN;

-- 1. 备份（可选）
CREATE TABLE IF NOT EXISTS document_section_embeddings_backup_20251110 AS
SELECT * FROM document_section_embeddings
WHERE source_table = 'protocol_guide'
  AND source_id = 10
  AND section_id IN ('sec_7', 'sec_8', 'sec_9', 'sec_10');

-- 2. 修正层级和父段落关系
UPDATE document_section_embeddings
SET 
    heading_level = 1,
    parent_section_id = NULL,
    updated_at = CURRENT_TIMESTAMP
WHERE source_table = 'protocol_guide'
  AND source_id = 10
  AND section_id IN ('sec_7', 'sec_8', 'sec_9', 'sec_10');

-- 3. 验证结果
DO $$
DECLARE
    child_count INTEGER;
    top_level_count INTEGER;
BEGIN
    -- 检查 Section 3 的子段落数量
    SELECT COUNT(*) INTO child_count
    FROM document_section_embeddings
    WHERE parent_section_id = 'sec_3';
    
    IF child_count != 2 THEN
        RAISE EXCEPTION 'Section 3 应该有 2 个子段落，但现在有 %', child_count;
    END IF;
    
    -- 检查顶级段落数量
    SELECT COUNT(*) INTO top_level_count
    FROM document_section_embeddings
    WHERE source_table = 'protocol_guide'
      AND source_id = 10
      AND heading_level = 1;
    
    IF top_level_count != 7 THEN
        RAISE NOTICE '警告：顶级段落数量为 %，预期 7 个', top_level_count;
    END IF;
    
    RAISE NOTICE '✅ 修正成功！Section 3 现在有 % 个子段落，共 % 个顶级段落', child_count, top_level_count;
END $$;

COMMIT;
```

### 执行命令

```bash
# 方法 1：直接执行 SQL
docker exec postgres_db psql -U postgres -d ai_platform -c "
BEGIN;

-- 修正层级和父段落关系
UPDATE document_section_embeddings
SET 
    heading_level = 1,
    parent_section_id = NULL,
    updated_at = CURRENT_TIMESTAMP
WHERE source_table = 'protocol_guide'
  AND source_id = 10
  AND section_id IN ('sec_7', 'sec_8', 'sec_9', 'sec_10');

-- 显示修正结果
SELECT 
    section_id, 
    heading_text, 
    heading_level, 
    parent_section_id 
FROM document_section_embeddings
WHERE source_table = 'protocol_guide'
  AND source_id = 10
  AND section_id IN ('sec_7', 'sec_8', 'sec_9', 'sec_10');

COMMIT;
"

# 方法 2：使用 SQL 文件
# docker exec -i postgres_db psql -U postgres -d ai_platform < fix_unh_iol_hierarchy.sql
```

---

## ✅ 验证修正效果

### 1. 数据库验证

```bash
# 验证 Section 3 的子段落
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    section_id,
    heading_text,
    heading_level,
    parent_section_id
FROM document_section_embeddings
WHERE parent_section_id = 'sec_3'
ORDER BY id;
"
# 预期：只有 2 条记录（sec_4 和 sec_5）
```

### 2. 功能验证

```bash
# 测试 Child Expansion
docker exec ai-django python -c "
import os, sys, django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService

service = ProtocolGuideSearchService()
results = service.search_knowledge('IOL 放測 SOP', limit=1)

if results:
    content = results[0]['content']
    
    # 检查子段落
    expected = ['3.1', '3.2']
    unexpected = ['4.IOL', '5.IOL', '6.全新', '7. 常見']
    
    found_expected = [s for s in expected if s in content]
    found_unexpected = [s for s in unexpected if s in content]
    
    print(f'✅ 预期子段落: {len(found_expected)}/{len(expected)}')
    print(f'❌ 不应出现: {len(found_unexpected)}/{len(unexpected)}')
    
    if len(found_expected) == 2 and len(found_unexpected) == 0:
        print('\\n🎉 修正成功！')
    else:
        print('\\n⚠️ 还有问题')
"
```

### 3. 重新运行测试

```bash
# 运行简化测试
docker exec ai-django python test_context_window_simple.py

# 预期：Test 4 应该显示更清晰的结果
# - 只展开 2 个子段落（不是 6 个）
# - 内容更精确相关
```

---

## 📊 修正前后对比

### 修正前

```
查询: "IOL 放測 SOP"

日志: 📑 段落 '3. IOL 放測 SOP' 無內容，展開 6 個子段落

返回内容包含:
✅ 3.1 以右圖上步選...
✅ 3.2 執行指令
❌ 4.IOL 版本對應...    (不相关！)
❌ 5.IOL 安裝需求        (不相关！)
❌ 6.全新 Ubuntu...      (不相关！)
❌ 7. 常見問題           (不相关！)

内容长度: ~1107 字符（包含不相关内容）
```

### 修正后

```
查询: "IOL 放測 SOP"

日志: 📑 段落 '3. IOL 放測 SOP' 無內容，展開 2 個子段落

返回内容包含:
✅ 3.1 以右圖上步選...
✅ 3.2 執行指令
✅ 3.2.1 如下圖示...    (3.2 的子段落)

内容长度: ~300-400 字符（精确相关）
```

---

## 🎯 影响评估

### 对现有功能的影响

| 功能 | 修正前 | 修正后 | 影响 |
|------|--------|--------|------|
| **Child Expansion** | 展开 6 个"子段落" | 展开 2 个子段落 | ✅ 更精确 |
| **Hierarchical Mode** | Section 4-7 错误关联到 Section 3 | Section 4-7 独立 | ✅ 更正确 |
| **Adjacent Mode** | 可能包含错误的相邻段落 | 正确的相邻段落 | ✅ 更准确 |
| **搜索结果** | 可能返回不相关内容 | 返回精确相关内容 | ✅ 更相关 |

### 对用户体验的影响

**修正前**：
- ⚠️ 用户搜索 "IOL 放測" 可能看到混合的内容
- ⚠️ 内容包含 Section 4-7（安装需求、常见问题等）
- ⚠️ 用户需要手动筛选相关信息

**修正后**：
- ✅ 用户只看到 Section 3 真正的子段落
- ✅ 内容更聚焦于 "放測 SOP" 的具体步骤
- ✅ 提高信息检索的精确度

---

## 🔄 回滚方案（如果需要）

如果修正后出现问题，可以快速回滚：

```sql
-- 回滚到修正前的状态
UPDATE document_section_embeddings
SET 
    heading_level = 2,
    parent_section_id = 'sec_3',
    updated_at = CURRENT_TIMESTAMP
WHERE source_table = 'protocol_guide'
  AND source_id = 10
  AND section_id IN ('sec_7', 'sec_8', 'sec_9', 'sec_10');
```

---

## 📅 建议执行时间

**推荐执行时间**：
- 🟢 **现在立即执行**：修正简单、影响小、风险低
- 🟡 **低峰期执行**：如晚上或周末（如果想更谨慎）
- 🔴 **不建议延后**：问题会持续影响搜索质量

**执行时长**：< 1 分钟

**停机时间**：无需停机，可在线修正

---

## 📝 执行清单

修正前的检查：
- [ ] 确认数据库连接正常
- [ ] 确认受影响的 4 个段落（sec_7, sec_8, sec_9, sec_10）
- [ ] 可选：创建备份表

执行修正：
- [ ] 运行 UPDATE SQL 语句
- [ ] 检查 SQL 返回的受影响行数（应该是 4）

验证修正：
- [ ] 查询 Section 3 的子段落数量（应该是 2）
- [ ] 查询 Section 4-7 的 level（应该是 1）
- [ ] 运行 Child Expansion 测试
- [ ] 运行完整测试套件

---

## 💡 预防未来类似问题

### 建议的改进措施

1. **向量生成时的验证**
   ```python
   # 在生成向量时，验证段落层级逻辑
   def validate_section_hierarchy(section):
       # 检查标题编号与 heading_level 是否一致
       title_number = extract_section_number(section.heading_text)
       
       if title_number.count('.') == 0:  # "3" -> level 1
           assert section.heading_level == 1
       elif title_number.count('.') == 1:  # "3.1" -> level 2
           assert section.heading_level == 2
       # ...
   ```

2. **定期数据质量检查**
   ```sql
   -- 检查段落层级异常
   SELECT *
   FROM document_section_embeddings
   WHERE heading_text ~ '^[0-9]+\.'  -- 顶级段落格式
     AND heading_level != 1;         -- 但 level 不是 1
   ```

3. **文档导入时的自动修正**
   - 在导入 Markdown 文档时，根据标题格式自动判断层级
   - 添加层级一致性检查

---

## 🎯 总结

**问题严重性**：🟡 中等（不影响功能，但影响质量）

**修正难度**：🟢 简单（1 条 SQL 语句）

**修正风险**：🟢 低（可快速回滚）

**建议行动**：✅ **立即执行修正**

**预期收益**：
- ✅ 搜索结果更精确
- ✅ Child Expansion 返回正确的子段落
- ✅ 提升用户体验
- ✅ 数据结构更合理

---

**下一步**：执行修正 SQL → 验证结果 → 重新运行测试 → 标记问题为已解决 ✅
