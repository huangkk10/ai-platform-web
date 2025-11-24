#!/bin/bash
# Benchmark API 端點測試（使用 curl）

echo "============================================================"
echo "🧪 Benchmark API 端點測試（curl 真實 HTTP 請求）"
echo "============================================================"
echo ""

# 測試計數器
PASSED=0
FAILED=0
TOTAL=0

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 測試函數
test_api() {
    TOTAL=$((TOTAL + 1))
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    local data="${4:-}"
    
    # 執行請求
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "http://localhost$url")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "http://localhost$url")
    fi
    
    # 提取狀態碼
    status_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -n -1)
    
    # 檢查結果
    if [[ "$status_code" == "200" ]] || [[ "$status_code" == "201" ]]; then
        echo -e "${GREEN}✅ $TOTAL. $name${NC} (HTTP $status_code)"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ $TOTAL. $name${NC} (HTTP $status_code)"
        FAILED=$((FAILED + 1))
        # 顯示錯誤訊息（限制 200 字元）
        error_msg=$(echo "$body" | head -c 200)
        if [ ! -z "$error_msg" ]; then
            echo "   錯誤: $error_msg..."
        fi
    fi
}

# ==================== 測試案例 API ====================
echo "📋 測試案例 API (Test Cases)"
echo "------------------------------------------------------------"

test_api "GET /api/benchmark/test-cases/" "/api/benchmark/test-cases/" "GET"
test_api "GET /api/benchmark/test-cases/{id}/" "/api/benchmark/test-cases/1/" "GET"
test_api "GET /api/benchmark/test-cases/statistics/" "/api/benchmark/test-cases/statistics/" "GET"
test_api "GET /api/benchmark/test-cases/?category=資源路徑" "/api/benchmark/test-cases/?category=%E8%B3%87%E6%BA%90%E8%B7%AF%E5%BE%91" "GET"
test_api "GET /api/benchmark/test-cases/?difficulty=easy" "/api/benchmark/test-cases/?difficulty=easy" "GET"

# 創建測試案例
test_api "POST /api/benchmark/test-cases/" "/api/benchmark/test-cases/" "POST" \
    '{"question":"API測試問題","category":"API測試","difficulty_level":"easy","question_type":"測試","knowledge_source":"API","expected_document_ids":[1,2],"min_required_matches":1,"is_active":true}'

# 批量啟用
test_api "POST /api/benchmark/test-cases/bulk_activate/" "/api/benchmark/test-cases/bulk_activate/" "POST" \
    '{"ids":[1,2,3]}'

# 批量停用
test_api "POST /api/benchmark/test-cases/bulk_deactivate/" "/api/benchmark/test-cases/bulk_deactivate/" "POST" \
    '{"ids":[4,5]}'

echo ""

# ==================== 測試執行 API ====================
echo "🚀 測試執行 API (Test Runs)"
echo "------------------------------------------------------------"

test_api "GET /api/benchmark/test-runs/" "/api/benchmark/test-runs/" "GET"
test_api "GET /api/benchmark/test-runs/{id}/" "/api/benchmark/test-runs/1/" "GET"
test_api "GET /api/benchmark/test-runs/?version_id=1" "/api/benchmark/test-runs/?version_id=1" "GET"
test_api "GET /api/benchmark/test-runs/?status=completed" "/api/benchmark/test-runs/?status=completed" "GET"
test_api "GET /api/benchmark/test-runs/{id}/results/" "/api/benchmark/test-runs/4/results/" "GET"

# 啟動測試（簡化版，只測 2 題）
echo "   🔄 啟動新測試（這可能需要幾秒鐘）..."
test_api "POST /api/benchmark/test-runs/start_test/" "/api/benchmark/test-runs/start_test/" "POST" \
    '{"version_id":3,"run_name":"API 測試","run_type":"manual","limit":2,"notes":"API 端點測試"}'

# 比較測試執行
test_api "POST /api/benchmark/test-runs/compare/" "/api/benchmark/test-runs/compare/" "POST" \
    '{"run_id_1":3,"run_id_2":4}'

echo ""

# ==================== 測試結果 API ====================
echo "📊 測試結果 API (Test Results)"
echo "------------------------------------------------------------"

test_api "GET /api/benchmark/test-results/" "/api/benchmark/test-results/" "GET"
test_api "GET /api/benchmark/test-results/{id}/" "/api/benchmark/test-results/1/" "GET"
test_api "GET /api/benchmark/test-results/?test_run_id=4" "/api/benchmark/test-results/?test_run_id=4" "GET"
test_api "GET /api/benchmark/test-results/?is_passed=true" "/api/benchmark/test-results/?is_passed=true" "GET"
test_api "GET /api/benchmark/test-results/failed_cases/" "/api/benchmark/test-results/failed_cases/" "GET"

echo ""

# ==================== 版本 API ====================
echo "🔖 版本 API (Versions)"
echo "------------------------------------------------------------"

test_api "GET /api/benchmark/versions/" "/api/benchmark/versions/" "GET"
test_api "GET /api/benchmark/versions/{id}/" "/api/benchmark/versions/3/" "GET"

# 創建新版本
test_api "POST /api/benchmark/versions/" "/api/benchmark/versions/" "POST" \
    '{"version_name":"API 測試版本","version_code":"v-api-test-'$(date +%s)'","description":"API 端點測試","algorithm_type":"hybrid","is_active":true}'

# 設定為基準版本
test_api "POST /api/benchmark/versions/{id}/set_as_baseline/" "/api/benchmark/versions/3/set_as_baseline/" "POST" "{}"

test_api "GET /api/benchmark/versions/baseline/" "/api/benchmark/versions/baseline/" "GET"
test_api "GET /api/benchmark/versions/{id}/test_history/" "/api/benchmark/versions/3/test_history/" "GET"

echo ""

# ==================== 總結 ====================
echo "============================================================"
echo "📊 測試總結"
echo "============================================================"
echo "總測試數: $TOTAL"
echo -e "${GREEN}✅ 通過: $PASSED ($(echo "scale=1; $PASSED * 100 / $TOTAL" | bc)%)${NC}"
echo -e "${RED}❌ 失敗: $FAILED ($(echo "scale=1; $FAILED * 100 / $TOTAL" | bc)%)${NC}"
echo "============================================================"

# 顯示資料庫狀態
echo ""
echo "============================================================"
echo "📈 資料庫狀態"
echo "============================================================"
docker exec ai-django python << 'PYEOF'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()
from api.models import *

print(f"測試案例總數: {BenchmarkTestCase.objects.count()}")
print(f"  - 啟用: {BenchmarkTestCase.objects.filter(is_active=True).count()}")
print(f"  - 停用: {BenchmarkTestCase.objects.filter(is_active=False).count()}")
print(f"測試執行總數: {BenchmarkTestRun.objects.count()}")
print(f"  - 完成: {BenchmarkTestRun.objects.filter(status='completed').count()}")
print(f"測試結果總數: {BenchmarkTestResult.objects.count()}")
print(f"  - 通過: {BenchmarkTestResult.objects.filter(is_passed=True).count()}")
print(f"  - 失敗: {BenchmarkTestResult.objects.filter(is_passed=False).count()}")
print(f"版本總數: {SearchAlgorithmVersion.objects.count()}")
print(f"  - 基準版本: {SearchAlgorithmVersion.objects.filter(is_baseline=True).count()}")
PYEOF
echo "============================================================"

# 返回測試結果
if [ $FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
