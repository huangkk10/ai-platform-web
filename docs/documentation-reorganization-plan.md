# 📚 AI Platform 文檔重新分類方案

## 🎯 目標
將 `docs` 目錄下的文檔進行邏輯分類，提升文檔可讀性和維護性。

## 📋 現狀分析
目前共有 **34 個文檔文件**，分散在：
- `docs/` 根目錄：23 個 `.md` 文件
- `docs/guide/` 目錄：12 個 `.md` 文件
- `docs/guide/deepseek-testing/` 目錄：7 個文檔

## 🗂️ 建議的新目錄結構

```
docs/
├── README.md                           # 總索引文件
├── ai-instructions.md                  # AI 助手專用指令（保留根目錄）
├── ai-assistant-documentation-index.md # AI 文檔索引（保留根目錄）
├── 
├── 📁 architecture/                    # 系統架構相關
│   ├── ai-guidance-vector-architecture.md
│   ├── celery-beat-architecture-guide.md
│   ├── rvt-analytics-system-architecture.md
│   ├── rvt-assistant-database-vector-architecture.md
│   └── vector-database-scheduled-update-architecture.md
│
├── 📁 development/                     # 開發指南
│   ├── backend-development.md
│   ├── frontend-development.md
│   ├── ui-component-guidelines.md
│   ├── config-management-guide.md
│   └── commit_message_guidelines.md
│
├── 📁 deployment/                      # 部署與環境設置
│   ├── docker-installation.md
│   ├── django-postgresql-integration.md
│   ├── postgresql-setup.md
│   ├── adminer-setup.md
│   └── portainer-setup.md
│
├── 📁 ai-integration/                  # AI 整合相關
│   ├── dify-external-knowledge-api-guide.md
│   ├── dify-know-issue-integration.md
│   ├── dify-app-config-usage.md
│   └── api-integration.md
│
├── 📁 vector-search/                   # 向量搜尋系統
│   ├── vector-search-guide.md
│   ├── vector-search-overview.md
│   ├── ai-vector-search-guide.md
│   ├── vector-search-quick-reference.md
│   ├── vector-update-quick-reference.md
│   └── vector-upgrade-1024-summary.md
│
├── 📁 features/                        # 功能模組文檔
│   ├── rvt-analytics-workflow-diagrams.md
│   ├── content-image-management-system.md
│   └── knowledge-base-framework-implementation-report.md
│
├── 📁 refactoring-reports/             # 重構報告
│   ├── auth-refactoring-success-report.md
│   ├── common-serializers-refactoring-report.md
│   ├── rvt-guide-refactoring-report.md
│   └── rvt-guide-serializers-modularization-report.md
│
└── 📁 testing/                         # 測試相關
    ├── deepseek-testing/
    │   ├── README.md
    │   ├── configuration.md
    │   ├── ssh-connection-guide.md
    │   ├── troubleshooting.md
    │   └── examples/
    │       ├── basic-test.md
    │       ├── chinese-encoding.md
    │       └── performance-test.md
    └── testing-guides.md (新增)
```

## 🔄 文檔搬移對應表

### 📁 architecture/ (系統架構)
```
ai-guidance-vector-architecture.md
celery-beat-architecture-guide.md
rvt-analytics-system-architecture.md
rvt-assistant-database-vector-architecture.md
vector-database-scheduled-update-architecture.md
```

### 📁 development/ (開發指南)
```
guide/backend-development.md
guide/frontend-development.md
ui-component-guidelines.md
config-management-guide.md
commit_message_guidelines.md
```

### 📁 deployment/ (部署設置)
```
guide/docker-installation.md
guide/django-postgresql-integration.md
guide/postgresql-setup.md
guide/adminer-setup.md
guide/portainer-setup.md
```

### 📁 ai-integration/ (AI 整合)
```
guide/dify-external-knowledge-api-guide.md
guide/dify-know-issue-integration.md
guide/dify-app-config-usage.md
guide/api-integration.md
```

### 📁 vector-search/ (向量搜尋)
```
vector-search-guide.md
vector-search-overview.md
ai-vector-search-guide.md
vector-search-quick-reference.md
vector-update-quick-reference.md
vector-upgrade-1024-summary.md
```

### 📁 features/ (功能模組)
```
rvt-analytics-workflow-diagrams.md
content-image-management-system.md
knowledge-base-framework-implementation-report.md
```

### 📁 refactoring-reports/ (重構報告)
```
auth-refactoring-success-report.md
common-serializers-refactoring-report.md
rvt-guide-refactoring-report.md
rvt-guide-serializers-modularization-report.md
```

### 📁 testing/ (測試相關)
```
guide/deepseek-testing/ (整個目錄)
```

## 🎯 重新分類的優勢

1. **邏輯清晰**：相關文檔歸類在一起
2. **易於維護**：開發者可以快速找到所需文檔
3. **結構化**：符合軟體開發生命週期
4. **可擴展**：新文檔有明確的歸屬分類

## 📋 保留在根目錄的文件

- `ai-instructions.md` - AI 助手專用指令
- `ai-assistant-documentation-index.md` - AI 文檔索引
- `README.md` (新增) - 總索引文件

## ⚠️ 注意事項

1. **更新內部連結**：搬移文檔後需要更新所有相對路徑
2. **更新索引文件**：修改 `ai-assistant-documentation-index.md` 中的路徑
3. **CI/CD 影響**：檢查是否有腳本依賴原路徑
4. **團隊通知**：通知團隊成員文檔結構變更

## 🚀 執行步驟

1. 創建新目錄結構
2. 搬移文檔文件
3. 更新內部連結
4. 更新索引文件
5. 測試所有連結
6. 清理空目錄

---
**建立時間**: 2025-10-18  
**狀態**: 提案階段  
**影響範圍**: 所有 docs 目錄文檔