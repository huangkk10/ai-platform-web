# 🧹 測試檔案清理建議

**日期**：2025-11-05  
**目的**：評估專案根目錄測試檔案的必要性並建議處理方式

---

## 📋 測試檔案清單與分析

### 1️⃣ `test_image_api.sh`
**用途**：測試圖片 API 端點是否正常回應

**內容摘要**：
```bash
- 測試多個圖片 ID (32, 35, 36, 37, 38, 39, 40)
- 檢查 HTTP 狀態碼
- 顯示圖片資料的 JSON 內容
```

**評估**：
- ✅ **保留價值**：中等
- 🎯 **用途**：快速驗證圖片 API 功能
- 📁 **建議**：移至 `tests/` 目錄
- ⚠️ **改進**：可以整合到自動化測試中

---

### 2️⃣ `test_image_preview_debug.sh`
**用途**：圖片預覽除錯流程說明腳本

**內容摘要**：
```bash
- 顯示修改總結和測試步驟
- 指導如何使用瀏覽器開發者工具除錯
- 列出預期的控制台輸出
- 提供故障排除建議
```

**評估**：
- ⚠️ **保留價值**：低（內容已整理到 Markdown 文檔）
- 📚 **替代方案**：已有 `docs/debugging/DEBUG_IMAGE_PREVIEW.md`
- 📁 **建議**：**可以刪除**（功能重複）
- ✨ **原因**：所有資訊已經在文檔中，且文檔更易於維護

---

### 3️⃣ `test_markdown_html_support.html`
**用途**：測試 markdown-it 的 HTML 標籤支援功能

**內容摘要**：
```html
- 獨立的 HTML 測試頁面
- 載入 markdown-it CDN
- 即時渲染測試
- 多個範例（<br> 標籤、混合內容、自動換行）
```

**評估**：
- ✅ **保留價值**：高
- 🎯 **用途**：驗證 markdown-it 配置和行為
- 📁 **建議**：移至 `tests/manual/` 目錄
- 💡 **優點**：可獨立運行，不依賴後端
- 🔧 **用途場景**：
  - 測試新的 markdown 配置
  - 驗證 HTML 支援行為
  - 除錯 markdown 渲染問題

---

### 4️⃣ `test_protocol_image_preview_fix.sh`
**用途**：Protocol Guide 圖片預覽修復測試指南

**內容摘要**：
```bash
- 說明修復內容（移除 SSR、使用 markdown-it）
- 測試步驟和預期結果
- 可用測試圖片 ID 列表
- 技術細節說明（修復前後對比）
```

**評估**：
- ⚠️ **保留價值**：低（歷史文檔性質）
- 📚 **性質**：修復說明文檔（非實際測試腳本）
- 📁 **建議**：**可以刪除或歸檔**
- ✨ **原因**：
  - 問題已經修復完成
  - 內容屬於歷史記錄，不是持續性測試
  - 如果需要保留，應轉為 Markdown 文檔放入 `docs/debugging/`

---

### 5️⃣ `test_protocol_image_preview.sh`
**用途**：Protocol Guide 圖片顯示功能測試指南

**內容摘要**：
```bash
- 測試步驟說明
- 從資料庫查詢可用的測試圖片
- 顯示已完成的修改內容
- 預期效果說明
```

**評估**：
- ⚠️ **保留價值**：低（與 #4 重複）
- 📚 **性質**：功能測試指南（非自動化測試）
- 📁 **建議**：**可以刪除或合併**
- ✨ **原因**：
  - 與 `test_protocol_image_preview_fix.sh` 功能重複
  - 包含資料庫查詢邏輯（可保留這部分）
  - 其餘內容為歷史文檔

---

## 🎯 處理建議總結

### ✅ **保留並移動**

| 檔案 | 建議位置 | 理由 |
|------|---------|------|
| `test_image_api.sh` | `tests/manual/test_image_api.sh` | 實用的手動測試工具 |
| `test_markdown_html_support.html` | `tests/manual/test_markdown_html_support.html` | 獨立的渲染測試頁面 |

### ❌ **可以刪除**

| 檔案 | 理由 | 替代方案 |
|------|------|---------|
| `test_image_preview_debug.sh` | 內容已整合到 Markdown 文檔 | `docs/debugging/DEBUG_IMAGE_PREVIEW.md` |
| `test_protocol_image_preview_fix.sh` | 歷史修復記錄，問題已解決 | 可轉為文檔保存在 `docs/debugging/` |
| `test_protocol_image_preview.sh` | 與 #4 重複，問題已解決 | 資料庫查詢部分可整合到 #1 |

### 🔄 **可選：轉換為文檔**

如果想保留歷史記錄：
- `test_protocol_image_preview_fix.sh` → `docs/debugging/protocol-guide-image-preview-fix-history.md`
- `test_protocol_image_preview.sh` → （合併到上述文檔）

---

## 📂 建議的目錄結構

```
tests/
├── manual/                                    # 手動測試工具
│   ├── test_image_api.sh                     # ✅ 保留
│   ├── test_markdown_html_support.html       # ✅ 保留
│   └── README.md                              # 說明如何使用這些測試工具
│
└── (其他自動化測試目錄)

docs/
└── debugging/
    ├── DEBUG_IMAGE_PREVIEW.md                 # ✅ 已存在
    └── protocol-guide-image-preview-fix-history.md  # 🆕 可選：歷史記錄
```

---

## 🚀 執行清理的命令

### 步驟 1：創建 tests/manual/ 目錄
```bash
mkdir -p tests/manual
```

### 步驟 2：移動保留的測試檔案
```bash
mv test_image_api.sh tests/manual/
mv test_markdown_html_support.html tests/manual/
```

### 步驟 3：刪除不必要的測試腳本
```bash
# 方案 A：直接刪除
rm test_image_preview_debug.sh
rm test_protocol_image_preview_fix.sh
rm test_protocol_image_preview.sh

# 方案 B：先備份再刪除（保險起見）
mkdir -p backups/test_scripts
mv test_image_preview_debug.sh backups/test_scripts/
mv test_protocol_image_preview_fix.sh backups/test_scripts/
mv test_protocol_image_preview.sh backups/test_scripts/
```

### 步驟 4：創建測試工具說明文檔
```bash
cat > tests/manual/README.md << 'EOF'
# 🧪 手動測試工具

本目錄包含手動測試工具和測試頁面。

## 可用工具

### 1. test_image_api.sh
測試圖片 API 端點是否正常。

**用法**：
```bash
./tests/manual/test_image_api.sh
```

### 2. test_markdown_html_support.html
測試 markdown-it 的 HTML 標籤支援。

**用法**：
在瀏覽器中打開此檔案即可使用。

EOF
```

---

## ⚖️ 決策建議

### 保守方案（推薦）
1. ✅ 移動 `test_image_api.sh` 和 `test_markdown_html_support.html` 到 `tests/manual/`
2. 📦 將其他三個腳本移至 `backups/test_scripts/`（不直接刪除）
3. 📝 創建 `tests/manual/README.md` 說明文檔
4. ⏰ 一個月後確認不需要，再刪除備份

### 積極方案
1. ✅ 移動有用的測試工具到 `tests/manual/`
2. ❌ 直接刪除歷史測試腳本
3. 📝 創建說明文檔

---

## 📊 效益評估

### 清理後的好處
- ✅ 專案根目錄更整潔
- ✅ 測試檔案有統一的組織結構
- ✅ 減少混淆（什麼檔案還需要？什麼是歷史檔案？）
- ✅ 新成員更容易理解專案結構

### 風險評估
- ⚠️ **風險極低**：這些都是測試/除錯腳本，不是核心功能
- ✅ **可逆性**：可以從 Git 歷史恢復
- ✅ **備份方案**：先移至 backups/ 目錄觀察一段時間

---

## ✅ 結論

**總體建議**：這些測試腳本**不是必要的**，可以安全清理。

**建議保留**：
- `test_image_api.sh` - 實用工具
- `test_markdown_html_support.html` - 獨立測試頁面

**建議刪除/歸檔**：
- `test_image_preview_debug.sh`
- `test_protocol_image_preview_fix.sh`
- `test_protocol_image_preview.sh`

這些腳本都是**歷史除錯記錄**，功能已經實現，問題已經解決，保留的價值不高。

---

**更新人員**：AI Assistant  
**更新日期**：2025-11-05  
**建議狀態**：待確認執行
