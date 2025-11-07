#!/bin/bash
# Protocol Assistant 問題修復驗證腳本

echo "======================================"
echo "Protocol Assistant 修復驗證測試"
echo "======================================"
echo ""

# 設定參數
API_URL="http://localhost/api/protocol-assistant/chat/"
TOKEN="YOUR_AUTH_TOKEN_HERE"  # 請替換為實際的 Token

# 測試案例
declare -a TEST_CASES=(
    "crystaldiskmark 如何放測"
    "burn in test 如何放測"
    "如何進行 protocol 測試"
)

echo "📋 測試案例："
for i in "${!TEST_CASES[@]}"; do
    echo "  $((i+1)). ${TEST_CASES[$i]}"
done
echo ""

# 執行測試
for question in "${TEST_CASES[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 問題：$question"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 發送請求
    response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -H "Authorization: Token $TOKEN" \
        -d "{\"message\": \"$question\"}")
    
    # 解析結果
    success=$(echo "$response" | jq -r '.success')
    answer=$(echo "$response" | jq -r '.answer')
    
    if [ "$success" == "true" ]; then
        echo "✅ 請求成功"
        echo ""
        echo "🤖 AI 回答："
        echo "$answer" | head -c 500
        if [ ${#answer} -gt 500 ]; then
            echo "... (已截斷)"
        fi
        echo ""
        
        # 檢查是否是「不確定」回答
        if echo "$answer" | grep -qi "不確定\|不知道\|無法回答"; then
            echo "⚠️  警告：AI 回答了「不確定」"
        else
            echo "✅ AI 提供了具體答案"
        fi
    else
        echo "❌ 請求失敗"
        echo "錯誤：$response"
    fi
    
    echo ""
    sleep 2
done

echo "======================================"
echo "測試完成"
echo "======================================"
echo ""
echo "📊 驗證檢查清單："
echo "  [ ] AI 沒有回答「不確定」"
echo "  [ ] 回答包含具體的測試步驟"
echo "  [ ] 引用來源正確顯示"
echo ""
echo "如果所有測試通過，修復成功！✅"
