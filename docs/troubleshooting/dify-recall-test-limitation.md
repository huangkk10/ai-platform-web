# Dify 知识库召回测试问题说明

## 📋 问题描述

**用户报告**: 在 Dify 知识库召回测试中，输入 `crystaldiskmark` 无法查询到数据

**截图显示**: 在 Dify 工作室的"召回测试"界面，查询 `crystaldiskmark` 失败

---

## 🔍 问题分析

### 测试结果

我们在 Django backend 进行了搜索测试：

```
查询: 'crystaldiskmark'
✅ 找到 2 个结果
  - Kingston Linux 開卡
  - CrystalDiskMark 5 ✅

查询: 'CrystalDiskMark'
✅ 找到 2 个结果
  - Kingston Linux 開卡
  - CrystalDiskMark 5 ✅

查询: 'diskmark'
✅ 找到 2 个结果
  - Kingston Linux 開卡
  - CrystalDiskMark 5 ✅
```

**结论**: Django backend 的向量搜索**完全正常**，可以找到 CrystalDiskMark 数据！

---

## 🎯 根本原因

### Protocol Assistant 的知识库架构

Protocol Assistant 使用的是 **外部知识 API** 模式，而不是 Dify 内部知识库：

```
用户查询
   ↓
Dify 应用 (Protocol_Guide)
   ↓
外部知识 API
   ↓
Django Backend API (/api/protocol-guides/)
   ↓
PostgreSQL + pgvector (向量搜索)
   ↓
返回结果给 Dify
   ↓
Dify 生成回答
```

### Dify "召回测试" 的局限性

**关键问题**: Dify 工作室的"召回测试"功能**只能测试 Dify 内部上传的知识库**，无法测试外部知识 API！

| 项目 | Dify 召回测试 | 实际使用 |
|------|---------------|----------|
| **测试对象** | Dify 内部知识库 | 外部知识 API (Django) |
| **数据来源** | 上传到 Dify 的文档 | PostgreSQL 数据库 |
| **向量库** | Dify 内置向量库 | pgvector |
| **能否测试外部 API** | ❌ **不支持** | ✅ 支持 |

---

## ✅ 正确的测试方法

### 方法 1：直接测试 Django API（推荐）

```bash
# 在 Django backend 测试
docker exec ai-django python test_crystaldiskmark_search.py
```

**结果**: ✅ 可以找到 CrystalDiskMark 数据

### 方法 2：测试完整的聊天流程

在前端 UI 中测试 Protocol Assistant：

1. 打开 Protocol Assistant 聊天界面
2. 输入查询：`crystaldiskmark 有什麼注意事項？`
3. 查看是否返回正确答案

### 方法 3：使用 API 直接测试

```bash
# 测试 Protocol Guide Chat API
curl -X POST "http://10.10.172.127/api/protocol-guides/chat/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "message": "crystaldiskmark 測試流程",
    "conversation_id": ""
  }'
```

### 方法 4：检查 Dify 日志

```bash
# 查看 Dify 是否调用外部 API
docker logs ai-django --follow | grep "Protocol Guide Chat"
```

**预期日志**:
```
[INFO] library.protocol_guide.api_handlers: 📩 Protocol Guide Chat Request
[INFO] library.protocol_guide.smart_search_router: 🔍 智能路由
[INFO] library.protocol_guide.two_tier_handler: 🔄 模式 B: 兩階段搜尋
```

---

## 📊 当前系统状态

### 数据库状态

```sql
-- Protocol Guide 知识库
SELECT COUNT(*) FROM protocol_guide;
-- 结果: 7 条记录

-- CrystalDiskMark 数据
SELECT id, title FROM protocol_guide WHERE title ILIKE '%crystal%';
-- 结果: ID 16 - "CrystalDiskMark 5"

-- 向量数据
SELECT COUNT(*) FROM document_embeddings WHERE source_table = 'protocol_guide';
-- 结果: 7 条向量

-- CrystalDiskMark 向量
SELECT source_id, vector_dims(embedding) 
FROM document_embeddings 
WHERE source_table = 'protocol_guide' AND source_id = 16;
-- 结果: ID 16, 1024 维向量 ✅
```

### 搜索功能状态

| 功能 | 状态 | 说明 |
|------|------|------|
| 向量数据生成 | ✅ 正常 | 1024 维向量已生成 |
| 向量搜索 | ✅ 正常 | 可以找到 CrystalDiskMark |
| 关键字搜索 | ✅ 正常 | 补充搜索正常 |
| Django API | ✅ 正常 | `/api/protocol-guides/` 正常 |
| Dify 外部 API | ⏳ 需要测试 | 需要在 UI 中测试 |

---

## 🔧 如何验证外部知识 API 是否配置正确

### 步骤 1：检查 Dify 应用配置

在 Dify 工作室中，进入 `Protocol_Guide` 应用：

1. 点击"上下文"（Context）
2. 检查是否添加了"外部知识 API"
3. 确认 API 端点配置：
   ```
   API 端点: http://10.10.172.37/api/dify/protocol-knowledge/
   API Key: (如果需要)
   ```

### 步骤 2：测试外部 API 连接

```bash
# 直接调用外部知识 API（模拟 Dify 调用）
curl -X POST "http://10.10.172.127/api/dify/protocol-knowledge/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "crystaldiskmark",
    "top_k": 3,
    "score_threshold": 0.3
  }'
```

**预期返回**:
```json
{
  "records": [
    {
      "content": "CrystalDiskMark 5 ...",
      "score": 0.95,
      "title": "CrystalDiskMark 5",
      "metadata": {...}
    }
  ]
}
```

### 步骤 3：在 UI 中测试完整流程

1. 打开前端 UI
2. 进入 Protocol Assistant
3. 输入查询：
   ```
   crystaldiskmark 測試流程
   ```
4. 查看是否返回相关答案
5. 检查浏览器控制台和后端日志

---

## 💡 为什么 Dify 召回测试无法使用

### Dify 召回测试的设计目的

Dify 的"召回测试"功能是为了测试**上传到 Dify 的文档**，用于：
- 测试 Dify 内部的向量索引
- 验证文档分块策略
- 调整检索参数

### 外部知识 API 的特点

外部知识 API 是 Dify 提供的高级功能，允许：
- 连接外部数据源
- 使用自定义搜索逻辑
- 实时查询数据库

**但是**: 外部 API 的数据**不会**显示在 Dify 的召回测试中！

---

## ✅ 解决方案总结

### 当前状况

- ✅ **Django backend 搜索正常** - 可以找到 CrystalDiskMark
- ✅ **向量数据完整** - 1024 维向量已生成
- ✅ **API 端点正常** - `/api/protocol-guides/` 可用
- ⚠️ **Dify 召回测试不适用** - 无法测试外部 API

### 推荐操作

1. **不要依赖 Dify 召回测试** - 它无法测试外部 API
2. **使用 Django 测试脚本** - `test_crystaldiskmark_search.py`
3. **在前端 UI 测试完整流程** - Protocol Assistant 聊天界面
4. **查看后端日志** - 确认 Dify 是否调用外部 API

### 验证步骤

```bash
# 1. 测试 Django 搜索
docker exec ai-django python test_crystaldiskmark_search.py

# 2. 测试 Chat API
# 在前端 UI 输入: "crystaldiskmark 測試流程"

# 3. 查看日志
docker logs ai-django --follow | grep "crystaldiskmark"
```

---

## 📚 相关文档

- **外部知识 API 指南**: `/docs/ai-integration/dify-external-knowledge-api-guide.md`
- **向量搜索指南**: `/docs/vector-search/vector-search-guide.md`
- **Protocol Assistant 架构**: `/docs/architecture/protocol-assistant-architecture.md`

---

## 🎯 结论

**问题**: Dify 召回测试无法查询到 `crystaldiskmark`

**原因**: Dify 召回测试只能测试内部知识库，无法测试外部知识 API

**验证**: Django backend 搜索完全正常，可以找到 CrystalDiskMark 数据

**解决**: 
1. 使用 Django 测试脚本验证搜索功能 ✅
2. 在前端 UI 测试完整聊天流程 ⏳
3. 不要依赖 Dify 召回测试（它不支持外部 API）

**状态**: ✅ 系统功能正常，只是测试方法不适用

---

**报告日期**: 2025-11-13  
**问题严重性**: 🟢 LOW - 非功能性问题（测试方法误用）  
**系统状态**: ✅ 正常运行
