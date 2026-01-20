#!/bin/bash

# 🎯 Beta 標籤功能驗證腳本

echo "=================================="
echo "🔍 Beta 標籤功能驗證"
echo "=================================="
echo ""

# 1. 檢查環境變數
echo "📋 1. 檢查環境變數設定..."
DEPLOY_ENV=$(docker exec ai-react printenv | grep REACT_APP_DEPLOY_ENV | cut -d'=' -f2)

if [ "$DEPLOY_ENV" == "develop" ]; then
    echo "✅ REACT_APP_DEPLOY_ENV = develop (正確)"
    echo "   → Beta 標籤應該會顯示"
else
    echo "❌ REACT_APP_DEPLOY_ENV = $DEPLOY_ENV"
    echo "   → Beta 標籤不會顯示"
fi
echo ""

# 2. 檢查容器狀態
echo "📋 2. 檢查容器狀態..."
CONTAINER_STATUS=$(docker inspect -f '{{.State.Status}}' ai-react 2>/dev/null)

if [ "$CONTAINER_STATUS" == "running" ]; then
    echo "✅ 前端容器運行中"
else
    echo "❌ 前端容器未運行（狀態: $CONTAINER_STATUS）"
fi
echo ""

# 3. 檢查前端服務
echo "📋 3. 檢查前端服務..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服務正常（http://localhost:3000）"
else
    echo "⚠️  前端服務可能還在啟動中，請稍等 10-20 秒"
fi
echo ""

# 4. 檢查修改的檔案
echo "📋 4. 檢查修改的檔案..."

# 檢查 Sidebar.js
if grep -q "REACT_APP_DEPLOY_ENV === 'develop'" frontend/src/components/Sidebar.js 2>/dev/null; then
    echo "✅ Sidebar.js 已正確修改（包含 Beta 標籤邏輯）"
else
    echo "❌ Sidebar.js 未找到 Beta 標籤邏輯"
fi

# 檢查 TopHeader.js
if grep -q "REACT_APP_DEPLOY_ENV === 'develop'" frontend/src/components/TopHeader.js 2>/dev/null; then
    echo "✅ TopHeader.js 已正確修改（包含 Beta 標籤邏輯）"
else
    echo "❌ TopHeader.js 未找到 Beta 標籤邏輯"
fi

# 檢查 docker-compose.yml
if grep -q "REACT_APP_DEPLOY_ENV=develop" docker-compose.yml 2>/dev/null; then
    echo "✅ docker-compose.yml 已正確設定環境變數"
else
    echo "❌ docker-compose.yml 未設定 REACT_APP_DEPLOY_ENV"
fi
echo ""

# 5. 總結
echo "=================================="
echo "📊 驗證總結"
echo "=================================="
echo ""

if [ "$DEPLOY_ENV" == "develop" ] && [ "$CONTAINER_STATUS" == "running" ]; then
    echo "🎉 所有檢查通過！"
    echo ""
    echo "📝 接下來請："
    echo "   1. 打開瀏覽器訪問 http://localhost:3000"
    echo "   2. 按 Ctrl+Shift+R 強制刷新"
    echo "   3. 檢查以下位置是否顯示橙色 Beta 標籤："
    echo "      - Sidebar Logo 旁邊: 'AI Assistant [Beta]'"
    echo "      - 每個頁面標題旁邊: '[Beta]'"
    echo ""
    echo "🔧 如果看不到標籤，請執行："
    echo "   docker compose restart react"
    echo "   然後等待 10-20 秒再刷新瀏覽器"
else
    echo "⚠️  部分檢查失敗，請檢查上方輸出"
    echo ""
    echo "🔧 建議執行以下命令修復："
    echo "   docker compose build react"
    echo "   docker compose up -d react"
fi
echo ""
echo "=================================="
