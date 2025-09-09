#!/bin/bash

# AI Platform Web 應用監控腳本
# 專門監控前後端整合的 Web 應用狀態

cd "$(dirname "$0")/.."

show_header() {
    echo "============================================"
    echo "  🌐 AI Platform Web 應用監控"
    echo "  時間: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================"
}

check_frontend() {
    echo "🎨 Frontend (React) 狀態檢查:"
    
    # 檢查主頁
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost)
    time=$(curl -s -o /dev/null -w "%{time_total}" http://localhost)
    
    if [ "$status" = "200" ]; then
        echo "✅ 主頁載入成功 - HTTP $status (${time}s)"
        
        # 檢查是否有 React 內容
        if curl -s http://localhost | grep -q "AI Platform"; then
            echo "✅ React 應用內容正常"
        else
            echo "❌ React 應用內容異常"
        fi
        
        # 檢查靜態資源
        if curl -s http://localhost | grep -q "bundle.js"; then
            echo "✅ JavaScript 資源已載入"
        else
            echo "⚠️  JavaScript 資源可能有問題"
        fi
    else
        echo "❌ 主頁載入失敗 - HTTP $status"
    fi
}

check_backend() {
    echo -e "\n🔧 Backend (Django) 狀態檢查:"
    
    # 檢查 API 根目錄
    api_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/)
    api_time=$(curl -s -o /dev/null -w "%{time_total}" http://localhost/api/)
    
    if [ "$api_status" = "403" ]; then
        echo "✅ API 服務正常運行 - HTTP $api_status (${api_time}s)"
        echo "   (403 = 需要認證，這是正常的)"
    elif [ "$api_status" = "200" ]; then
        echo "✅ API 服務正常運行 - HTTP $api_status (${api_time}s)"
    else
        echo "❌ API 服務異常 - HTTP $api_status"
    fi
    
    # 檢查 Django Admin
    admin_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/admin/)
    admin_time=$(curl -s -o /dev/null -w "%{time_total}" http://localhost/admin/)
    
    if [ "$admin_status" = "302" ]; then
        echo "✅ Django Admin 正常 - HTTP $admin_status (${admin_time}s)"
        echo "   (302 = 重定向到登入頁，這是正常的)"
    else
        echo "❌ Django Admin 異常 - HTTP $admin_status"
    fi
}

check_integration() {
    echo -e "\n🔗 前後端整合狀態:"
    
    # 檢查前端是否能顯示後端狀態
    if curl -s http://localhost | grep -q "System Status"; then
        echo "✅ 前端包含系統狀態組件"
    else
        echo "❌ 前端缺少系統狀態組件"
    fi
    
    # 檢查 CORS 和代理設定
    cors_check=$(curl -s -H "Origin: http://localhost:3000" http://localhost/api/ -w "%{http_code}" -o /dev/null)
    if [ "$cors_check" = "403" ] || [ "$cors_check" = "200" ]; then
        echo "✅ CORS/代理設定正常"
    else
        echo "❌ CORS/代理設定可能有問題"
    fi
}

check_database_connection() {
    echo -e "\n🗄️  資料庫連接狀態:"
    
    # 透過 Django 檢查資料庫
    db_check=$(docker exec ai-django python manage.py check --database default 2>&1)
    if echo "$db_check" | grep -q "System check identified no issues"; then
        echo "✅ 資料庫連接正常"
    else
        echo "❌ 資料庫連接可能有問題"
        echo "   詳細: $db_check"
    fi
}

show_performance() {
    echo -e "\n⚡ 效能指標:"
    
    # 整體載入時間
    total_time=$(curl -s -w "%{time_total}" -o /dev/null http://localhost)
    echo "🎯 主頁完整載入時間: ${total_time}s"
    
    # API 回應時間
    api_time=$(curl -s -w "%{time_total}" -o /dev/null http://localhost/api/)
    echo "🔗 API 回應時間: ${api_time}s"
    
    # 容器資源使用
    echo "💻 關鍵容器資源使用:"
    docker stats --no-stream --format "   {{.Name}}: CPU {{.CPUPerc}} | MEM {{.MemPerc}}" ai-django ai-react ai-nginx
}

show_user_access_info() {
    echo -e "\n📍 用戶訪問資訊:"
    echo "🌐 主要網站: http://localhost"
    echo "🔧 API 文檔: http://localhost/api/"
    echo "👨‍💼 管理後台: http://localhost/admin/"
    echo "📊 資料庫管理: http://localhost:9090"
    echo "🐳 容器管理: http://localhost:9000"
}

# 執行所有檢查
show_header
check_frontend
check_backend
check_integration
check_database_connection
show_performance
show_user_access_info

echo -e "\n============================================"
echo "💡 提示: 如果發現問題，請檢查 docker logs 或聯繫系統管理員"
echo "============================================"