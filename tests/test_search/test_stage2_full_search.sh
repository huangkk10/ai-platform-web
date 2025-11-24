#!/bin/bash

echo "🧪 測試二階段搜尋 Stage 2 全文搜尋功能"
echo "=========================================="
echo ""

# 取得 Auth Token（假設使用 admin 用戶）
echo "📝 步驟 1：準備測試查詢"
echo "查詢內容：cup顏色"
echo ""

# 清空舊日誌
echo "🧹 清理舊日誌..."
docker exec ai-django bash -c "echo '' > /app/logs/django.log"
echo ""

# 發送測試查詢
echo "📤 步驟 2：發送測試查詢到 Protocol Assistant"
echo "等待 AI 回應..."
echo ""

# 注意：需要替換成實際的 Token
# 這裡使用 curl 發送請求
curl -X POST "http://localhost/api/protocol-guide/chat/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -d '{"message": "cup顏色"}' \
  2>/dev/null | jq -r '.answer' | head -10

echo ""
echo ""
echo "📊 步驟 3：檢查日誌 - 驗證 Stage 2 全文搜尋"
echo "=========================================="
echo ""

# 檢查 Stage 2 是否被觸發
echo "🔍 檢查 Stage 2 觸發："
docker logs ai-django --tail 200 | grep -E "階段 2|Stage 2" | tail -5

echo ""
echo "🏷️ 檢查 __FULL_SEARCH__ 標記："
docker logs ai-django --tail 200 | grep "__FULL_SEARCH__" | tail -5

echo ""
echo "🎯 檢查標記檢測和清理："
docker logs ai-django --tail 200 | grep -E "檢測到 Stage 2|清理後查詢" | tail -5

echo ""
echo "🔧 檢查 search_mode 切換："
docker logs ai-django --tail 200 | grep -E "search_mode.*document" | tail -5

echo ""
echo "📈 檢查全文搜尋執行："
docker logs ai-django --tail 200 | grep -E "全文級搜尋|document_only|文檔搜索" | tail -5

echo ""
echo "✅ 測試完成！"
echo ""
echo "預期結果："
echo "  1. ✅ 日誌顯示「階段 2: 發送...」"
echo "  2. ✅ 日誌顯示「Stage 2 查詢（含標記）: cup顏色 __FULL_SEARCH__」"
echo "  3. ✅ 日誌顯示「檢測到 Stage 2 標記，切換到全文搜尋模式」"
echo "  4. ✅ 日誌顯示「清理後查詢: 'cup顏色'」（不含標記）"
echo "  5. ✅ 日誌顯示「search_mode='document_only'」"
echo ""
