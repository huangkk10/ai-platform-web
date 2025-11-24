#!/bin/bash

# 測試 Protocol Assistant 對話記錄功能
# 驗證修復後是否正常記錄對話到資料庫

echo "======================================"
echo "Protocol Assistant 對話記錄測試"
echo "======================================"
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 步驟 1：檢查修復前的記錄數量
echo -e "${BLUE}[步驟 1]${NC} 檢查修復前的記錄數量..."
BEFORE_COUNT=$(docker exec postgres_db psql -U postgres -d ai_platform -t -c "SELECT COUNT(*) FROM conversation_sessions WHERE chat_type = 'protocol_assistant_chat';")
echo -e "  修復前記錄數：${YELLOW}${BEFORE_COUNT}${NC}"
echo ""

# 步驟 2：檢查最新記錄時間
echo -e "${BLUE}[步驟 2]${NC} 檢查最新記錄時間..."
LATEST_RECORD=$(docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT id, session_id, message_count, created_at FROM conversation_sessions WHERE chat_type = 'protocol_assistant_chat' ORDER BY created_at DESC LIMIT 1;")
echo "$LATEST_RECORD"
echo ""

# 步驟 3：提示用戶測試
echo -e "${YELLOW}[步驟 3]${NC} 請進行以下測試："
echo "  1. 開啟瀏覽器訪問 Protocol Assistant 聊天頁面"
echo "  2. 發送 2-3 個測試問題，例如："
echo "     - \"Protocol 有哪些功能？\""
echo "     - \"如何進行 CrystalDiskMark 測試？\""
echo "     - \"請提供 CUP 完整測試流程\""
echo ""
echo -e "${YELLOW}完成測試後按 Enter 繼續...${NC}"
read -r

# 步驟 4：檢查修復後的記錄數量
echo ""
echo -e "${BLUE}[步驟 4]${NC} 檢查修復後的記錄數量..."
AFTER_COUNT=$(docker exec postgres_db psql -U postgres -d ai_platform -t -c "SELECT COUNT(*) FROM conversation_sessions WHERE chat_type = 'protocol_assistant_chat';")
echo -e "  修復後記錄數：${YELLOW}${AFTER_COUNT}${NC}"

# 計算新增記錄數
NEW_RECORDS=$((AFTER_COUNT - BEFORE_COUNT))
echo ""
echo -e "${GREEN}[結果]${NC} 新增記錄數：${GREEN}${NEW_RECORDS}${NC}"
echo ""

# 步驟 5：顯示最新的 5 筆記錄
echo -e "${BLUE}[步驟 5]${NC} 顯示最新的 5 筆記錄..."
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    id, 
    LEFT(session_id, 20) as session_id, 
    chat_type, 
    message_count, 
    created_at 
FROM conversation_sessions 
WHERE chat_type = 'protocol_assistant_chat' 
ORDER BY created_at DESC 
LIMIT 5;
"
echo ""

# 步驟 6：檢查最新記錄的詳細資訊
echo -e "${BLUE}[步驟 6]${NC} 檢查最新記錄的詳細資訊..."
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    cs.id,
    cs.session_id,
    cs.chat_type,
    cs.message_count,
    cs.total_tokens,
    cs.created_at,
    COUNT(cm.id) as actual_message_count
FROM conversation_sessions cs
LEFT JOIN chat_messages cm ON cs.id = cm.conversation_id
WHERE cs.chat_type = 'protocol_assistant_chat'
GROUP BY cs.id, cs.session_id, cs.chat_type, cs.message_count, cs.total_tokens, cs.created_at
ORDER BY cs.created_at DESC
LIMIT 3;
"
echo ""

# 步驟 7：驗證結果
echo "======================================"
if [ "$NEW_RECORDS" -gt 0 ]; then
    echo -e "${GREEN}✅ 測試成功！${NC}"
    echo -e "   Protocol Assistant 對話記錄功能正常運作"
    echo -e "   新增了 ${GREEN}${NEW_RECORDS}${NC} 筆對話記錄"
else
    echo -e "${RED}❌ 測試失敗！${NC}"
    echo -e "   沒有新增任何對話記錄"
    echo -e "   ${YELLOW}請檢查：${NC}"
    echo "   1. 是否成功發送了測試訊息？"
    echo "   2. Django 日誌中是否有錯誤訊息？"
    echo ""
    echo "   查看日誌："
    echo "   docker logs ai-django --tail 50 | grep -i 'protocol'"
fi
echo "======================================"
echo ""

# 步驟 8：檢查 Analytics API
echo -e "${BLUE}[步驟 8]${NC} 測試 Analytics API..."
echo "  提示：需要登入才能訪問 API"
echo ""
echo "  測試指令（請在瀏覽器登入後執行）："
echo "  curl -X GET 'http://localhost/api/protocol-analytics/overview/?days=7' \\"
echo "    -H 'Cookie: sessionid=YOUR_SESSION_ID' \\"
echo "    -H 'Accept: application/json'"
echo ""

# 步驟 9：提供下一步建議
echo -e "${YELLOW}[下一步]${NC}"
echo "  1. 訪問 Analytics Dashboard：http://localhost/admin/analytics"
echo "  2. 切換到 'Protocol Assistant' 選項"
echo "  3. 確認可以看到近期的對話記錄和統計資料"
echo ""

echo "測試完成！"
