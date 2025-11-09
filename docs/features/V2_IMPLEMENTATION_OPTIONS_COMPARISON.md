# 🔍 V2 視窗擴展實現方案比較

## 📊 兩種實現方案的完整比較

---

## 選項 A：擴展現有 `search_with_context()` 方法

### ✅ 優點

1. **代碼統一性** ⭐⭐⭐⭐⭐
   - 只有一個搜尋方法，維護簡單
   - 不會造成「該用哪個方法？」的困惑
   - 符合 DRY 原則（Don't Repeat Yourself）

2. **向後兼容** ⭐⭐⭐⭐⭐
   - 新增參數有預設值，不會影響現有調用
   - 現有代碼無需修改即可繼續運作
   - 漸進式升級，風險低

3. **API 一致性** ⭐⭐⭐⭐⭐
   - ViewSet 已經在調用 `search_with_context()`
   - 只需添加參數傳遞，不用改調用邏輯
   - 前端 API 不需要變更

4. **靈活性高** ⭐⭐⭐⭐⭐
   - 可以透過 `context_mode` 參數選擇模式：
     - `'hierarchical'`: 層級上下文（父子兄弟）
     - `'adjacent'`: 線性視窗（前後段落）
     - `'both'`: 兩種都包含
   - 未來可以輕鬆擴展更多模式

5. **測試成本低** ⭐⭐⭐⭐
   - 只需測試一個方法的不同參數組合
   - 現有測試繼續有效（預設參數）
   - 新增測試案例即可

6. **文檔清晰** ⭐⭐⭐⭐
   - 只需維護一份 API 文檔
   - 參數說明清楚即可
   - 減少學習成本

### ❌ 缺點

1. **方法複雜度增加** ⚠️
   - 一個方法處理多種模式，代碼較長
   - 需要內部邏輯判斷（if/else）
   - 但這是可控的複雜度

2. **重構風險** ⚠️
   - 需要修改現有方法
   - 如果實現有 bug，會影響現有功能
   - **緩解方法**：充分測試，保持向後兼容

### 📝 實現範例

```python
def search_with_context(
    self,
    query: str,
    source_table: str,
    limit: int = 3,
    threshold: float = 0.7,
    min_level: int = 1,
    max_level: int = 6,
    include_siblings: bool = False,
    context_window: int = 1,  # ✅ 新增
    context_mode: str = 'hierarchical'  # ✅ 新增，預設為現有行為
) -> List[Dict[str, Any]]:
    """
    搜尋段落（包含上下文）
    
    Args:
        context_mode: 上下文模式
            - 'hierarchical': 層級結構（父子兄弟）- 預設
            - 'adjacent': 線性視窗（前後段落）
            - 'both': 同時包含兩種上下文
        context_window: 視窗大小（僅 adjacent/both 模式）
    """
    sections = self.search_sections(
        query, source_table, limit, 
        threshold, min_level, max_level
    )
    
    for section in sections:
        if context_mode in ['hierarchical', 'both']:
            # 原有邏輯：層級上下文
            section['parent'] = self._get_parent_section(...)
            section['children'] = self._get_child_sections(...)
            if include_siblings:
                section['siblings'] = self._get_sibling_sections(...)
        
        if context_mode in ['adjacent', 'both']:
            # ✅ 新增邏輯：線性視窗
            adjacent = self._get_adjacent_sections(
                source_table,
                section['source_id'],
                section['section_id'],
                window_size=context_window
            )
            section['previous'] = adjacent['previous']
            section['next'] = adjacent['next']
    
    return sections
```

**修改行數**：約 30-40 行（含新增輔助方法 50 行）

---

## 選項 B：創建新方法 `search_with_expanded_context()`

### ✅ 優點

1. **職責分離** ⭐⭐⭐
   - 新方法專注於視窗擴展
   - 舊方法保持不變，零風險
   - 符合 SOLID 原則中的單一職責

2. **零風險** ⭐⭐⭐⭐⭐
   - 完全不會影響現有功能
   - 即使新方法有 bug，舊方法依然正常
   - 適合不熟悉現有代碼的開發者

3. **清晰度高** ⭐⭐⭐⭐
   - 方法名稱明確表達用途
   - 不會有「這個參數該傳什麼」的困惑
   - 新手友好

### ❌ 缺點

1. **代碼重複** ❌❌❌
   - 需要複製基礎搜尋邏輯
   - 兩個方法都要調用 `search_sections()`
   - 違反 DRY 原則

2. **維護成本高** ❌❌❌❌
   - 修改一處功能，兩個方法都要改
   - Bug 修復需要同步兩個方法
   - 容易遺漏同步，造成不一致

3. **選擇困難** ❌❌
   - 開發者會困惑：「該用哪個方法？」
   - 需要額外文檔說明使用場景
   - API 變得複雜

4. **ViewSet 需要大改** ❌❌❌
   - 需要修改 ViewSet 的調用邏輯
   - 增加判斷：用哪個方法？
   - 前端可能需要傳遞更多參數

5. **擴展性差** ❌❌
   - 如果未來需要「同時支援兩種模式」怎麼辦？
   - 再創建第三個方法 `search_with_full_context()`？
   - 方法數量會爆炸

6. **測試成本高** ❌❌
   - 需要測試兩個方法
   - 需要測試方法間的差異
   - 測試案例數量加倍

### 📝 實現範例

```python
def search_with_expanded_context(
    self,
    query: str,
    source_table: str,
    limit: int = 3,
    threshold: float = 0.7,
    min_level: int = 1,
    max_level: int = 6,
    context_window: int = 1
) -> List[Dict[str, Any]]:
    """
    搜尋段落（包含線性視窗上下文）
    """
    # ❌ 代碼重複：又要調用 search_sections
    sections = self.search_sections(
        query, source_table, limit,
        threshold, min_level, max_level
    )
    
    for section in sections:
        # 只實現視窗邏輯
        adjacent = self._get_adjacent_sections(
            source_table,
            section['source_id'],
            section['section_id'],
            window_size=context_window
        )
        section['previous'] = adjacent['previous']
        section['next'] = adjacent['next']
    
    return sections

# ❌ ViewSet 需要大改
if version == 'v2':
    if context_mode == 'hierarchical':
        raw_results = search_service.search_with_context(...)
    elif context_mode == 'adjacent':
        raw_results = search_service.search_with_expanded_context(...)
    else:
        # 如果要同時支援兩種？需要再寫一個方法？
        pass
```

**修改行數**：約 60-80 行（新方法 + ViewSet 邏輯修改）

---

## 📊 綜合評分表

| 評估項目 | 選項 A（擴展現有） | 選項 B（創建新方法） | 說明 |
|---------|-------------------|---------------------|------|
| **代碼維護性** | ⭐⭐⭐⭐⭐ | ⭐⭐ | A 只需維護一個方法 |
| **實現成本** | ⭐⭐⭐⭐ | ⭐⭐⭐ | A 稍微複雜一點 |
| **風險控制** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | B 完全無風險 |
| **擴展性** | ⭐⭐⭐⭐⭐ | ⭐⭐ | A 可輕鬆添加新模式 |
| **代碼重複** | ⭐⭐⭐⭐⭐ | ⭐ | B 有明顯重複 |
| **API 一致性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | A 不改變 API |
| **測試成本** | ⭐⭐⭐⭐ | ⭐⭐ | A 測試案例較少 |
| **文檔複雜度** | ⭐⭐⭐⭐ | ⭐⭐ | A 只需一份文檔 |
| **學習曲線** | ⭐⭐⭐ | ⭐⭐⭐⭐ | B 概念更簡單 |
| **長期維護** | ⭐⭐⭐⭐⭐ | ⭐⭐ | A 更易維護 |

**總分**：
- **選項 A**：45/50 ⭐⭐⭐⭐⭐
- **選項 B**：26/50 ⭐⭐⭐

---

## 🎯 推薦決策

### 🏆 **強烈推薦：選項 A（擴展現有方法）**

### 理由

1. **符合軟體工程最佳實踐**
   - DRY 原則（不重複代碼）
   - 單一數據源（Single Source of Truth）
   - 低耦合高內聚

2. **實際案例參考**
   - Django ORM 的 `filter()` 方法就是透過參數支援各種查詢
   - Elasticsearch 的搜尋 API 也是一個端點，多種模式
   - 這是業界標準做法

3. **未來證明（Future-Proof）**
   - 如果需求變更：「V3 要同時支援兩種上下文」
   - 選項 A：添加 `context_mode='both'` 即可（5 分鐘）
   - 選項 B：需要創建第三個方法或大規模重構（1 小時+）

4. **團隊協作友好**
   - 新成員只需學習一個方法
   - 代碼審查更簡單（只看一個方法）
   - 減少「這兩個方法有什麼差別？」的問題

### 風險緩解

選項 A 的唯一風險是「修改現有方法」，但可以這樣緩解：

1. **充分測試**
   ```python
   # 測試預設行為（向後兼容）
   test_search_with_context_default()
   
   # 測試新模式
   test_search_with_context_adjacent_mode()
   test_search_with_context_both_mode()
   ```

2. **漸進式部署**
   - Step 1: 添加參數（預設值保持舊行為）
   - Step 2: 測試所有模式
   - Step 3: 部署到生產環境
   - Step 4: 逐步啟用新模式

3. **快速回滾機制**
   - Git 分支保護
   - 如果有問題，一行代碼即可回到舊行為：
     ```python
     context_mode = 'hierarchical'  # 強制使用舊模式
     ```

---

## 💡 具體實施建議（選項 A）

### Phase 1：準備工作（10 分鐘）
1. 創建新分支 `feature/context-window-expansion`
2. 備份現有測試結果
3. 編寫測試案例骨架

### Phase 2：實現核心邏輯（30 分鐘）
1. 實現 `_get_adjacent_sections()` 輔助方法
2. 修改 `search_with_context()` 方法簽名
3. 添加 `context_mode` 判斷邏輯

### Phase 3：ViewSet 整合（10 分鐘）
1. 修改 RVT ViewSet 傳遞參數
2. 修改 Protocol ViewSet 傳遞參數

### Phase 4：測試驗證（20 分鐘）
1. 單元測試（測試各種模式）
2. 整合測試（測試 ViewSet）
3. 瀏覽器功能測試

### Phase 5：文檔更新（10 分鐘）
1. 更新 API 文檔
2. 更新功能說明

**總工作時間**：約 1.5 小時

---

## 🎯 最終建議

**選擇選項 A（擴展現有方法）**，因為：

✅ **長期維護成本最低**  
✅ **代碼質量最高**  
✅ **擴展性最好**  
✅ **符合業界標準**  
✅ **團隊協作最友好**

唯一需要注意的是：**充分測試**，確保向後兼容性。

---

**推薦指數**：⭐⭐⭐⭐⭐（5/5）

**建議行動**：立即開始實施選項 A

---

**分析日期**：2025-11-09  
**分析者**：AI Development Assistant  
**推薦方案**：選項 A - 擴展現有 `search_with_context()` 方法
