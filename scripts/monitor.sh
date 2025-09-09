#!/bin/bash

# AI Platform 監控腳本
# 用法: ./scripts/monitor.sh [logs|stats|health|all]

cd "$(dirname "$0")/.."

show_header() {
    echo "============================================"
    echo "  AI Platform 監控中心"
    echo "  時間: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================"
}

show_container_status() {
    echo -e "\n📊 容器運行狀態:"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
}

show_resource_usage() {
    echo -e "\n💻 資源使用情況:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}"
}

show_service_health() {
    echo -e "\n🌐 服務健康檢查:"
    
    services=(
        "前端 (React):http://localhost"
        "API 端點:http://localhost/api/"
        "Django Admin:http://localhost/admin/"
        "Adminer:http://localhost:9090"
        "Portainer:http://localhost:9000"
    )
    
    for service in "${services[@]}"; do
        name=$(echo $service | cut -d: -f1)
        url=$(echo $service | cut -d: -f2,3)
        
        status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
        response_time=$(curl -s -o /dev/null -w "%{time_total}" "$url" 2>/dev/null)
        
        if [[ $status_code =~ ^[2-3][0-9][0-9]$ ]]; then
            echo "✅ $name - HTTP $status_code (${response_time}s)"
        else
            echo "❌ $name - HTTP $status_code (${response_time}s)"
        fi
    done
}

show_logs() {
    echo -e "\n📋 最新服務日誌:"
    echo "--- Django ---"
    docker logs --tail 5 ai-django 2>/dev/null | tail -3
    echo "--- Nginx ---"
    docker logs --tail 3 ai-nginx 2>/dev/null | tail -2
    echo "--- PostgreSQL ---"
    docker logs --tail 3 postgres_db 2>/dev/null | tail -2
}

case "${1:-all}" in
    "logs")
        show_header
        show_logs
        ;;
    "stats")
        show_header
        show_resource_usage
        ;;
    "health")
        show_header
        show_service_health
        ;;
    "all")
        show_header
        show_container_status
        show_service_health
        show_resource_usage
        show_logs
        ;;
    *)
        echo "用法: $0 [logs|stats|health|all]"
        echo "  logs   - 顯示服務日誌"
        echo "  stats  - 顯示資源使用情況"
        echo "  health - 顯示服務健康狀態"
        echo "  all    - 顯示所有資訊 (預設)"
        exit 1
        ;;
esac

echo -e "\n============================================"