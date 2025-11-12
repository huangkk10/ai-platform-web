# 阶段 2 查询重写必要性分析

## 📋 问题描述

在两阶段搜索的阶段 2 中，当前实现会添加"完整內容"关键字：

```python
# 当前实现
if is_full_search:
    rewritten_query = f"{query} 完整內容"  # Stage 2
else:
    rewritten_query = query  # Stage 1
```

**核心问题**：`search_with_vectors()` 已经有自动降级机制（段落 → 文档），那么添加"完整內容"是否必要？

---

## 🔍 深度分析

### 方案 A：保留"完整內容"（当前实现）

#### 执行流程
```
用户查询: "Cup 如何测试?"
阶段 2 重写: "Cup 如何测试? 完整內容"
    ↓
Dify 调用外部知识库 API
    ↓
search_with_vectors(query="Cup 如何测试? 完整內容", threshold=0.75)
    ↓
步骤 1: 段落向量搜索
    └─ 向量化: embedding("Cup 如何测试? 完整內容")
    └─ 匹配段落: 相似度可能降低（多了2个字）
    └─ 结果: 可能找不到段落（threshold=0.75）
    └─ section_results = []
    ↓
步骤 2: 自动降级（因为 section_results 为空）
    └─ 整篇文档搜索 (threshold=0.6375)
    └─ 找到完整文档 ✅
    ↓
返回给 Dify
    ↓
Dify Prompt 检测到"完整內容"
    └─ LLM 使用详细模式组织答案 ✅
```

#### 优点
1. ✅ **双重保险**：即使段落搜索成功，"完整內容"也能引导 LLM 详细回答
2. ✅ **Prompt 层控制**：Dify Prompt 可以根据"完整內容"调整回答风格
3. ✅ **语义提示**：告诉系统用户想要完整信息

#### 缺点
1. ⚠️ **可能降低匹配度**：添加"完整內容"改变向量，可能导致原本能匹配的段落无法匹配
2. ⚠️ **依赖降级机制**：期望段落搜索失败来触发文档搜索，这不是主动控制
3. ⚠️ **不够直接**：通过"意外失败"来达成目标

---

### 方案 B：移除"完整內容"（建议测试）

#### 执行流程
```
用户查询: "Cup 如何测试?"
阶段 2 保持: "Cup 如何测试?"  # ← 不添加"完整內容"
    ↓
Dify 调用外部知识库 API
    ↓
search_with_vectors(query="Cup 如何测试?", threshold=0.75)
    ↓
步骤 1: 段落向量搜索
    └─ 向量化: embedding("Cup 如何测试?")
    └─ 匹配段落: 找到 2 个段落 (0.86, 0.82) ✅
    └─ section_results = [{...}, {...}]
    └─ 返回段落结果 ← 不会降级！
    ↓
返回给 Dify（2 个段落）
    ↓
Dify Prompt 无法区分阶段 1 和阶段 2
    └─ LLM 可能使用相同模式回答 ⚠️
    └─ 阶段 2 回答可能与阶段 1 相同 ⚠️
```

#### 优点
1. ✅ **简化逻辑**：不需要查询重写
2. ✅ **保持向量一致性**：阶段 1 和阶段 2 使用相同向量

#### 缺点
1. ❌ **失去 Prompt 控制**：Dify 无法区分阶段 1 和阶段 2
2. ❌ **可能返回相同结果**：段落搜索成功 → 返回段落 → LLM 回答可能相同
3. ❌ **不确定性问题无法解决**：如果阶段 1 因为段落内容不足而不确定，阶段 2 还是返回相同段落

---

## 📊 关键差异对比

| 方面 | 方案 A（添加"完整內容"） | 方案 B（不添加） |
|------|-------------------------|-----------------|
| **段落搜索结果** | 可能失败（向量改变） | 通常成功 |
| **是否降级到文档搜索？** | 容易触发（期望行为） | 不容易触发 |
| **Dify Prompt 能否区分阶段？** | ✅ 能（检测"完整內容"） | ❌ 不能 |
| **LLM 回答风格** | 详细模式（受 Prompt 控制） | 可能与阶段 1 相同 |
| **解决不确定性概率** | 较高（文档搜索 + 详细模式） | 较低（相同段落 + 相同模式） |

---

## 🎯 核心问题：为什么阶段 1 不确定？

### 原因 1：段落内容不足
```
阶段 1 段落结果：
- 段落 1: "Cup 测试准备步骤..."（100 字）
- 段落 2: "测试注意事项..."（80 字）

问题：内容零散，LLM 无法组织完整答案
→ 回答："可能需要..."（不确定）
```

**解决方案**：
- ✅ 方案 A：降级到文档搜索 → 获得完整文档（2000 字）→ LLM 有足够上下文
- ❌ 方案 B：返回相同段落 → LLM 仍然内容不足 → 仍不确定

### 原因 2：Prompt 理解问题
```
阶段 1 Prompt 模式：简洁回答
→ LLM 使用简短风格："可能是..."

问题：简短回答容易触发不确定关键字
```

**解决方案**：
- ✅ 方案 A：Prompt 检测"完整內容" → 切换详细模式 → 避免简短回答
- ⚠️ 方案 B：Prompt 无法区分阶段 → 仍使用简洁模式 → 可能仍不确定

---

## 🧪 实验验证

### 实验 1：测试"完整內容"对向量匹配的影响

```python
# 测试代码
from api.services.embedding_service import get_embedding_service

service = get_embedding_service()

# 原查询向量
query_1 = "Cup 如何测试?"
results_1 = service.semantic_search(
    query=query_1,
    source_table='protocol_guide',
    top_k=3,
    threshold=0.75
)

# 添加"完整內容"后的向量
query_2 = "Cup 如何测试? 完整內容"
results_2 = service.semantic_search(
    query=query_2,
    source_table='protocol_guide',
    top_k=3,
    threshold=0.75
)

# 对比结果
print("原查询结果:")
for r in results_1:
    print(f"  - {r['similarity']:.3f}: {r['title']}")

print("\n添加'完整內容'后结果:")
for r in results_2:
    print(f"  - {r['similarity']:.3f}: {r['title']}")
```

**预期结果**：
- 如果相似度差异 < 0.05：影响不大
- 如果相似度差异 > 0.05：显著影响

---

### 实验 2：测试阶段 2 去掉"完整內容"的效果

```bash
# 修改代码
# two_tier_handler.py line 228
# 改为：rewritten_query = query

# 测试查询
curl -X POST "http://localhost/api/rvt-guide/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Cup 如何测试",
    "conversation_id": null
  }'
```

**观察指标**：
1. 阶段 1 是否不确定？
2. 阶段 2 是否进入？
3. 阶段 2 搜索结果是否与阶段 1 相同？
4. 阶段 2 回答是否仍不确定？

---

## 💡 建议方案

### 选项 1：保留"完整內容"（推荐保守方案）⭐

**理由**：
1. **双重机制**：向量变化 + Prompt 检测，增加阶段 2 成功率
2. **Prompt 控制**：Dify 可以根据"完整內容"调整回答风格
3. **实验验证过**：Protocol Guide 使用此方案效果良好

**适用场景**：
- Dify Prompt 配置了"完整內容"检测
- 期望阶段 2 使用不同的回答风格
- 担心段落内容不足导致不确定

---

### 选项 2：移除"完整內容"，依赖自动降级（激进方案）

**理由**：
1. **简化逻辑**：不需要查询重写
2. **依赖降级机制**：相信 `search_with_vectors()` 的降级逻辑
3. **保持向量一致性**：避免向量变化

**风险**：
1. ❌ 如果段落搜索成功，阶段 2 可能与阶段 1 相同
2. ❌ Dify Prompt 无法区分阶段
3. ❌ 不确定性可能无法解决

**需要配合的改进**：
```python
# 需要在 Prompt 中区分阶段
# 方法：传递元数据
response = self.dify_client.chat(
    question=query,  # 不添加"完整內容"
    conversation_id=conversation_id,
    user=user_id,
    inputs={
        'search_stage': 'stage_2',  # ← 通过 inputs 传递阶段信息
        'require_detailed_answer': True
    }
)
```

---

### 选项 3：混合方案（智能选择）⭐⭐

**核心思想**：根据阶段 1 的失败原因决定是否添加"完整內容"

```python
def _request_dify_chat(
    self,
    query: str,
    conversation_id: str,
    user_id: str,
    is_full_search: bool = False,
    stage_1_metadata: dict = None  # ← 新增：阶段 1 的元数据
) -> Dict[str, Any]:
    """智能查询重写"""
    
    if is_full_search:
        # 检查阶段 1 是否触发了文档搜索
        stage_1_used_doc_search = (
            stage_1_metadata and 
            '整篇文檔' in stage_1_metadata.get('search_method', '')
        )
        
        if stage_1_used_doc_search:
            # 阶段 1 已经用了文档搜索，不需要添加"完整內容"
            # 通过 inputs 传递阶段信息给 Prompt
            rewritten_query = query
            use_stage_metadata = True
        else:
            # 阶段 1 用了段落搜索，添加"完整內容"触发文档搜索
            rewritten_query = f"{query} 完整內容"
            use_stage_metadata = False
    else:
        rewritten_query = query
        use_stage_metadata = False
    
    # 调用 Dify
    response = self.dify_client.chat(
        question=rewritten_query,
        conversation_id=conversation_id,
        user=user_id,
        inputs={'search_stage': 'stage_2'} if use_stage_metadata else {}
    )
    
    return response
```

**优点**：
1. ✅ 避免不必要的查询重写
2. ✅ 根据实际情况智能决策
3. ✅ 保持 Prompt 控制能力

---

## 📋 决策树

```
阶段 1 是否不确定？
├─ 否 → 返回阶段 1 结果（结束）
│
└─ 是 → 进入阶段 2
    │
    ├─ 阶段 1 使用了文档搜索？
    │  ├─ 是 → 不添加"完整內容"
    │  │      传递 inputs={'search_stage': 'stage_2'}
    │  │      期望：Prompt 使用详细模式
    │  │
    │  └─ 否（段落搜索）→ 添加"完整內容"
    │         期望：触发文档搜索 + Prompt 详细模式
    │
    └─ 阶段 2 是否确定？
       ├─ 是 → 返回阶段 2 结果
       └─ 否 → 降级模式（组合回答）
```

---

## 🎯 最终推荐

### 短期（立即可行）：**保留"完整內容"（当前实现）**

**理由**：
1. 已验证有效（Protocol Guide）
2. 风险最低
3. 不需要修改 Dify Prompt

### 中期（优化方向）：**实验验证**

执行上述实验 1 和实验 2，收集数据：
- "完整內容"对向量匹配的实际影响
- 去掉"完整內容"后的阶段 2 效果

### 长期（终极方案）：**混合方案 + 显式搜索模式控制**

**最佳架构改进**：
```python
# 在 search_with_vectors() 中添加显式 search_mode 参数
def search_with_vectors(
    self, 
    query, 
    limit=5, 
    threshold=0.7,
    search_mode='auto'  # ← 新增：'auto', 'section_only', 'document_only'
):
    if search_mode == 'document_only':
        # 阶段 2 直接跳过段落搜索
        return search_with_vectors_generic(...)
    elif search_mode == 'section_only':
        # 只执行段落搜索，不降级
        return search_sections(...)
    else:  # 'auto'
        # 当前的自动降级逻辑
        ...
```

然后在两阶段处理中：
```python
# 阶段 2 显式请求文档搜索
stage_2_results = search_service.search_knowledge(
    query=user_query,  # 不需要添加"完整內容"
    search_mode='document_preferred'  # ← 显式控制
)
```

---

## 📊 总结表

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **保留"完整內容"** | 双重保险、Prompt 控制、已验证 | 依赖降级、向量变化 | ⭐⭐⭐⭐ |
| **移除"完整內容"** | 简化逻辑、向量一致 | 可能无效、失去 Prompt 控制 | ⭐⭐ |
| **混合方案** | 智能决策、最优效果 | 复杂度高、需要元数据传递 | ⭐⭐⭐⭐⭐（长期） |
| **显式搜索模式** | 最直接、可控性强 | 需要架构改进 | ⭐⭐⭐⭐⭐（终极） |

---

## 🔍 答案总结

**回到您的问题**："是不是使用 `rewritten_query = query` 也可以呢？"

**答案**：
- ✅ **技术上可以**：`search_with_vectors()` 确实有自动降级机制
- ⚠️ **但不推荐**：会失去 Dify Prompt 的阶段区分能力
- 💡 **建议**：保留"完整內容"，或使用混合方案

**关键洞察**：
> "完整內容"的作用不仅是触发文档搜索，更重要的是**告诉 Dify Prompt 这是阶段 2，应该使用详细模式回答**。即使段落搜索成功，Prompt 层的区分仍然有价值。

---

**文档版本**：v1.0  
**创建日期**：2025-11-12  
**作者**：AI Platform Team
