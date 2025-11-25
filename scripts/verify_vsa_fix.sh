#!/bin/bash
# VSA 測試案例修復驗證腳本

echo "=========================================="
echo "VSA 測試案例修復驗證"
echo "=========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "1. 檢查 Django 容器狀態..."
if docker ps | grep -q ai-django; then
    echo -e "${GREEN}✅ Django 容器運行中${NC}"
else
    echo -e "${RED}❌ Django 容器未運行${NC}"
    exit 1
fi

echo ""
echo "2. 檢查資料庫中的測試案例數量..."
DB_COUNT=$(docker exec postgres_db psql -U postgres -d ai_platform -t -c "SELECT COUNT(*) FROM dify_benchmark_test_case WHERE is_active = true;" | tr -d ' ')

if [ "$DB_COUNT" -eq 55 ]; then
    echo -e "${GREEN}✅ 資料庫中有 $DB_COUNT 筆測試案例（預期 55 筆）${NC}"
else
    echo -e "${YELLOW}⚠️  資料庫中有 $DB_COUNT 筆測試案例（預期 55 筆）${NC}"
fi

echo ""
echo "3. 檢查測試案例分類分布..."
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    test_class_name as \"分類\",
    COUNT(*) as \"數量\"
FROM dify_benchmark_test_case 
WHERE is_active = true
GROUP BY test_class_name 
ORDER BY test_class_name;
" | head -n 20

echo ""
echo "4. 驗證完成！"
echo ""
echo "=========================================="
echo "後續步驟："
echo "=========================================="
echo "1. 重新整理瀏覽器（清除快取）"
echo "   - Chrome/Edge: Ctrl + Shift + R"
echo "   - Mac: Cmd + Shift + R"
echo ""
echo "2. 進入 VSA 測試案例頁面"
echo "   http://localhost/dify-benchmark/test-cases"
echo ""
echo "3. 確認顯示："
echo "   - 總測試案例：55"
echo "   - 啟用中：55"
echo "   - 表格中顯示所有 55 筆資料"
echo ""
echo "4. 檢查瀏覽器開發者工具 Network 面板"
echo "   - API 回應應該是陣列格式（非分頁物件）"
echo "   - 回應應包含 55 個元素"
echo "=========================================="
