# 📚 AI Platform 文檔索引 - AI 助手專用指引

## 🤖 **給 AI 助手的重要說明**

當用戶詢問 AI Platform 相關問題時，請根據問題類型參考以下文檔：

---

## 📋 **問題分類與對應文檔**

### 🔄 **定時任務與 Celery Beat 相關**
**常見問題**：
- "聚類什麼時候執行？"
- "向量資料多久更新一次？"
- "為什麼定時任務沒有執行？"
- "Celery Beat 是怎麼運作的？"

**參考文檔**：
1. **🎯 主要參考**: `/docs/celery-beat-architecture-guide.md`
2. **AI 指導**: `/docs/ai-guidance-vector-architecture.md`
3. **快速參考**: `/docs/vector-update-quick-reference.md`

**核心回答要點**：
- 聚類分析：**每天凌晨 3:30** 執行
- 向量化：用戶問題每小時，助手回覆每6小時
- 架構：Beat(排程) + Worker(執行) + Redis(佇列)

### 🎯 **向量搜尋與向量資料庫**
**常見問題**：
- "向量搜尋如何工作？"
- "為什麼搜尋結果不準確？"
- "如何提升向量搜尋效果？"
- "向量維度是多少？"

**參考文檔**：
1. **🎯 主要參考**: `/docs/vector-search-guide.md`
2. **AI 指導**: `/docs/ai-vector-search-guide.md`
3. **技術概覽**: `/docs/vector-search-overview.md`
4. **升級記錄**: `/docs/vector-upgrade-1024-summary.md`

**核心回答要點**：
- 模型：intfloat/multilingual-e5-large (1024維)
- 資料表：`chat_message_embeddings_1024`
- 相似度：餘弦相似度，閾值 0.7-0.8

### 🏗️ **代碼重構與架構設計**
**常見問題**：
- "RVT Guide 如何重構的？"
- "Library First 原則是什麼？"
- "如何減少 views.py 的代碼？"

**參考文檔**：
1. **🎯 主要參考**: `/docs/rvt-guide-refactoring-report.md`
2. **UI 規範**: `/docs/ui-component-guidelines.md`

**核心回答要點**：
- 代碼減少 77% (335行 → 77行)
- 模組化架構：API處理器 + ViewSet管理器 + 服務層
- 向後兼容，功能完整

### 🤖 **AI 整合與 Dify 配置**
**常見問題**：
- "如何配置 Dify 整合？"
- "外部知識庫如何設置？"
- "AI 聊天 API 如何使用？"

**參考文檔**：
1. **配置指南**: `/docs/guide/dify-external-knowledge-api-guide.md`
2. **設置說明**: `/docs/guide/dify-app-config-usage.md`
3. **API 整合**: `/docs/guide/api-integration.md`

### 📊 **RVT Assistant 分析報告系統** ⭐ **NEW**
**常見問題**：
- "熱門問題排名如何計算？"
- "為什麼統計數據不準確？"  
- "UCC/特定問題沒有出現在排名中？"
- "什麼是智慧分析模式？"
- "分析模式有哪些？如何選擇？"

**參考文檔**：
1. **🎯 完整架構**: `/docs/rvt-analytics-system-architecture.md` ⭐ **主要參考**
2. **🤖 AI 快速參考**: `/docs/ai-rvt-analytics-quick-reference.md` ⭐ **診斷必備**
3. **🔄 流程圖解**: `/docs/rvt-analytics-workflow-diagrams.md`
4. **向量架構**: `/docs/ai-guidance-vector-architecture.md`
5. **定時任務**: `/docs/vector-database-scheduled-update-architecture.md`

**核心回答要點**：
- **三種分析模式**：聚類(`clustered`) / 頻率(`frequency`) / **智慧(`smart`)** ⭐ 推薦
- **智慧分析**：自動檢測聚類問題並選擇最佳模式
- **數據更新頻率**：向量化每小時，統計每日凌晨 3:30
- **常見問題**：聚類掩蓋高頻問題 → 使用智慧模式自動修正
- **快速診斷**：檢查 mode=smart 參數，確認定時任務運行

### 🎨 **前端開發與 UI 規範**
**常見問題**：
- "應該使用哪個 UI 框架？"
- "如何統一前端風格？"
- "組件庫標準是什麼？"

**參考文檔**：
1. **🎯 主要參考**: `/docs/ui-component-guidelines.md`
2. **前端指南**: `/docs/guide/frontend-development.md`

**核心回答要點**：
- **強制使用 Ant Design** 作為唯一 UI 框架
- 禁止混用其他 UI 庫 (Bootstrap, Material-UI 等)
- 參考範例：RvtGuidePage.js, KnowIssuePage.js

### 🐳 **Docker 與部署**
**常見問題**：
- "如何部署系統？"
- "Docker 配置說明？"
- "容器間如何通信？"

**參考文檔**：
1. **Docker 指南**: `/docs/guide/docker-installation.md`
2. **Celery 架構**: `/docs/celery-beat-architecture-guide.md`

## 🚨 **重要提醒給 AI 助手**

### ❌ **不要建議的做法**
1. **不要建議即時向量化** - 現有定時方案已最佳化
2. **不要建議混用 UI 框架** - 只使用 Ant Design
3. **不要建議修改聊天流程** - 功能穩定，風險高
4. **不要建議複雜架構修改** - 現有架構已驗證有效

### ✅ **推薦的回答方式**
1. **先了解具體問題** - 詢問用戶遇到的具體情況
2. **參考對應文檔** - 根據問題類型找到正確文檔
3. **提供具體指令** - 給出可執行的檢查或修復指令
4. **說明設計原理** - 解釋為什麼採用某種設計

### 📋 **標準回答模板**

#### **向量化相關問題**
```
根據系統設計，AI Platform 採用定時向量化機制：

⏰ **執行時間**：
- 用戶問題：每小時處理
- 助手回覆：每6小時處理  
- 聚類分析：每天凌晨3:30

🏗️ **架構原理**：
系統使用 Celery Beat 容器化架構，詳細說明請參考：
/docs/celery-beat-architecture-guide.md

🔧 **如果有問題**，請檢查：
1. `docker logs ai-celery-beat`
2. `docker logs ai-celery-worker`  
3. 訪問 http://localhost:5555 查看 Flower 監控
```

#### **UI 開發相關問題**
```
AI Platform 統一使用 Ant Design 作為 UI 框架：

✅ **正確做法**：
import { Table, Card, Button } from 'antd';

❌ **禁止做法**：
import { Button } from 'react-bootstrap';  // 禁止
import { TextField } from '@mui/material';  // 禁止

📖 **詳細規範請參考**：
/docs/ui-component-guidelines.md
```

## � **RVT Analytics 問題速查表** ⭐

### **問題類型 → 快速解答**

| 用戶問題 | AI 回答模板 | 參考文檔 |
|----------|-------------|----------|
| "熱門問題沒有更新" | 系統每小時更新向量，每日更新統計。建議使用智慧分析模式(mode=smart)自動選擇最佳分析方式 | ai-rvt-analytics-quick-reference.md |
| "UCC問題沒出現在排名中" | 這是聚類掩蓋問題。智慧分析模式會自動檢測並修正，確保高頻問題正確顯示 | rvt-analytics-system-architecture.md |
| "什麼是智慧分析模式" | 自動檢測聚類演算法是否掩蓋高頻問題，智能選擇聚類或頻率模式，提供最準確的排名 | rvt-analytics-system-architecture.md |
| "分析模式有哪些" | 三種：聚類(發現模式)、頻率(真實排名)、智慧(自動選擇)。推薦使用智慧模式 | ai-rvt-analytics-quick-reference.md |
| "為什麼顯示舊數據" | 檢查前端API是否使用mode=smart，清除瀏覽器快取，或重啟前端容器 | ai-rvt-analytics-quick-reference.md |

### **診斷命令速記**
```bash
# 檢查系統狀態
docker compose ps | grep -E "(celery|react)"

# 手動更新統計  
docker exec ai-django python -c "
from library.rvt_analytics.tasks import precompute_question_classifications
print(precompute_question_classifications())
"

# 測試智慧分析
docker exec ai-django python -c "
from library.rvt_analytics.api_handlers import RVTAnalyticsAPIHandler
# [測試代碼見快速參考文檔]
"
```

---

## �📈 **文檔更新日期**

| 文檔 | 最後更新 | 狀態 |
|------|----------|------|
| **rvt-analytics-system-architecture.md** | **2025-10-13** | **✅ 新增** |
| **ai-rvt-analytics-quick-reference.md** | **2025-10-13** | **✅ 新增** |
| **rvt-analytics-workflow-diagrams.md** | **2025-10-13** | **✅ 新增** |
| celery-beat-architecture-guide.md | 2025-10-09 | ✅ 最新 |
| ai-guidance-vector-architecture.md | 2025-10-09 | ✅ 最新 |
| rvt-guide-refactoring-report.md | 2025-10-07 | ✅ 最新 |
| ui-component-guidelines.md | 2025-09-24 | ✅ 最新 |

---

**給 AI 助手的最後提醒**：
- 📖 務必先查閱相關文檔再回答
- 🎯 根據問題類型選擇正確的參考文檔  
- 💡 優先推薦已驗證的解決方案
- 🚨 避免建議可能破壞系統穩定性的修改

**維護責任**: AI Platform Development Team  
**更新頻率**: 隨系統更新同步維護