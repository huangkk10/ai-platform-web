# Protocol 版本管理系統使用手冊

**系統版本**: v1.2.2  
**最後更新**: 2025-11-27  
**適用對象**: Protocol Assistant 系統管理員、開發人員

---

## 📋 目錄

1. [系統概述](#系統概述)
2. [訪問權限](#訪問權限)
3. [功能說明](#功能說明)
4. [操作指南](#操作指南)
5. [常見問題](#常見問題)
6. [故障排除](#故障排除)

---

## 🎯 系統概述

### 什麼是 Protocol 版本管理系統？

Protocol 版本管理系統允許您：
- **查看所有 Protocol Guide 的 Dify 配置版本**
- **設定 Baseline 版本**（決定 Protocol Assistant 使用哪個版本進行檢索）
- **查看每個版本的檢索模式和核心配置**

### 為什麼需要版本管理？

不同版本的 Protocol Guide 使用不同的檢索策略：
- **v1.1**: 基礎二階段搜尋
- **v1.2**: 加入 Title Boost
- **v1.2.1**: 動態 Threshold + Title Boost
- **v1.2.2**: 混合搜尋 + Title Boost（目前 Baseline）

透過版本管理，您可以：
- ✅ 快速切換不同檢索策略
- ✅ A/B 測試不同版本的效果
- ✅ 回滾到穩定版本

---

## 🔑 訪問權限

### 誰可以訪問版本管理頁面？

**需要權限**: `kb_protocol_assistant`（Protocol Assistant 知識庫權限）

**權限檢查**:
1. 登入系統
2. 檢查側邊欄是否顯示「Knowledge Base」→「Protocol 版本管理」
3. 如果沒有，請聯絡系統管理員開通權限

### 如何開通權限？

**管理員操作**:
1. 訪問 `http://localhost/admin/user-management`
2. 編輯目標用戶
3. 勾選「知識庫 Protocol Assistant」權限
4. 儲存

---

## 📊 功能說明

### 頁面佈局

```
┌────────────────────────────────────────────────────────────┐
│ Protocol Guide 版本管理                    [重新整理]      │
├────────────────────────────────────────────────────────────┤
│ 📌 當前 Baseline 版本                                      │
│ ⭐ Dify 二階搜尋 v1.2.2 (Hybrid Search + Title Boost)     │
│    版本代碼: dify-two-tier-v1.2.2                         │
│    檢索模式: 混合搜尋                                      │
├────────────────────────────────────────────────────────────┤
│ 版本列表                                                   │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ 版本代碼 │ 版本名稱 │ 檢索模式 │ 狀態 │ 操作       │ │
│ ├──────────────────────────────────────────────────────┤ │
│ │ ⭐ v1.2.2│ Hybrid...│ 混合搜尋 │ ✅   │ 當前 Base..│ │
│ │    v1.2.1│ Dynamic..│ 動態 Thr │ ✅   │ 設為 Base..│ │
│ │    v1.2  │ Title... │ 二階段   │ ✅   │ 設為 Base..│ │
│ └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### 版本列表欄位說明

| 欄位 | 說明 | 圖示含義 |
|------|------|---------|
| **版本代碼** | 版本的唯一識別碼 | ⭐ = Baseline 版本 |
| **版本名稱** | 版本的完整名稱 | - |
| **檢索模式** | 使用的搜尋策略 | 🔀 = 混合搜尋 |
| **核心配置** | 關鍵參數設定 | RRF k, Title Boost |
| **狀態** | 版本啟用狀態 | ✅ 啟用 / ❌ 停用<br>🔵 Baseline |
| **操作** | 可執行的動作 | 「設為 Baseline」按鈕 |

### 檢索模式標籤

| 標籤 | 顏色 | 說明 |
|------|------|------|
| **混合搜尋** | 藍色 | 向量搜尋 + 關鍵字搜尋 + RRF 融合 |
| **動態 Threshold** | 橙色 | 從資料庫動態載入閾值參數 |
| **二階段搜尋** | 綠色 | 基礎的兩階段向量搜尋 |

---

## 📖 操作指南

### 操作 1：查看當前 Baseline 版本

**目的**: 確認 Protocol Assistant 目前使用哪個版本

**步驟**:
1. 訪問 `http://localhost/protocol/versions`
2. 查看頁面頂部的金色卡片
3. 確認顯示的版本資訊

**範例**:
```
📌 當前 Baseline 版本
⭐ Dify 二階搜尋 v1.2.2 (Hybrid Search + Title Boost)
   版本代碼: dify-two-tier-v1.2.2
   檢索模式: 混合搜尋
```

---

### 操作 2：查看所有可用版本

**目的**: 了解系統中有哪些版本可以選擇

**步驟**:
1. 滾動到版本列表表格
2. 查看所有版本的詳細資訊
3. 注意 ⭐ 星星圖標表示當前 Baseline

**版本資訊解讀**:
```
⭐ ✅ 🔀 ID: 5 | dify-two-tier-v1.2.2 | Hybrid Search
   ✅    ID: 4 | dify-two-tier-v1.1.1 | Dynamic Threshold
   ✅    ID: 3 | dify-two-tier-v1.2.1 | Dynamic Threshold + Title
```

**圖例**:
- ⭐ = Baseline 版本
- ✅ = 啟用狀態
- 🔀 = 混合搜尋

---

### 操作 3：設定新的 Baseline 版本（重要！）

**目的**: 切換 Protocol Assistant 使用的檢索版本

**步驟**:

#### 3.1 找到目標版本
1. 在版本列表中找到您想設為 Baseline 的版本
2. 確認該版本狀態為「✅ 啟用」
3. 注意該版本的檢索模式和核心配置

#### 3.2 點擊「設為 Baseline」按鈕
1. 點擊目標版本右側的「設為 Baseline」按鈕
2. 系統會彈出確認對話框

#### 3.3 檢查確認對話框

**對話框內容**:
```
┌─────────────────────────────────────────────────┐
│ 設定為 Baseline 版本                             │
├─────────────────────────────────────────────────┤
│ 確定要將 Dify 二階搜尋 v1.2.1 設定為 Baseline  │
│ 版本嗎？                                         │
│                                                  │
│ ⚠️ 此版本使用動態 Threshold                     │
│ • 配置將從資料庫即時載入                        │
│ • 可在 Threshold Setting 頁面調整參數           │
│                                                  │
│ ℹ️ 注意：設定為 Baseline 後，Protocol          │
│ Assistant 將使用此版本的配置進行檢索。          │
│                                                  │
│              [取消]      [確定設定]              │
└─────────────────────────────────────────────────┘
```

**提示說明**:

##### 藍色提示（混合搜尋）:
```
🔵 此版本使用混合搜尋
• 向量搜尋 + 關鍵字搜尋
• RRF 融合（k=60）
• Title Boost (+15%)
```

**含義**: 
- 同時使用向量搜尋和關鍵字搜尋
- 使用 RRF 演算法融合兩種搜尋結果
- 標題匹配的文檔會額外加分 15%

##### 橙色提示（動態 Threshold）:
```
🟠 此版本使用動態 Threshold
• 配置將從資料庫即時載入（SearchThresholdSetting）
• 可在 Threshold Setting 頁面調整參數
```

**含義**:
- 搜尋閾值不是寫死在代碼中
- 可以在不重啟系統的情況下調整參數
- 需要在「Threshold Setting」頁面管理配置

#### 3.4 確認設定
1. 檢查對話框中的資訊
2. 如果確認無誤，點擊「確定設定」
3. 等待系統處理（通常 < 1 秒）

#### 3.5 驗證設定成功
1. 看到綠色成功訊息：「✅ Baseline 版本設定成功」
2. 頁面自動重新整理
3. 確認：
   - 金色 Baseline 卡片更新為新版本
   - 版本列表中 ⭐ 星星移動到新版本
   - 舊版本的「當前 Baseline」標籤消失

**成功範例**:
```
✅ Baseline 版本設定成功

📌 當前 Baseline 版本（更新後）
⭐ Dify 二階搜尋 v1.2.1 (Dynamic Threshold + Title Boost)
   版本代碼: dify-two-tier-v1.2.1
   檢索模式: 動態 Threshold
```

---

### 操作 4：重新整理版本列表

**目的**: 確保看到最新的版本資訊

**步驟**:
1. 點擊頁面右上角的「重新整理」按鈕
2. 等待載入（通常 < 0.5 秒）
3. 版本列表更新

**使用時機**:
- 其他管理員可能已修改 Baseline
- 確認剛才的設定是否生效
- 系統新增了版本

---

## ❓ 常見問題

### Q1: 什麼是 Baseline 版本？

**A**: Baseline 版本是 Protocol Assistant 目前使用的檢索配置版本。當用戶在 Protocol Assistant 中提問時，系統會使用 Baseline 版本的檢索策略來搜尋相關文檔。

### Q2: 切換 Baseline 版本會影響現有的對話嗎？

**A**: 
- **新對話**: 立即使用新的 Baseline 版本
- **現有對話**: 繼續使用對話開始時的版本（不受影響）
- **建議**: 測試新版本時，開啟新對話

### Q3: 多個管理員同時設定 Baseline 會怎樣？

**A**: 系統使用資料庫事務確保一致性，最後一個設定會生效。建議團隊協調好再進行切換。

### Q4: 可以停用 Baseline 版本嗎？

**A**: 不可以。系統會阻止您將當前 Baseline 版本停用。如果需要停用某個版本，請先切換 Baseline 到其他版本。

### Q5: 「設為 Baseline」按鈕是灰色的怎麼辦？

**可能原因**:
1. **該版本已經是 Baseline** → 按鈕會顯示「當前 Baseline」標籤
2. **該版本未啟用** → 需要先啟用版本（聯絡管理員）
3. **沒有權限** → 確認是否有 `kb_protocol_assistant` 權限

### Q6: 混合搜尋和二階段搜尋有什麼區別？

**二階段搜尋** (v1.1, v1.2):
- Stage 1: 段落向量搜尋
- Stage 2: 全文向量搜尋
- 速度快，但可能錯過關鍵字精確匹配

**混合搜尋** (v1.2.2):
- Stage 1: 段落向量搜尋 + 關鍵字搜尋 + RRF 融合
- Stage 2: 全文向量搜尋
- 速度稍慢（+20ms），但準確度提升 20%

**建議**:
- 一般使用：v1.2.2（混合搜尋）
- 需要極速回應：v1.2（二階段 + Title Boost）

### Q7: 如何測試新版本的效果？

**測試步驟**:
1. 記錄當前 Baseline 版本（以便回滾）
2. 設定新版本為 Baseline
3. 在 Protocol Assistant 中開啟**新對話**
4. 使用相同的測試問題
5. 比較回應質量
6. 如果不滿意，切換回原版本

**測試問題範例**:
- 「iol 密碼是什麼？」（測試精確匹配）
- 「如何進行 CrystalDiskMark 測試？」（測試語義理解）
- 「Lenovo 有哪些測試項目？」（測試混合查詢）

---

## 🔧 故障排除

### 問題 1: 頁面無法載入

**症狀**: 訪問 `/protocol/versions` 顯示錯誤或空白頁

**檢查步驟**:
1. **確認權限**
   ```bash
   # 檢查用戶權限
   # 側邊欄應該顯示「Protocol 版本管理」選項
   ```

2. **檢查前端容器**
   ```bash
   docker compose logs react --tail 50
   # 應該看到：Compiled successfully!
   ```

3. **檢查後端容器**
   ```bash
   docker compose logs django --tail 50 | grep "error"
   # 不應該有錯誤訊息
   ```

4. **檢查 API 端點**
   ```bash
   curl http://localhost/api/dify/versions/
   # 應該返回版本列表 JSON
   ```

**解決方案**:
- 如果是權限問題：聯絡管理員開通權限
- 如果是容器問題：重啟容器 `docker compose restart`
- 如果是 API 問題：查看後端日誌排查

---

### 問題 2: 設定 Baseline 失敗

**症狀**: 點擊「確定設定」後出現錯誤訊息

**常見錯誤**:

#### 錯誤 1: 「版本 ID X 不存在」
```
❌ 設定 Baseline 失敗：版本 ID 5 不存在
```

**原因**: 版本已被刪除或 ID 錯誤

**解決方案**: 
1. 重新整理頁面
2. 從列表中重新選擇版本

#### 錯誤 2: 「版本未啟用」
```
❌ 設定 Baseline 失敗：版本「v1.2.1」未啟用，請先啟用該版本
```

**原因**: 該版本被停用了

**解決方案**:
1. 聯絡管理員啟用該版本
2. 或選擇其他已啟用的版本

#### 錯誤 3: 「網絡錯誤」
```
❌ 設定 Baseline 失敗：Network Error
```

**原因**: 前後端通訊問題

**解決方案**:
1. 檢查網絡連接
2. 確認後端容器運行中
3. 刷新頁面重試

---

### 問題 3: Baseline 卡片顯示錯誤版本

**症狀**: 設定成功但卡片沒有更新

**檢查步驟**:
1. **檢查瀏覽器快取**
   - 按 `Ctrl + Shift + R`（Windows/Linux）
   - 或 `Cmd + Shift + R`（Mac）
   - 強制刷新頁面

2. **檢查資料庫**
   ```bash
   docker exec postgres_db psql -U postgres -d ai_platform -c "
   SELECT id, version_code, is_baseline 
   FROM dify_config_version 
   WHERE is_baseline = true;
   "
   ```

3. **檢查快取**
   ```bash
   # 進入 Django shell
   docker exec -it ai-django python manage.py shell
   
   # 檢查快取狀態
   from library.config.dify_config_manager import get_baseline_version_code
   print(get_baseline_version_code())
   ```

**解決方案**:
- 資料庫正確但頁面錯誤：清除瀏覽器快取
- 快取過期：重啟 Django 容器
- 都不行：聯絡技術支援

---

### 問題 4: Protocol Assistant 沒有使用新的 Baseline

**症狀**: 切換 Baseline 後，Protocol Assistant 回應沒有改變

**檢查步驟**:
1. **確認是新對話**
   - 現有對話使用對話開始時的版本
   - 需要開啟**新對話**測試

2. **檢查 Dify 日誌**
   ```bash
   docker logs ai-django | grep "Baseline" | tail -20
   # 應該看到：使用 Baseline 版本: dify-two-tier-v1.2.2
   ```

3. **檢查版本載入**
   ```bash
   docker logs ai-django | grep "version_config" | tail -20
   # 應該看到載入的版本配置
   ```

**解決方案**:
1. 在 Protocol Assistant 中開啟新對話
2. 如果仍無效，重啟 Django 容器
3. 檢查 Dify 應用配置是否正確

---

## 📞 技術支援

### 聯絡方式

**技術支援**: AI Platform Team  
**郵件**: [團隊郵件]  
**文檔位置**: `/docs/implementation-plans/`

### 報告問題時請提供

1. **問題描述**：詳細說明發生了什麼
2. **操作步驟**：如何重現問題
3. **錯誤訊息**：完整的錯誤訊息（如有）
4. **截圖**：相關的頁面截圖
5. **瀏覽器**：使用的瀏覽器和版本
6. **時間**：問題發生的時間

### 常用診斷命令

```bash
# 檢查容器狀態
docker compose ps

# 檢查前端日誌
docker compose logs react --tail 50

# 檢查後端日誌
docker compose logs django --tail 50

# 檢查資料庫連接
docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT 1;"

# 檢查 Baseline 版本
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT version_code, is_baseline 
FROM dify_config_version 
WHERE is_baseline = true;
"
```

---

## 📚 相關文檔

- [v1.2.2 混合搜尋實施計畫](./v1.2.2-hybrid-search-implementation-plan.md)
- [v1.2.2 最終完成報告](./v1.2.2-final-completion-report.md)
- [Protocol Assistant 使用手冊](../user-manuals/protocol-assistant-user-guide.md)

---

**手冊版本**: v1.0  
**最後更新**: 2025-11-27  
**作者**: AI Platform Team
