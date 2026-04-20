# 搜尋 Threshold 設定頁面說明

## 頁面位置

管理後台 → 搜尋 Threshold 設定（Beta）

**前端元件**：[`frontend/src/pages/admin/ThresholdSettingsPage.js`](../../frontend/src/pages/admin/ThresholdSettingsPage.js)  
**後端 API**：`GET/PATCH /api/search-threshold-settings/{assistant_type}/`  
**資料模型**：`SearchThresholdSetting`（`backend/api/models.py`）  
**ViewSet**：[`backend/api/views/viewsets/threshold_viewsets.py`](../../backend/api/views/viewsets/threshold_viewsets.py)

---

## 頁面用途

統一管理 **Protocol Assistant** 與 **RVT Assistant** 的向量搜尋參數，包含：

- 一階（常用）搜尋的相似度門檻與向量融合權重
- 二階（進階）搜尋的相似度門檻與向量融合權重
- 搜尋結果的 Context Window 擴展行為

設定儲存於資料庫，透過 `ThresholdManager`（Singleton）讀取並快取，每 5 分鐘自動更新。

---

## 表格欄位說明

### 一階設定（常用）
> 用於**段落級別**的語義搜尋（Stage 1），適合精準查詢。

| 欄位 | 說明 |
|------|------|
| **段落向量 Threshold** | 一階段落向量搜尋的相似度閾值（0–100%）。結果的餘弦相似度必須 ≥ 此值才會被納入。值越高，結果越精準但數量越少。 |
| **標題權重** | 一階搜尋中，**標題向量**在多向量融合時的佔比（0–100%）。 |
| **內容權重** | 一階搜尋中，**內容向量**在多向量融合時的佔比（0–100%）。標題 + 內容 = 100%。 |
| **RRF K 值** | Reciprocal Rank Fusion 融合常數（建議範圍 30–120，業界標準 60）。控制向量搜尋與關鍵字搜尋合併時排名的平滑程度：K 值越小，排名靠前的結果權重更集中；K 值越大，結果分布越平均（適合探索性查詢）。詳見下方「[RRF K 值詳細說明](#rrf-k-值詳細說明)」。 |

### 二階設定（進階）
> 用於**全文級別**的深度搜尋（Stage 2），在一階結果不足時觸發，適合探索性查詢。

| 欄位 | 說明 |
|------|------|
| **段落向量 Threshold** | 二階全文向量搜尋的相似度閾值（建議比一階低，讓更多結果通過）。 |
| **標題權重** | 二階搜尋中，標題向量的融合佔比。 |
| **內容權重** | 二階搜尋中，內容向量的融合佔比。 |

### Window 擴展
> 控制搜尋結果是否自動擴展到周邊段落，提供更完整的上下文。

| 欄位 | 說明 |
|------|------|
| **擴展範圍** | 找到目標段落後，向上下各擴展幾個段落（`0` = 關閉，`±1` 表示各擴展 1 個）。 |
| **擴展模式** | **層級**（`hierarchical`）：同一父節點下的段落；**線性**（`adjacent`）：前後相鄰段落；**兩者**（`both`）：同時使用兩種方式。 |
| **包含同層** | 是否一併納入同一父節點下的兄弟段落（`是` / `否`）。 |

---

## RRF K 值詳細說明

### 什麼是 RRF？

一階搜尋採用**混合搜尋**模式，同時執行兩種搜尋再合併：

```
┌─────────────────┐     ┌─────────────────┐
│   向量搜尋       │     │   關鍵字搜尋     │
│  （語義理解）    │     │  （精確匹配）    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
            ┌─────────────────┐
            │  RRF 融合        │
            │  （K 值參數）    │
            └────────┬────────┘
                     ▼
              最終排序結果
```

**RRF（Reciprocal Rank Fusion）** 的核心公式：

$$\text{RRF\_score}(d) = \sum \frac{1}{K + \text{rank}(d)}$$

- $K$：融合常數（此頁面設定的 RRF K 值）
- $\text{rank}(d)$：文件 $d$ 在各搜尋結果中的排名（從 1 開始）

各搜尋方式的分數加總後，分數越高的文件排名越前。

---

### K 值如何影響結果？

K 值的作用是「平滑化」排名差距：

| K 值範圍 | 效果 | 適用場景 |
|----------|------|---------|
| **30–50（小）** | 排名差異被放大，**排名靠前的結果更突出** | 精確查詢，需要最佳答案 |
| **60（標準）** | 排名差異適中，兼顧精準與多樣性 | 通用場景（預設值） |
| **80–120（大）** | 排名差異被平滑，**結果分布更平均** | 探索性查詢，需要多樣結果 |

---

### 實際數值範例

假設向量搜尋和關鍵字搜尋各自返回結果，文件 A 在向量搜尋排名第 1、在關鍵字搜尋排名第 5：

**K = 30 時：**

$$\frac{1}{30+1} + \frac{1}{30+5} = 0.0323 + 0.0286 = \mathbf{0.0609}$$

**K = 60 時：**

$$\frac{1}{60+1} + \frac{1}{60+5} = 0.0164 + 0.0154 = \mathbf{0.0318}$$

**K = 120 時：**

$$\frac{1}{120+1} + \frac{1}{120+5} = 0.0083 + 0.0077 = \mathbf{0.0160}$$

K 值越大，各文件的 RRF 分數整體越低且越接近，排名靠前的優勢變小，讓中後段結果也有機會出現。

---

### 調整建議

- 若使用者提問精確（如「IOL 密碼」、「CrystalDiskMark 安裝步驟」），**K 值調小（30–50）** 讓最相關的結果更突出。
- 若使用者提問模糊（如「介紹一下這個工具」），**K 值調大（80–120）** 增加結果多樣性。
- 不確定時保持預設值 **60** 即可，這是業界公認的穩定值。

---

## 目前預設值

| Assistant | 一階 Threshold | 一階標題/內容 | RRF K | 二階 Threshold | 二階標題/內容 | Window 範圍 | 擴展模式 | 包含同層 |
|-----------|---------------|--------------|-------|---------------|--------------|------------|---------|---------|
| Protocol Assistant | 85% | 25% / 75% | 60 | 85% | 10% / 90% | ±1 | 兩者 | 是 |
| RVT Assistant | 85% | 70% / 30% | 60 | 85% | 90% / 10% | 關閉 | 層級 | 否 |

---

## 如何編輯設定

1. 點擊對應 Assistant 列右側的「**編輯**」按鈕，開啟編輯 Modal。
2. Modal 分三個區塊：
   - **一階設定**：調整 Threshold（Slider，0–100%）、標題 / 內容權重（Slider，總和須為 100%）、RRF K 值（Slider，30–120）。
   - **二階設定**：調整 Threshold 與標題 / 內容權重。
   - **Window 擴展設定**：選擇擴展範圍、模式、是否包含兄弟段落。
3. 點擊「**儲存**」，後端透過 `PATCH /api/search-threshold-settings/{assistant_type}/` 更新，並立即重整 ThresholdManager 快取。
4. 頁面自動刷新顯示最新值。

---

## Threshold 三層優先順序

```
Dify Studio 設定（最高，即時生效）
         ↓（若無）
資料庫設定（此頁面管理，預設值）
         ↓（若無）
程式碼預設值 0.7
```

ThresholdManager（Singleton）以 5 分鐘為週期快取資料庫設定。若需立即套用，可點擊右上角「**重新整理**」按鈕強制重整快取。

---

## 相關檔案

| 職責 | 檔案路徑 |
|------|---------|
| 前端頁面 | `frontend/src/pages/admin/ThresholdSettingsPage.js` |
| 後端 ViewSet（主要） | `backend/api/views/viewsets/threshold_viewsets.py` |
| 後端 ViewSet（舊版） | `backend/api/views/viewsets/system_viewsets.py` |
| 資料模型 | `backend/api/models.py`（`SearchThresholdSetting`） |
| Threshold 管理器 | `library/common/threshold_manager.py` |
| 初始化腳本 | `backend/init_threshold_settings.py` |
| DB Table | `search_threshold_settings` |

---

## API 端點

| 方法 | 路徑 | 說明 | 權限 |
|------|------|------|------|
| `GET` | `/api/search-threshold-settings/` | 取得所有 Assistant 設定列表 | 管理員 |
| `GET` | `/api/search-threshold-settings/{assistant_type}/` | 取得特定 Assistant 設定 | 管理員 |
| `PATCH` | `/api/search-threshold-settings/{assistant_type}/` | 更新設定 | 管理員 |
| `GET` | `/api/threshold-settings/` | 另一版 ViewSet（列表） | 已認證用戶可讀 |
| `POST` | `/api/threshold-settings/refresh-cache/` | 手動重整快取 | 管理員 |
| `GET` | `/api/threshold-settings/get-cache-info/` | 查詢快取狀態 | 已認證用戶 |
