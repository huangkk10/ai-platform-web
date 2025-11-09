# 🚀 上下文視窗功能完整實作計畫

**專案名稱**: 搜尋版本切換功能（V1 基礎搜尋 vs V2 上下文增強）  
**實作日期**: 2025-11-09  
**預計完成**: 2-3 天  
**適用範圍**: RVT Assistant, Protocol Assistant  
**實作方式**: 樣式 1 - 頂部 Toggle Bar

---

## 📋 目錄

1. [專案概述](#1-專案概述)
2. [Phase 0: 環境準備](#phase-0-環境準備)
3. [Phase 1: 後端核心功能](#phase-1-後端核心功能)
4. [Phase 2: 前端 UI 實作](#phase-2-前端-ui-實作)
5. [Phase 3: 測試與驗證](#phase-3-測試與驗證)
6. [Phase 4: 部署與監控](#phase-4-部署與監控)
7. [附錄：故障排除](#附錄故障排除)

---

## 1. 專案概述

### 🎯 目標

實作一個簡單的版本切換功能，讓用戶可以在聊天介面中自由切換：
- **V1 (基礎搜尋)**: 現有的段落向量搜尋
- **V2 (上下文增強)**: 包含前後段落和父子段落的完整上下文搜尋

### 📐 最終效果

```
┌──────────────────────────────────────────────────────────┐
│ RVT Assistant                    🔄 [V1] ⚫ [V2]         │ ← Toggle Bar
├──────────────────────────────────────────────────────────┤
│  [搜尋輸入框]                                            │
│                                                          │
│  👤 User: 請說明軟體配置流程                            │
│                                                          │
│  🤖 Assistant  [V2: 上下文增強] ⏱️ 85ms                │
│  📍 主要結果: 3.2 軟體配置...                           │
│  ⬆️ 前置段落 (1) ⬇️ 後續段落 (1)                       │
└──────────────────────────────────────────────────────────┘
```

### 🎯 成功標準

- ✅ 用戶可以輕鬆切換 V1/V2
- ✅ V1 回應時間 < 100ms
- ✅ V2 回應時間 < 200ms
- ✅ V2 正確顯示上下文段落
- ✅ 無 Console 錯誤

### 📊 實作範圍

| 項目 | 現狀 | 目標 | 優先級 |
|------|------|------|--------|
| **後端 API** | 僅 V1 | 支援 V1/V2 切換 | 🔴 P0 |
| **前端 Hook** | 無版本狀態 | 添加版本切換邏輯 | 🔴 P0 |
| **前端 UI** | 無切換控制 | Toggle Bar + 版本標記 | 🔴 P0 |
| **RVT Assistant** | 僅 V1 | V1/V2 完整支援 | 🔴 P0 |
| **Protocol Assistant** | 僅 V1 | V1/V2 完整支援 | 🟡 P1 |
| **使用統計** | 無 | 簡單計數（可選） | 🟢 P2 |

---

## Phase 0: 環境準備

### ⏱️ 預計時間：30 分鐘

### 0.1 檢查現有功能

```bash
# 1. 確認 V1 搜尋功能正常
docker exec ai-django python manage.py shell

# 在 Django shell 中測試
from library.common.knowledge_base.section_search_service import SectionSearchService
search_service = SectionSearchService()

# 測試 V1 搜尋
results = search_service.search_sections(
    query="軟體配置",
    source_table='rvt_guide',
    limit=5,
    threshold=0.7
)
print(f"✅ V1 搜尋結果: {len(results)} 筆")
```

### 0.2 確認 V2 方法是否存在

```bash
# 檢查是否已實作 search_sections_with_expanded_context
docker exec ai-django python manage.py shell

from library.common.knowledge_base.section_search_service import SectionSearchService
import inspect

search_service = SectionSearchService()
methods = [m for m in dir(search_service) if not m.startswith('_')]
print("可用方法:", methods)

# 確認是否有 search_sections_with_expanded_context
if 'search_sections_with_expanded_context' in methods:
    print("✅ V2 方法已存在")
else:
    print("❌ V2 方法尚未實作，需要先實作")
```

### 0.3 創建功能分支

```bash
# 切換到開發分支
cd /home/user/codes/ai-platform-web
git checkout context_window  # 或創建新分支
git pull origin context_window

# 創建功能分支
git checkout -b feature/search-version-toggle
```

### ✅ 檢查點

- [ ] V1 搜尋功能正常
- [ ] 確認 V2 方法狀態（存在/需實作）
- [ ] Git 分支已創建
- [ ] Docker 容器運行正常

---

## Phase 1: 後端核心功能

### ⏱️ 預計時間：2-3 小時

### 1.1 修改 API 端點（RVT Assistant）

**檔案**: `backend/api/views/viewsets/knowledge_viewsets.py`

#### 步驟 1.1.1：找到 RVTGuideViewSet

```bash
# 查看現有實作
cat backend/api/views/viewsets/knowledge_viewsets.py | grep -A 20 "class RVTGuideViewSet"
```

#### 步驟 1.1.2：修改 search_sections API

<function_calls>
<invoke name="read_file">
<parameter name="filePath">/home/user/codes/ai-platform-web/backend/api/views/viewsets/knowledge_viewsets.py