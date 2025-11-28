# Protocol Assistant 搜尋功能修復規劃文檔

**文件建立日期**：2025-01-27  
**問題狀態**：分析完成，待修復  
**影響範圍**：Protocol Assistant RAG 搜尋功能

---

## 📋 問題摘要

### 用戶反饋
用戶查詢 "crystaldiskmark" 時：
1. **修復前**：完全找不到 "CrystalDiskMark 5" 文檔
2. **修復權重後**：可以找到，但返回內容極少（僅 38 字元）

### 預期行為
- 應該能找到 "CrystalDiskMark 5" 文檔
- 應該返回足夠的內容供 AI 回答問題

---

## 🔍 問題根因分析

### 問題 1：RRF 融合時結果丟失（嚴重）

#### 症狀
- 向量搜尋找到 6 個結果
- 關鍵字搜尋找到 4 個結果  
- RRF 融合後只剩 2 個結果

#### 根因
`_get_doc_identifier()` 函數使用錯誤的欄位讀取文檔 ID：

```python
# 檔案：/library/protocol_guide/search_service.py
# 行數：394

def _get_doc_identifier(self, result: Dict) -> str:
    # ❌ 錯誤：讀取 source_id 或 metadata.source_id
    doc_id = result.get('source_id')
    if doc_id is None:
        metadata = result.get('metadata', {})
        doc_id = metadata.get('source_id')
    
    return f"protocol_guide:{doc_id if doc_id else 'unknown'}"
```

#### 實際資料結構對比

**向量搜尋結果**（來自 section_search_service.py）：
```python
{
    'section_id': 'doc_16',
    'source_id': 16,           # ✅ 有 source_id
    'heading_text': 'CrystalDiskMark 5',
    'content': '...',
    'similarity': 0.901
}
```

**經過 _format_section_results_to_standard 轉換後**：
```python
{
    'content': '## CrystalDiskMark 5\n...',
    'score': 0.901,
    'title': 'CrystalDiskMark 5',
    'metadata': {
        'id': 16,              # ✅ 正確的 ID 在 metadata.id
        'sections_found': 1,
        'max_similarity': 0.901
    }
}
# ⚠️ 注意：頂層沒有 source_id 欄位！
```

**關鍵字搜尋結果**（直接從 DB 查詢）：
```python
{
    'source_id': 16,           # ✅ 頂層有 source_id
    'heading_text': '1.Test Platform',
    'content': '...',
    'similarity': 1.0
}
```

#### 結果
| 搜尋類型 | 結果數 | doc_id 生成 |
|---------|--------|-------------|
| 向量搜尋 | 6 | `protocol_guide:unknown` ❌ |
| 關鍵字搜尋 | 4 | `protocol_guide:16` ✅ |
| RRF 融合後 | 2 | 無法合併，大量結果丟失 |

---

### 問題 2：視窗擴展功能未使用

#### 現有功能
`SectionSearchService` 已有 `context_window` 參數支援視窗擴展：

```python
# 檔案：/library/common/knowledge_base/section_search_service.py
# 行數：57

def search_sections_with_context(
    self, 
    query: str, 
    top_k: int = 5,
    threshold: float = 0.7,
    context_window: int = 1    # 👈 已有此參數
):
```

#### 問題
`ProtocolGuideSearchService` 沒有使用此參數：

```python
# 檔案：/library/protocol_guide/search_service.py

# 向量搜尋時
section_results = self.section_search_service.search_sections(
    query=query,
    top_k=stage1_top_k,
    threshold=adjusted_threshold,
    source_table=self.source_table,
    source_id=None
)
# ❌ 沒有傳遞 context_window
```

#### 影響
- 搜尋 "CrystalDiskMark" 只找到標題段落
- 標題段落內容為空（僅有標題文字 38 字元）
- 子段落展開機制在 `_format_section_results_to_standard` 中有，但只限於直接子段落

---

### 問題 3：子段落展開邏輯的限制

#### 現有邏輯
`_format_section_results_to_standard` 已有子段落展開：

```python
# 當段落內容為空時，查詢子段落
if not content and section_id:
    cursor.execute("""
        SELECT section_id, heading_text, content
        FROM document_section_embeddings
        WHERE source_table = %s 
          AND source_id = %s
          AND parent_section_id = %s
        ORDER BY section_id
        LIMIT 10
    """, [self.source_table, doc_id, section_id])
```

#### 限制
1. 只展開直接子段落（一層）
2. 依賴 `parent_section_id` 欄位（可能未正確設定）
3. 沒有提供上下文鄰近段落

---

## 📊 資料庫現狀

### CrystalDiskMark 5 向量結構

| section_id | heading_level | heading_text | content 長度 | parent_section_id |
|------------|---------------|--------------|-------------|------------------|
| doc_16 | 0 | CrystalDiskMark 5 | 76 | NULL |
| doc_16_1 | 1 | 1.Test Platform | 175 | doc_16 |
| doc_16_2 | 1 | 2.Test Report | 89 | doc_16 |
| doc_16_3 | 1 | 3.Test Checklist | 1234 | doc_16 |
| doc_16_4 | 1 | 4.Test Procedure | 2456 | doc_16 |

### 搜尋權重配置

**版本**：`dify-two-tier-v1.2.2`（is_baseline = true）

| 設定項 | Stage 1 值 | 說明 |
|--------|-----------|------|
| title_weight | 0.9 | 標題權重 90%（已調整）|
| content_weight | 0.1 | 內容權重 10%（已調整）|
| threshold | 0.6 | 相似度閾值 |
| top_k | 8 | 返回數量 |
| hybrid_search | true | 啟用混合搜尋 |
| rrf_k | 60 | RRF 參數 |

---

## ✅ 修復計劃

### 修復 1：修正 `_get_doc_identifier` 函數（優先級：高）

**檔案**：`/library/protocol_guide/search_service.py`  
**行數**：394

**修改前**：
```python
def _get_doc_identifier(self, result: Dict) -> str:
    doc_id = result.get('source_id')
    if doc_id is None:
        metadata = result.get('metadata', {})
        doc_id = metadata.get('source_id')
    
    return f"protocol_guide:{doc_id if doc_id else 'unknown'}"
```

**修改後**：
```python
def _get_doc_identifier(self, result: Dict) -> str:
    """
    從搜尋結果中提取文檔識別碼
    
    支援兩種結果格式：
    1. 原始段落結果：source_id 在頂層
    2. 標準化結果：id 在 metadata.id
    """
    # 優先從 metadata.id 讀取（標準化格式）
    metadata = result.get('metadata', {})
    doc_id = metadata.get('id')
    
    # 回退到頂層 source_id（原始段落格式）
    if doc_id is None:
        doc_id = result.get('source_id')
    
    return f"protocol_guide:{doc_id if doc_id else 'unknown'}"
```

**驗證方式**：
```bash
docker exec ai-django python -c "
from library.protocol_guide.search_service import ProtocolGuideSearchService
service = ProtocolGuideSearchService()

# 測試標準化格式
test1 = {'metadata': {'id': 16}, 'content': 'test'}
print('標準化格式:', service._get_doc_identifier(test1))

# 測試原始段落格式
test2 = {'source_id': 16, 'content': 'test'}
print('原始段落格式:', service._get_doc_identifier(test2))
"
```

---

### 修復 2：添加視窗擴展支援（優先級：中）

**檔案**：`/library/protocol_guide/search_service.py`

**方案 A：使用現有的 context_window 參數**

修改 `_vector_search` 方法，添加 `context_window` 參數：

```python
def _vector_search(self, query: str, stage: int = 1, settings: Dict = None, context_window: int = 2) -> List[Dict]:
    """
    執行向量搜尋
    
    Args:
        context_window: 上下文視窗大小（預設 2，表示前後各 2 個段落）
    """
    # ... 現有邏輯 ...
    
    section_results = self.section_search_service.search_sections_with_context(
        query=query,
        top_k=stage1_top_k,
        threshold=adjusted_threshold,
        source_table=self.source_table,
        source_id=None,
        context_window=context_window  # ✅ 新增
    )
```

**方案 B：在結果格式化時展開更多內容**

修改 `_format_section_results_to_standard` 以獲取更多相鄰段落：

```python
# 當找到標題段落時，自動獲取其下所有內容段落
if heading_level == 0:  # 文檔標題
    cursor.execute("""
        SELECT section_id, heading_text, content
        FROM document_section_embeddings
        WHERE source_table = %s AND source_id = %s
        ORDER BY section_id
        LIMIT 20
    """, [self.source_table, doc_id])
```

**建議**：先實施方案 A，因為改動較小且已有現成功能。

---

### 修復 3：優化關鍵字搜尋結果格式（優先級：低）

**目標**：統一向量搜尋和關鍵字搜尋的結果格式，避免 `_get_doc_identifier` 需要處理多種格式。

**檔案**：`/library/common/knowledge_base/base_search_service.py`

**修改**：在 `search_by_keyword` 方法中，將結果轉換為標準格式：

```python
def search_by_keyword(self, query: str, ...):
    # ... 查詢邏輯 ...
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'content': row[2],
            'score': row[5],
            'title': getattr(self.model_class.objects.get(id=row[0]), 'title', ''),
            'metadata': {
                'id': row[0],           # ✅ 統一放在 metadata.id
                'section_id': row[1],
                'heading_text': row[3],
                'similarity': row[5]
            }
        })
    return results
```

---

## 🧪 測試計劃

### 測試 1：驗證 RRF 融合修復

```bash
docker exec ai-django python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
import django
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService
service = ProtocolGuideSearchService()

results = service.search('crystaldiskmark', top_k=5)
print(f'搜尋結果數量: {len(results)}')
for i, r in enumerate(results):
    print(f'{i+1}. {r.get(\"title\", \"N/A\")} - score: {r.get(\"score\", 0):.3f}')
    print(f'   內容長度: {len(r.get(\"content\", \"\"))} 字元')
"
```

**預期結果**：
- 結果數量 >= 3
- CrystalDiskMark 5 排在前 3 名
- 內容長度 > 500 字元

### 測試 2：驗證視窗擴展

```bash
docker exec ai-django python -c "
# 測試視窗擴展功能
from library.common.knowledge_base.section_search_service import SectionSearchService

service = SectionSearchService()
results = service.search_sections_with_context(
    query='crystaldiskmark',
    top_k=3,
    threshold=0.6,
    context_window=2
)

for r in results:
    print(f'標題: {r.get(\"heading_text\")}')
    print(f'內容長度: {len(r.get(\"content\", \"\"))} 字元')
    print('---')
"
```

---

## 📅 實施時間表

| 階段 | 任務 | 預估時間 | 優先級 |
|------|------|---------|--------|
| 1 | 修復 `_get_doc_identifier` | 15 分鐘 | 🔴 高 |
| 2 | 測試 RRF 融合結果 | 10 分鐘 | 🔴 高 |
| 3 | 修改 Model 新增視窗擴展欄位 | 15 分鐘 | 🟡 中 |
| 4 | 執行 Migration | 5 分鐘 | 🟡 中 |
| 5 | 修改 Serializer | 10 分鐘 | 🟡 中 |
| 6 | 修改前端 UI（Threshold 設定頁）| 45 分鐘 | 🟡 中 |
| 7 | 整合視窗擴展到搜尋服務 | 30 分鐘 | 🟡 中 |
| 8 | 統一結果格式（可選）| 45 分鐘 | 🟢 低 |
| 9 | 完整回歸測試 | 30 分鐘 | 🔴 高 |

**總預估時間**：3-4 小時

---

## 📁 相關檔案清單

| 檔案路徑 | 修改類型 | 說明 |
|----------|---------|------|
| `/library/protocol_guide/search_service.py` | 修改 | 修復 `_get_doc_identifier`、整合視窗擴展 |
| `/library/common/knowledge_base/base_search_service.py` | 可選修改 | 統一結果格式 |
| `/library/common/knowledge_base/section_search_service.py` | 參考 | 已有 context_window 功能 |
| `/backend/api/models.py` | 修改 | 新增視窗擴展欄位到 SearchThresholdSetting |
| `/backend/api/serializers.py` | 修改 | 新增視窗擴展欄位序列化 |
| `/frontend/src/pages/admin/ThresholdSettingsPage.js` | 修改 | 新增視窗擴展 UI 控制項 |

---

## 📌 後續建議

1. **監控搜尋品質**：添加日誌記錄 RRF 融合前後的結果數量
2. **A/B 測試**：建立新版本配置進行效果對比
3. **用戶回饋收集**：追蹤修復後的用戶滿意度
4. **文檔更新**：更新開發文檔，說明正確的結果格式

---

## 🔄 修復 4：視窗擴展功能整合到 Threshold 設定管理（新增）

### 📋 現有視窗擴展功能分析

#### 已實現的功能
`SectionSearchService` 已有完整的 `search_with_context()` 方法：

```python
# 檔案：/library/common/knowledge_base/section_search_service.py

def search_with_context(
    self,
    query: str,
    source_table: str,
    limit: int = 3,
    threshold: float = 0.7,
    include_siblings: bool = False,      # 👈 參數 1
    context_window: int = 1,             # 👈 參數 2
    context_mode: str = 'hierarchical'   # 固定使用層級模式
) -> List[Dict[str, Any]]:
```

#### 可配置參數（3 個）

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `context_window` | int | 0 | 視窗大小（0=不擴展，1-5=前後各擴展 N 個段落）|
| `include_siblings` | bool | False | 是否包含兄弟段落（同層級的其他段落）|
| `context_mode` | str | 'hierarchical' | 上下文模式（層級/線性/兩者）|

#### context_mode 選項說明

| 模式 | 值 | 說明 | 返回的上下文 |
|------|------|------|-------------|
| 層級結構 | `hierarchical` | 獲取父子段落關係（預設）| `parent`, `children`, `siblings`(可選) |
| 線性視窗 | `adjacent` | 獲取前後相鄰段落 | `previous`, `next` |
| 兩者兼具 | `both` | 同時獲取層級和線性上下文 | 全部欄位 |

**視覺化說明**：
```
文檔段落: [2.1] → [2.2] → [3.1] → [3.2] → [3.3] → [4.1]
                                    ↑
                              🎯 搜尋命中 3.2

📂 hierarchical（層級結構）:
   返回: parent=3, children=[3.2.1, 3.2.2], siblings=[3.1, 3.3]
   適用: Protocol 文檔（結構化清晰）

📏 adjacent（線性視窗）:
   返回: previous=[3.1], next=[3.3]（根據 context_window 大小）
   適用: 連續性內容、前後文關聯強

📦 both（兩者兼具）:
   返回: 以上全部
   適用: 需要完整上下文的複雜查詢
```

---

### 🗄️ 資料庫修改：擴展 SearchThresholdSetting Model

**檔案**：`/backend/api/models.py`

**新增欄位**（3 個）：

```python
class SearchThresholdSetting(models.Model):
    # ... 現有欄位（stage1/stage2 的 threshold 和權重）...
    
    # === 🆕 視窗擴展配置（新增） ===
    context_window = models.IntegerField(
        default=0,
        verbose_name="視窗擴展大小",
        help_text="搜尋時前後各擴展幾個段落（0=不擴展，1-5）"
    )
    
    include_siblings = models.BooleanField(
        default=False,
        verbose_name="包含兄弟段落",
        help_text="是否包含同層級的兄弟段落"
    )
    
    context_mode = models.CharField(
        max_length=20,
        default='hierarchical',
        choices=[
            ('hierarchical', '層級結構'),
            ('adjacent', '線性視窗'),
            ('both', '兩者兼具'),
        ],
        verbose_name="上下文模式",
        help_text="hierarchical=父子段落, adjacent=前後段落, both=全部"
    )
```

**Migration 命令**：
```bash
docker exec ai-django python manage.py makemigrations api
docker exec ai-django python manage.py migrate
```

---

### 📊 Serializer 修改

**檔案**：`/backend/api/serializers.py`

```python
class SearchThresholdSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchThresholdSetting
        fields = [
            'id', 'assistant_type', 'assistant_type_display',
            # 現有欄位
            'master_threshold', 
            'stage1_title_weight', 'stage1_content_weight', 'stage1_threshold',
            'stage2_title_weight', 'stage2_content_weight', 'stage2_threshold',
            # 🆕 視窗擴展欄位（新增）
            'context_window', 
            'include_siblings',
            'context_mode',
            # 其他
            'use_unified_weights', 'description', 'is_active',
            'created_at', 'updated_at'
        ]
```

---

### 🎨 前端 UI 修改

#### 1️⃣ **列表頁面**：視窗擴展欄位放在「二階設定（進階）」右邊

**檔案**：`/frontend/src/pages/admin/ThresholdSettingsPage.js`

**表格欄位結構**（修改後）：

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                   ☆ 一階設定（常用）          │  二階設定（進階）   │  視窗擴展設定                    │ 操作 │
│ ────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ Assistant  段落向量    標題    內容          │ 段落向量  標題  內容│ 視窗大小  兄弟段落  上下文模式   │      │
│           Threshold   權重    權重           │ Threshold 權重  權重│                                  │      │
│ ────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ Protocol   70%        90%     10%            │   80%     20%   80% │    2        ☑       層級結構     │ 編輯 │
│ Assistant                                    │                     │                                  │      │
│ ────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ RVT        80%        70%     30%            │   80%     90%   10% │    1        ☐       線性視窗     │ 編輯 │
│ Assistant                                    │                     │                                  │      │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**新增欄位定義**：

```javascript
// unifiedColumns 新增第 4 組 grouped header
{
  title: (
    <span style={{ color: '#52c41a', fontWeight: 'bold' }}>視窗擴展設定</span>
  ),
  className: 'context-header',
  children: [
    {
      title: (
        <Space>
          視窗大小
          <Tooltip title="搜尋時前後各擴展幾個段落（0=不擴展）">
            <InfoCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'context_window',
      key: 'context_window',
      width: 100,
      render: (value) => (
        <Text style={{ fontSize: '14px', color: '#52c41a' }}>
          {value === 0 ? '不擴展' : `±${value}`}
        </Text>
      )
    },
    {
      title: (
        <Space>
          兄弟段落
          <Tooltip title="是否包含同層級的兄弟段落">
            <InfoCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'include_siblings',
      key: 'include_siblings',
      width: 90,
      render: (value) => (
        value ? <Tag color="green">啟用</Tag> : <Tag color="default">停用</Tag>
      )
    },
    {
      title: (
        <Space>
          上下文模式
          <Tooltip title="hierarchical=層級結構, adjacent=線性視窗, both=兩者兼具">
            <InfoCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'context_mode',
      key: 'context_mode',
      width: 110,
      render: (value) => {
        const modeMap = {
          'hierarchical': { text: '層級結構', color: 'blue' },
          'adjacent': { text: '線性視窗', color: 'orange' },
          'both': { text: '兩者兼具', color: 'purple' }
        };
        const mode = modeMap[value] || { text: value, color: 'default' };
        return <Tag color={mode.color}>{mode.text}</Tag>;
      }
    }
  ]
}
```

---

#### 2️⃣ **編輯 Modal**：視窗擴展設定放在「二階設定（進階）」Card 下方

**位置**：在現有的「二階設定」Card 的 `<Alert>` 後面，`</Card>` 之前新增 `<Divider>` 和「視窗擴展設定」Card

**UI 草圖**：

```
┌─────────────────────────────────────────────────────────────────────┐
│ 編輯 Protocol Assistant 搜尋參數                               ✕   │
├─────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ ℹ️ 設定說明                                                      │ │
│ │ 設定一階（常用）和二階（進階）搜尋參數...                        │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ ☆ 一階設定（常用）                                               │ │
│ │ ... (現有內容不變)                                               │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 二階設定（進階）                                                 │ │
│ │ ... (現有內容不變)                                               │ │
│ │ 💡 提示：標題權重 + 內容權重 = 100%                               │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 🔍 視窗擴展設定（新增）                                          │ │
│ │ ─────────────────────────────────────────────────────────────── │ │
│ │ * 視窗擴展大小 ⓘ                                                 │ │
│ │ ├────────────●────────────────────────────┤                      │ │
│ │ 0            2                            5                      │ │
│ │ (不擴展)   (前後各2段)                 (前後各5段)               │ │
│ │                                                                  │ │
│ │ * 上下文模式 ⓘ                                                   │ │
│ │ ┌──────────────────────────────────────────────────────────────┐ │ │
│ │ │ ○ 層級結構 - 獲取父子段落關係（適合結構化文檔）               │ │ │
│ │ │ ○ 線性視窗 - 獲取前後相鄰段落（適合連續性內容）               │ │ │
│ │ │ ○ 兩者兼具 - 同時獲取層級和線性上下文                         │ │ │
│ │ └──────────────────────────────────────────────────────────────┘ │ │
│ │                                                                  │ │
│ │ ☑ 包含兄弟段落 ⓘ                                                 │ │
│ │   搜尋結果會包含同層級的其他段落                                 │ │
│ │                                                                  │ │
│ │ 💡 提示：視窗擴展可增加返回內容的上下文完整性                     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│                                          [ 取消 ]  [ 儲存 ]         │
└─────────────────────────────────────────────────────────────────────┘
```

**需要 import 的新組件**：

```javascript
import { Checkbox, Radio } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
```

**新增 Form 欄位**（放在二階設定 Card 後面）：

```javascript
{/* 視窗擴展設定（新增 Card） */}
<Divider />

<Card 
  title={
    <Space>
      <SearchOutlined style={{ color: '#52c41a' }} />
      <span>視窗擴展設定</span>
    </Space>
  }
  size="small"
>
  {/* 視窗大小 */}
  <Form.Item
    label={
      <Space>
        <span>視窗擴展大小</span>
        <Tooltip title="搜尋時前後各擴展幾個段落。0=不擴展，數字越大返回的上下文越多。">
          <InfoCircleOutlined />
        </Tooltip>
      </Space>
    }
    name="context_window"
    rules={[{ required: true, message: '請設定視窗大小' }]}
  >
    <Slider
      min={0}
      max={5}
      step={1}
      marks={{
        0: '0 (不擴展)',
        1: '±1',
        2: '±2',
        3: '±3',
        5: '±5'
      }}
      tooltip={{
        formatter: (value) => value === 0 ? '不擴展' : `前後各 ${value} 個段落`
      }}
    />
  </Form.Item>

  {/* 上下文模式 */}
  <Form.Item
    label={
      <Space>
        <span>上下文模式</span>
        <Tooltip title="決定如何獲取搜尋結果的上下文內容">
          <InfoCircleOutlined />
        </Tooltip>
      </Space>
    }
    name="context_mode"
    rules={[{ required: true, message: '請選擇上下文模式' }]}
  >
    <Radio.Group>
      <Space direction="vertical">
        <Radio value="hierarchical">
          <Space>
            <Tag color="blue">層級結構</Tag>
            <Text type="secondary">獲取父子段落關係（適合結構化文檔）</Text>
          </Space>
        </Radio>
        <Radio value="adjacent">
          <Space>
            <Tag color="orange">線性視窗</Tag>
            <Text type="secondary">獲取前後相鄰段落（適合連續性內容）</Text>
          </Space>
        </Radio>
        <Radio value="both">
          <Space>
            <Tag color="purple">兩者兼具</Tag>
            <Text type="secondary">同時獲取層級和線性上下文</Text>
          </Space>
        </Radio>
      </Space>
    </Radio.Group>
  </Form.Item>

  {/* 包含兄弟段落 */}
  <Form.Item
    name="include_siblings"
    valuePropName="checked"
  >
    <Checkbox>
      <Space>
        包含兄弟段落
        <Tooltip title="啟用後，搜尋結果會包含同層級（相同父段落）的其他段落">
          <InfoCircleOutlined />
        </Tooltip>
      </Space>
    </Checkbox>
  </Form.Item>

  <Alert
    message="💡 提示：視窗擴展可增加返回內容的上下文完整性，但會增加處理時間"
    type="info"
    showIcon
  />
</Card>
```

---

#### 3️⃣ **handleEdit 和 handleSave 修改**

```javascript
// handleEdit - 載入視窗擴展設定
const handleEdit = (record) => {
  setEditingRecord(record);
  form.setFieldsValue({
    // 現有欄位
    stage1_threshold: parseFloat(record.stage1_threshold) * 100,
    stage1_title_weight: record.stage1_title_weight,
    stage1_content_weight: record.stage1_content_weight,
    stage2_threshold: parseFloat(record.stage2_threshold) * 100,
    stage2_title_weight: record.stage2_title_weight,
    stage2_content_weight: record.stage2_content_weight,
    // 🆕 視窗擴展欄位（3 個）
    context_window: record.context_window || 0,
    include_siblings: record.include_siblings || false,
    context_mode: record.context_mode || 'hierarchical'
  });
  setEditModalVisible(true);
};

// handleSave - 儲存視窗擴展設定
const handleSave = async () => {
  try {
    const values = await form.validateFields();

    setLoading(true);
    await axios.patch(`/api/search-threshold-settings/${editingRecord.assistant_type}/`, {
      // 現有欄位
      stage1_threshold: (values.stage1_threshold / 100).toFixed(2),
      stage1_title_weight: values.stage1_title_weight,
      stage1_content_weight: values.stage1_content_weight,
      stage2_threshold: (values.stage2_threshold / 100).toFixed(2),
      stage2_title_weight: values.stage2_title_weight,
      stage2_content_weight: values.stage2_content_weight,
      // 🆕 視窗擴展欄位（3 個）
      context_window: values.context_window,
      include_siblings: values.include_siblings,
      context_mode: values.context_mode
    }, { withCredentials: true });

    message.success('設定更新成功！');
    // ...
  }
};
```

---

### 🔧 後端修改：整合視窗擴展到搜尋流程

**檔案**：`/library/protocol_guide/search_service.py`

**修改 `_vector_search` 方法**：

```python
def _vector_search(self, query: str, stage: int = 1, settings: Dict = None) -> List[Dict]:
    """執行向量搜尋（支援視窗擴展）"""
    
    # 1. 獲取配置
    threshold_settings = self._get_threshold_settings()
    
    # 2. 讀取視窗擴展配置（3 個參數）
    context_window = getattr(threshold_settings, 'context_window', 0)
    include_siblings = getattr(threshold_settings, 'include_siblings', False)
    context_mode = getattr(threshold_settings, 'context_mode', 'hierarchical')
    
    # 3. 判斷是否啟用視窗擴展
    if context_window > 0:
        # ✅ 使用視窗擴展搜尋
        self.logger.info(
            f"🔍 啟用視窗擴展: window={context_window}, "
            f"siblings={include_siblings}, mode={context_mode}"
        )
        section_results = self.section_search_service.search_with_context(
            query=query,
            source_table=self.source_table,
            limit=stage1_top_k,
            threshold=adjusted_threshold,
            context_window=context_window,
            include_siblings=include_siblings,
            context_mode=context_mode  # 🆕 使用配置的模式
        )
    else:
        # 標準搜尋（無視窗擴展）
        section_results = self.section_search_service.search_sections(
            query=query,
            source_table=self.source_table,
            limit=stage1_top_k,
            threshold=adjusted_threshold
        )
    
    return section_results
```

---

### 📅 實施步驟

| 步驟 | 任務 | 預估時間 | 依賴 |
|------|------|---------|------|
| 1 | Model 新增 3 個欄位 | 10 分鐘 | 無 |
| 2 | 執行 Migration | 5 分鐘 | 步驟 1 |
| 3 | 修改 Serializer | 5 分鐘 | 步驟 2 |
| 4 | 前端：列表頁新增 3 個欄位 | 25 分鐘 | 步驟 3 |
| 5 | 前端：編輯 Modal 新增表單（含 Radio Group）| 35 分鐘 | 步驟 3 |
| 6 | 後端：搜尋服務整合 | 20 分鐘 | 步驟 2 |
| 7 | 測試驗證 | 20 分鐘 | 步驟 6 |

**總預估時間**：約 2 小時

---

### ✅ 預期效果

| 設定 | context_window | include_siblings | context_mode | 預期結果 |
|------|---------------|-----------------|--------------|---------|
| 預設 | 0 | ☐ | hierarchical | 只返回匹配的段落（38 字元）|
| 啟用 | 2 | ☐ | hierarchical | 返回匹配段落 + 父/子段落 |
| 啟用 | 2 | ☑ | hierarchical | 返回匹配段落 + 父/子/兄弟段落 |
| 啟用 | 2 | ☐ | adjacent | 返回匹配段落 + 前後各 2 個段落 |
| 啟用 | 2 | ☑ | both | 返回全部上下文（最完整）|

**CrystalDiskMark 查詢範例**：

```
設定：context_window=2, include_siblings=false, context_mode='hierarchical'

搜尋 "CrystalDiskMark" → 返回:
├── CrystalDiskMark 5（標題）
│   ├── 1.Test Platform（子段落）
│   ├── 2.Test Report（子段落）
│   └── 3.Test Checklist（子段落）
  
總內容：~1500+ 字元 ✅
```

```
設定：context_window=2, include_siblings=false, context_mode='adjacent'

搜尋 "CrystalDiskMark" → 返回:
├── 前 2 個段落
├── CrystalDiskMark 5（匹配段落）
└── 後 2 個段落
  
適用：文檔連續性強的情況
```

---

### 🎯 建議預設配置值

| Assistant | context_window | include_siblings | context_mode | 說明 |
|-----------|---------------|-----------------|--------------|------|
| Protocol Assistant | 2 | ☐ | hierarchical | 文檔結構清晰，展開子段落即可 |
| RVT Assistant | 1 | ☑ | adjacent | 內容連貫，需要前後文脈絡 |

---

**文件撰寫人**：AI Assistant  
**審核狀態**：待審核  
**下一步行動**：待用戶確認後開始實施修復
