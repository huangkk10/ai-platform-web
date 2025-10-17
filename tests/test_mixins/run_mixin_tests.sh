#!/bin/bash
# ViewSets Mixins 測試運行腳本

echo "🧪 開始運行 ViewSets Mixins 單元測試..."
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查是否在 Docker 容器中
if [ -f /.dockerenv ]; then
    echo "📦 在 Docker 容器中運行"
    PYTHON_CMD="python"
else
    echo "💻 在本地環境運行"
    PYTHON_CMD="docker exec ai-django python"
fi

# 選項
RUN_COVERAGE=false
RUN_VERBOSE=false
TEST_FILE=""

# 解析命令行參數
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage|-c)
            RUN_COVERAGE=true
            shift
            ;;
        --verbose|-v)
            RUN_VERBOSE=true
            shift
            ;;
        --file|-f)
            TEST_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "使用方法: $0 [選項]"
            echo ""
            echo "選項:"
            echo "  -c, --coverage    生成覆蓋率報告"
            echo "  -v, --verbose     詳細輸出"
            echo "  -f, --file FILE   只運行指定的測試文件"
            echo "  -h, --help        顯示此幫助訊息"
            echo ""
            echo "範例:"
            echo "  $0                           # 運行所有測試"
            echo "  $0 -c                        # 運行測試並生成覆蓋率"
            echo "  $0 -f test_library_manager   # 只運行指定測試"
            exit 0
            ;;
        *)
            echo "未知選項: $1"
            echo "使用 --help 查看幫助"
            exit 1
            ;;
    esac
done

# 構建測試命令
if [ "$RUN_COVERAGE" = true ]; then
    TEST_CMD="pytest tests/test_mixins/"
    TEST_CMD="$TEST_CMD --cov=backend/api/views/mixins"
    TEST_CMD="$TEST_CMD --cov-report=html"
    TEST_CMD="$TEST_CMD --cov-report=term-missing"
else
    TEST_CMD="pytest tests/test_mixins/"
fi

# 添加文件過濾
if [ -n "$TEST_FILE" ]; then
    TEST_CMD="$TEST_CMD/${TEST_FILE}.py"
fi

# 添加詳細輸出
if [ "$RUN_VERBOSE" = true ]; then
    TEST_CMD="$TEST_CMD -v"
fi

# 添加顏色和格式
TEST_CMD="$TEST_CMD --tb=short --color=yes -ra"

echo "📋 測試範圍: tests/test_mixins/"
if [ -n "$TEST_FILE" ]; then
    echo "📄 測試文件: ${TEST_FILE}.py"
fi
echo "🔧 覆蓋率報告: $RUN_COVERAGE"
echo ""

# 運行測試
echo "▶️  執行測試命令..."
echo "-----------------------------------"

if [ -f /.dockerenv ]; then
    # 在容器中直接運行
    eval $TEST_CMD
    TEST_RESULT=$?
else
    # 在本地通過 docker exec 運行
    docker exec ai-django bash -c "$TEST_CMD"
    TEST_RESULT=$?
fi

echo "-----------------------------------"
echo ""

# 顯示結果
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ 所有測試通過！${NC}"
else
    echo -e "${RED}❌ 測試失敗！${NC}"
fi

# 顯示覆蓋率報告位置
if [ "$RUN_COVERAGE" = true ] && [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo -e "${YELLOW}📊 覆蓋率報告已生成：${NC}"
    echo "   HTML 報告: htmlcov/index.html"
    echo ""
    echo "   查看報告："
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "   open htmlcov/index.html"
    else
        echo "   xdg-open htmlcov/index.html"
    fi
fi

echo ""
echo "🏁 測試完成"

exit $TEST_RESULT
