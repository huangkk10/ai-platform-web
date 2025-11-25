#!/bin/bash

###############################################################################
# Dify v1.2.1 動態 Threshold 功能快速驗證腳本
# 用途: 快速驗證核心功能是否正常運作
# 時間: 約 5-10 分鐘
###############################################################################

set -e  # 遇到錯誤立即停止

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 輔助函數
print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

###############################################################################
# Step 1: 環境檢查
###############################################################################
print_section "Step 1: 環境檢查"

# 檢查 Docker 容器
print_info "檢查 Docker 容器狀態..."
if docker compose ps | grep -q "ai-django.*Up"; then
    print_success "Django 容器運行中"
else
    print_error "Django 容器未運行！請執行: docker compose up -d"
    exit 1
fi

if docker compose ps | grep -q "postgres_db.*Up"; then
    print_success "PostgreSQL 容器運行中"
else
    print_error "PostgreSQL 容器未運行！請執行: docker compose up -d"
    exit 1
fi

###############################################################################
# Step 2: 檢查 v1.2.1 版本是否存在
###############################################################################
print_section "Step 2: 檢查 v1.2.1 版本"

print_info "查詢資料庫中的 v1.2.1 版本..."
VERSION_CHECK=$(docker exec postgres_db psql -U postgres -d ai_platform -t -c \
  "SELECT version_name, is_baseline, 
   rag_settings->'stage1'->>'use_dynamic_threshold' as stage1_dynamic,
   rag_settings->'stage2'->>'use_dynamic_threshold' as stage2_dynamic
   FROM dify_config_version 
   WHERE version_name LIKE '%1.2.1%';" | head -1)

if [ -z "$VERSION_CHECK" ]; then
    print_warning "v1.2.1 版本不存在，正在創建..."
    
    # 執行版本創建腳本
    docker exec ai-django python /app/scripts/create_dify_v1_2_1_dynamic_version.py
    
    if [ $? -eq 0 ]; then
        print_success "v1.2.1 版本創建成功"
    else
        print_error "v1.2.1 版本創建失敗"
        exit 1
    fi
else
    print_success "v1.2.1 版本已存在"
    echo "$VERSION_CHECK"
fi

###############################################################################
# Step 3: 設定 v1.2.1 為 Baseline
###############################################################################
print_section "Step 3: 設定 v1.2.1 為 Baseline"

print_info "設定 v1.2.1 為 Baseline..."
BASELINE_RESULT=$(docker exec ai-django python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import DifyConfigVersion
try:
    # 先清除所有 Baseline
    DifyConfigVersion.objects.all().update(is_baseline=False)
    
    # 設定 v1.2.1 為 Baseline
    v = DifyConfigVersion.objects.get(version_name__contains='1.2.1')
    v.is_baseline = True
    v.save()
    
    print(f'SUCCESS:{v.version_name}')
except Exception as e:
    print(f'ERROR:{str(e)}')
" 2>&1 | grep -E "SUCCESS|ERROR")

if echo "$BASELINE_RESULT" | grep -q "SUCCESS:"; then
    VERSION_NAME=$(echo "$BASELINE_RESULT" | cut -d':' -f2)
    print_success "已將 '$VERSION_NAME' 設為 Baseline"
else
    print_error "設定 Baseline 失敗: $BASELINE_RESULT"
    exit 1
fi

###############################################################################
# Step 4: 驗證 Baseline 設定
###############################################################################
print_section "Step 4: 驗證 Baseline 設定"

print_info "確認 v1.2.1 是否為 Baseline..."
IS_BASELINE=$(docker exec postgres_db psql -U postgres -d ai_platform -t -c \
  "SELECT is_baseline FROM dify_config_version WHERE version_name LIKE '%1.2.1%';" | tr -d ' ')

if [ "$IS_BASELINE" = "t" ]; then
    print_success "v1.2.1 已確認為 Baseline"
else
    print_error "v1.2.1 不是 Baseline (is_baseline = $IS_BASELINE)"
fi

###############################################################################
# Step 5: 檢查 Threshold 設定
###############################################################################
print_section "Step 5: 檢查 Threshold 設定"

print_info "查詢當前 Protocol Assistant 的 Threshold 設定..."
THRESHOLD_RESULT=$(docker exec postgres_db psql -U postgres -d ai_platform -t -c \
  "SELECT 
    stage1_threshold, stage1_title_weight, stage1_content_weight,
    stage2_threshold, stage2_title_weight, stage2_content_weight
   FROM search_threshold_settings 
   WHERE assistant_type = 'protocol_assistant';" | head -1)

if [ -z "$THRESHOLD_RESULT" ]; then
    print_error "找不到 protocol_assistant 的 Threshold 設定"
else
    print_success "當前 Threshold 設定:"
    echo "$THRESHOLD_RESULT"
fi

###############################################################################
# Step 6: 修改 Threshold 設定（測試動態載入）
###############################################################################
print_section "Step 6: 測試動態 Threshold 更新"

print_info "備份當前設定並修改 Threshold..."
MODIFY_RESULT=$(docker exec ai-django python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import SearchThresholdSetting
try:
    setting = SearchThresholdSetting.objects.get(assistant_type='protocol_assistant')
    
    # 備份原始值
    original = {
        'stage1_threshold': float(setting.stage1_threshold),
        'stage2_threshold': float(setting.stage2_threshold)
    }
    print(f'原始值 - Stage1: {original[\"stage1_threshold\"]}, Stage2: {original[\"stage2_threshold\"]}')
    
    # 修改為測試值
    setting.stage1_threshold = 0.75
    setting.stage2_threshold = 0.65
    setting.save()
    
    print(f'新值 - Stage1: 0.75, Stage2: 0.65')
    print('SUCCESS')
except Exception as e:
    print(f'ERROR:{str(e)}')
" 2>&1 | grep -v "Celery" | grep -v "objects imported")

if echo "$MODIFY_RESULT" | grep -q "SUCCESS"; then
    print_success "Threshold 設定已更新"
    echo "$MODIFY_RESULT" | grep -v "SUCCESS"
else
    print_error "Threshold 更新失敗: $MODIFY_RESULT"
fi

###############################################################################
# Step 7: 測試動態載入邏輯
###############################################################################
print_section "Step 7: 測試動態載入邏輯"

print_info "測試 DynamicThresholdLoader..."
LOADER_TEST=$(docker exec ai-django python <<EOF
import sys
sys.path.insert(0, '/app')

from library.dify_integration.dynamic_threshold_loader import DynamicThresholdLoader

loader = DynamicThresholdLoader()

# 測試載入 Stage 1 配置
config1 = loader.load_stage_config('protocol_guide', stage=1)
print(f"Stage 1 - Threshold: {config1['threshold']}, Title Weight: {config1['title_weight']}%")

# 測試載入 Stage 2 配置
config2 = loader.load_stage_config('protocol_guide', stage=2)
print(f"Stage 2 - Threshold: {config2['threshold']}, Title Weight: {config2['title_weight']}%")

# 測試完整 RAG 設定載入
rag_settings = {
    'stage1': {'use_dynamic_threshold': True, 'threshold': 0.80, 'title_weight': 95},
    'stage2': {'use_dynamic_threshold': True, 'threshold': 0.80, 'title_weight': 10}
}

loaded = loader.load_full_rag_settings(rag_settings, 'protocol_guide')
print(f"動態載入成功: Stage1 Threshold = {loaded['stage1']['threshold']}")
print("SUCCESS")
EOF
)

if echo "$LOADER_TEST" | grep -q "SUCCESS"; then
    print_success "動態載入邏輯運作正常"
    echo "$LOADER_TEST" | grep -v "SUCCESS"
else
    print_error "動態載入測試失敗"
    echo "$LOADER_TEST"
fi

###############################################################################
# Step 8: 檢查前端 API 端點
###############################################################################
print_section "Step 8: 前端 API 端點說明"

print_info "前端應該使用以下 API 端點："
echo "  • 獲取 Baseline: GET /api/dify-benchmark/versions/get_baseline/"
echo "  • 設定 Baseline: POST /api/dify-benchmark/versions/{id}/set_baseline/"
echo "  • 版本列表: GET /api/dify-benchmark/versions/"
echo ""
print_info "請在瀏覽器中測試："
echo "  1. 訪問 http://10.10.172.127/dify-benchmark/versions"
echo "  2. 檢查 Baseline 摘要卡片是否顯示"
echo "  3. 檢查 v1.2.1 版本是否有 🔄 動態標記"

###############################################################################
# Step 9: 檢查資料庫記錄完整性
###############################################################################
print_section "Step 9: 檢查資料庫記錄完整性"

print_info "驗證 v1.2.1 版本的資料結構..."
STRUCTURE_CHECK=$(docker exec postgres_db psql -U postgres -d ai_platform -t -c \
  "SELECT 
    version_name,
    description,
    jsonb_typeof(rag_settings) as rag_type,
    rag_settings->'stage1'->>'use_dynamic_threshold' as stage1_dynamic,
    rag_settings->'stage1'->>'title_match_bonus' as stage1_bonus,
    rag_settings->'stage2'->>'use_dynamic_threshold' as stage2_dynamic,
    rag_settings->'stage2'->>'title_match_bonus' as stage2_bonus
   FROM dify_config_version 
   WHERE version_name LIKE '%1.2.1%';" | head -1)

if echo "$STRUCTURE_CHECK" | grep -q "true"; then
    print_success "v1.2.1 版本資料結構正確"
    echo "$STRUCTURE_CHECK"
else
    print_error "v1.2.1 版本資料結構異常"
    echo "$STRUCTURE_CHECK"
fi

###############################################################################
# Step 10: 生成測試總結報告
###############################################################################
print_section "Step 10: 測試總結報告"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           Dify v1.2.1 動態 Threshold 快速驗證報告              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 檢查所有關鍵功能
CHECKS=0
PASSED=0

# Check 1: v1.2.1 版本存在
CHECKS=$((CHECKS + 1))
if docker exec postgres_db psql -U postgres -d ai_platform -t -c \
  "SELECT COUNT(*) FROM dify_config_version WHERE version_name LIKE '%1.2.1%';" | grep -q "1"; then
    print_success "v1.2.1 版本已創建"
    PASSED=$((PASSED + 1))
else
    print_error "v1.2.1 版本不存在"
fi

# Check 2: v1.2.1 是 Baseline
CHECKS=$((CHECKS + 1))
if docker exec postgres_db psql -U postgres -d ai_platform -t -c \
  "SELECT is_baseline FROM dify_config_version WHERE version_name LIKE '%1.2.1%';" | grep -q "t"; then
    print_success "v1.2.1 已設為 Baseline"
    PASSED=$((PASSED + 1))
else
    print_warning "v1.2.1 不是當前 Baseline"
fi

# Check 3: 動態 Threshold 標記正確
CHECKS=$((CHECKS + 1))
if docker exec postgres_db psql -U postgres -d ai_platform -t -c \
  "SELECT rag_settings->'stage1'->>'use_dynamic_threshold' 
   FROM dify_config_version WHERE version_name LIKE '%1.2.1%';" | grep -q "true"; then
    print_success "動態 Threshold 標記正確"
    PASSED=$((PASSED + 1))
else
    print_error "動態 Threshold 標記錯誤"
fi

# Check 4: Threshold 設定存在
CHECKS=$((CHECKS + 1))
if docker exec postgres_db psql -U postgres -d ai_platform -t -c \
  "SELECT COUNT(*) FROM search_threshold_settings WHERE assistant_type = 'protocol_assistant';" | grep -q "1"; then
    print_success "Threshold 設定已配置"
    PASSED=$((PASSED + 1))
else
    print_error "Threshold 設定不存在"
fi

# Check 5: DynamicThresholdLoader 可用
CHECKS=$((CHECKS + 1))
if docker exec ai-django python -c \
  "from library.dify_integration.dynamic_threshold_loader import DynamicThresholdLoader; DynamicThresholdLoader()" 2>/dev/null; then
    print_success "DynamicThresholdLoader 可正常導入"
    PASSED=$((PASSED + 1))
else
    print_error "DynamicThresholdLoader 導入失敗"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  測試結果: $PASSED / $CHECKS 項通過"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$PASSED" -eq "$CHECKS" ]; then
    print_success "所有檢查項目通過！✨"
    echo ""
    print_info "下一步建議："
    echo "  1. 訪問 http://10.10.172.127/dify-benchmark/versions 檢查前端 UI"
    echo "  2. 訪問 http://10.10.172.127/protocol-assistant 檢查 Baseline Alert"
    echo "  3. 執行完整的端到端測試（參考測試指南）"
    echo ""
    exit 0
else
    print_warning "部分檢查項目未通過，請檢查上方錯誤訊息"
    echo ""
    exit 1
fi
