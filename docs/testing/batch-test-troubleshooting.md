# 批量測試「全選」功能疑難排解

## 問題描述
用戶報告每次測試時點擊「全選」，但測試結果顯示並非所有版本都被測試。

## 驗證結果

### 系統狀態 ✅
- 資料庫有 7 個啟用版本（ID: 3-9）
- API 正確返回全部 7 個版本
- 前端程式碼邏輯正確

### 測試記錄分析
- **批次 20251123_085101**: 只測試了 3 個版本（ID: 3, 4, 5）
- **批次 20251123_085038**: 只測試了 4 個版本（ID: 6, 7, 8, 9）
- **預期**: 應該測試 7 個版本

## 疑難排解步驟

### 步驟 1：強制刷新前端
```bash
# 清除瀏覽器快取並重新載入
1. 按 Ctrl+Shift+R（Linux/Windows）或 Cmd+Shift+R（Mac）
2. 或者打開開發者工具（F12），在 Network 面板勾選「Disable cache」
```

### 步驟 2：驗證版本列表載入
1. 打開批量測試頁面：`http://localhost/benchmark/batch-test`
2. 打開瀏覽器開發者工具（F12）
3. 切換到 Console 面板
4. 查看是否有錯誤訊息
5. 切換到 Network 面板
6. 篩選 `versions` 請求
7. 確認返回的版本數量是否為 7

### 步驟 3：確認版本全選狀態
1. 等待頁面完全載入（loading 圖示消失）
2. **不要點擊「全選」按鈕**（因為預設已經全選）
3. 檢查每個版本的 checkbox 是否都被勾選
4. 在 Console 輸入以下命令確認：
   ```javascript
   // 這應該顯示 7
   document.querySelectorAll('.version-checkbox:checked').length
   ```

### 步驟 4：執行完整測試
1. **確認所有 7 個版本都被勾選**
2. 在 Console 執行：
   ```javascript
   // 應該顯示 [3, 4, 5, 6, 7, 8, 9] 或類似的 7 個 ID
   console.log('選中的版本:', window.selectedVersionIds || '無法取得');
   ```
3. 點擊「開始批量測試」
4. 觀察執行過程

### 步驟 5：查看 API 請求內容
1. 在 Network 面板找到 `batch_test` 請求
2. 查看 Request Payload
3. 確認 `version_ids` 陣列包含 7 個 ID

## 預期正常行為

### API 請求內容（正確範例）
```json
{
  "version_ids": [3, 4, 5, 6, 7, 8, 9],
  "batch_name": "批量測試 2025/11/23 ...",
  "notes": "測試 7 個版本，XX 個測試案例",
  "force_retest": false
}
```

### 資料庫記錄（正確範例）
執行完成後，資料庫應該有 7 筆記錄，都有相同的 batch_id：
```sql
SELECT notes, COUNT(*) 
FROM benchmark_test_run 
WHERE notes LIKE '%批次 ID: 20251123_%' 
GROUP BY notes 
ORDER BY MIN(created_at) DESC 
LIMIT 1;

-- 應該顯示：
-- notes: "批次 ID: 20251123_HHMMSS"
-- count: 7
```

## 手動驗證腳本

創建一個測試腳本來驗證「全選」功能：

\`\`\`bash
# 執行完整的 7 個版本測試
docker exec ai-django bash -c "cd /app && python << 'PYEOF'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.benchmark.batch_version_tester import batch_test_selected_versions

# 全選所有版本
result = batch_test_selected_versions(
    version_ids=[3, 4, 5, 6, 7, 8, 9],
    batch_name='完整測試-全部7個版本',
    notes='手動驗證全選功能'
)

if result['success']:
    print(f'✅ 測試完成！')
    print(f'批次 ID: {result[\"batch_id\"]}')
    print(f'測試的版本數: {len(result[\"test_runs\"])}')
    print(f'測試 Run IDs: {result[\"test_run_ids\"]}')
else:
    print(f'❌ 測試失敗: {result[\"error\"]}')
PYEOF
"
\`\`\`

執行後查詢資料庫：
\`\`\`bash
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
  notes,
  COUNT(*) as version_count,
  ARRAY_AGG(version_id ORDER BY version_id) as version_ids
FROM benchmark_test_run
WHERE notes LIKE '%完整測試-全部7個版本%'
GROUP BY notes;
"
\`\`\`

**預期結果**: 應該顯示 7 個版本（version_count: 7, version_ids: {3,4,5,6,7,8,9}）

## 如果問題持續

如果確認前端顯示正常但仍然無法測試全部版本，可能需要：

1. **檢查後端日誌**
   \`\`\`bash
   docker logs ai-django --tail 100 | grep -i "batch_test\|version"
   \`\`\`

2. **檢查前端 Console 錯誤**
   - 是否有 JavaScript 錯誤
   - 是否有 API 錯誤響應

3. **重啟服務**
   \`\`\`bash
   cd /home/user/codes/ai-platform-web
   docker compose restart django react
   \`\`\`

4. **聯繫開發團隊**
   - 提供瀏覽器 Console 截圖
   - 提供 Network 面板的 API 請求內容
   - 提供測試的具體步驟

## 聯絡資訊
- GitHub Issues: [專案 Repository]
- 文檔: `/docs/testing/BATCH_TESTING_UI_TEST_GUIDE.md`
