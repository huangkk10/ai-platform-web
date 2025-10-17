# 📚 AI Platform 文檔中心

歡迎來到 AI Platform 的文檔中心！這裡包含了系統的完整文檔，已按照功能和用途進行了分類整理。

## 🗂️ 文檔分類

### 📁 [architecture/](./architecture/) - 系統架構相關
深入了解 AI Platform 的系統設計和架構：
- `ai-guidance-vector-architecture.md` - AI 指導向量架構
- `celery-beat-architecture-guide.md` - Celery Beat 任務調度架構
- `rvt-analytics-system-architecture.md` - RVT 分析系統架構
- `rvt-assistant-database-vector-architecture.md` - RVT 助手資料庫向量架構
- `vector-database-scheduled-update-architecture.md` - 向量資料庫定時更新架構

### 📁 [development/](./development/) - 開發指南
開發人員必備的技術指南：
- `assistant-template-guide.md` - 🎯 **AI Assistant 標準範本指南**（使用 RVT Assistant 作為範本）
- `backend-development.md` - 後端開發指南
- `frontend-development.md` - 前端開發指南
- `ui-component-guidelines.md` - UI 組件使用規範
- `config-management-guide.md` - 配置管理指南
- `commit_message_guidelines.md` - Commit 訊息規範

### 📁 [deployment/](./deployment/) - 部署與環境設置
系統部署和環境配置相關文檔：
- `docker-installation.md` - Docker 安裝指南
- `django-postgresql-integration.md` - Django PostgreSQL 整合
- `postgresql-setup.md` - PostgreSQL 設置指南
- `adminer-setup.md` - Adminer 資料庫管理工具設置
- `portainer-setup.md` - Portainer 容器管理工具設置

### 📁 [ai-integration/](./ai-integration/) - AI 整合相關
AI 系統整合和配置文檔：
- `dify-external-knowledge-api-guide.md` - Dify 外部知識庫 API 指南
- `dify-know-issue-integration.md` - Dify Know Issue 整合指南
- `dify-app-config-usage.md` - Dify 應用配置使用指南
- `api-integration.md` - API 整合指南

### 📁 [vector-search/](./vector-search/) - 向量搜尋系統
向量搜尋功能的完整指南：
- `vector-search-guide.md` - 向量搜尋完整指南
- `vector-search-overview.md` - 向量搜尋系統概覽
- `ai-vector-search-guide.md` - AI 向量搜尋使用指南
- `vector-search-quick-reference.md` - 向量搜尋快速參考
- `vector-update-quick-reference.md` - 向量更新快速參考
- `vector-upgrade-1024-summary.md` - 向量系統升級摘要

### 📁 [features/](./features/) - 功能模組文檔
系統各功能模組的詳細說明：
- `rvt-analytics-workflow-diagrams.md` - RVT 分析工作流程圖
- `content-image-management-system.md` - 內容圖片管理系統
- `knowledge-base-framework-implementation-report.md` - 知識庫框架實施報告

### 📁 [refactoring-reports/](./refactoring-reports/) - 重構報告
系統重構和改進的記錄：
- `auth-refactoring-success-report.md` - 認證系統重構成功報告
- `common-serializers-refactoring-report.md` - 通用序列化器重構報告
- `rvt-guide-refactoring-report.md` - RVT 指南重構報告
- `rvt-guide-serializers-modularization-report.md` - RVT 指南序列化器模組化報告

### 📁 [testing/](./testing/) - 測試相關
測試工具和測試指南：
- `deepseek-testing/` - DeepSeek 測試工具目錄
  - `README.md` - DeepSeek 測試概覽
  - `configuration.md` - 測試配置說明
  - `ssh-connection-guide.md` - SSH 連接指南
  - `troubleshooting.md` - 故障排除指南
  - `examples/` - 測試範例目錄

## 🤖 AI 助手專用文檔

### 根目錄重要文檔
- [`ai-instructions.md`](./ai-instructions.md) - AI 助手專用指令和配置
- [`ai-assistant-documentation-index.md`](./ai-assistant-documentation-index.md) - AI 文檔索引和問題分類指引

## 📋 快速導航

### 🚀 新手入門
1. **環境設置**: 先閱讀 [`deployment/`](./deployment/) 目錄下的部署指南
2. **開發指南**: 參考 [`development/`](./development/) 目錄下的開發規範
3. **系統架構**: 了解 [`architecture/`](./architecture/) 目錄下的系統設計

### 🔧 開發相關
- **前端開發**: `development/frontend-development.md` + `development/ui-component-guidelines.md`
- **後端開發**: `development/backend-development.md` + `deployment/django-postgresql-integration.md`
- **AI 整合**: `ai-integration/` 目錄下所有文檔

### 🔍 功能使用
- **向量搜尋**: `vector-search/vector-search-guide.md`
- **知識庫管理**: `features/knowledge-base-framework-implementation-report.md`
- **RVT 分析**: `features/rvt-analytics-workflow-diagrams.md`

## 📝 文檔維護

### 更新記錄
- **2025-10-18**: 完成文檔重新分類，建立新的目錄結構
- **分類原則**: 按照功能用途分為 8 個主要類別
- **覆蓋範圍**: 包含 34 個文檔文件的完整重組

### 貢獻指南
1. 新增文檔請放入對應的分類目錄
2. 更新現有文檔請同時更新本索引文件
3. 遵循既定的命名和格式規範

---

**🎯 專案狀態**: ✅ 生產就緒  
**📊 文檔完整度**: 100%  
**🔄 最後更新**: 2025-10-18  
**👥 維護團隊**: AI Platform Team