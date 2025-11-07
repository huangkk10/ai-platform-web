#!/bin/bash
# 測試 Dify API 的直接請求，檢查問題

echo "======================================"
echo "Dify API 直接測試"
echo "======================================"
echo ""

API_URL="http://10.10.172.37/v1/chat-messages"
API_KEY="app-MgZZOhADkEmdUrj2DtQLJ23G"

echo "📝 測試問題：crystaldiskmark 如何放測"
echo ""

# 測試 1：完全不設定 retrieval_model
echo "測試 1：不設定 retrieval_model（使用 Dify APP 預設配置）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

response1=$(curl -s -X POST "$API_URL" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "crystaldiskmark 如何放測",
    "inputs": {},
    "response_mode": "blocking",
    "user": "test_user_1"
  }')

echo "回應："
echo "$response1" | jq -r '.answer' | head -c 300
echo ""
echo ""

# 測試 2：明確設定 score_threshold = 0
echo "測試 2：明確設定 score_threshold = 0"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

response2=$(curl -s -X POST "$API_URL" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "crystaldiskmark 如何放測",
    "inputs": {},
    "response_mode": "blocking",
    "user": "test_user_2",
    "retrieval_model": {
      "search_method": "semantic_search",
      "reranking_enable": false,
      "top_k": 5,
      "score_threshold_enabled": true,
      "score_threshold": 0.0
    }
  }')

echo "回應："
echo "$response2" | jq -r '.answer' | head -c 300
echo ""
echo ""

# 測試 3：測試外部知識庫 API 返回的內容
echo "測試 3：檢查外部知識庫 API 返回的內容"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

kb_response=$(curl -s -X POST "http://localhost/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_guide_db",
    "query": "crystaldiskmark 如何放測",
    "retrieval_setting": {
      "top_k": 5,
      "score_threshold": 0.0
    }
  }')

echo "外部知識庫返回："
echo "$kb_response" | jq '.records | length'
echo "結果數量"
echo ""
echo "第一條結果的分數和標題："
echo "$kb_response" | jq -r '.records[0] | "Score: \(.score), Title: \(.title)"'
echo ""
echo "第一條結果的內容（前 200 字）："
echo "$kb_response" | jq -r '.records[0].content' | head -c 200
echo ""
echo ""

echo "======================================"
echo "測試完成"
echo "======================================"
