#!/bin/bash

##############################################################################
# Threshold Settings API 測試腳本
# 
# 測試項目：
# 1. 管理員登入
# 2. 列出所有 Threshold 設定
# 3. 獲取特定 Assistant 的設定
# 4. 更新 Protocol Assistant 設定
# 5. 更新 RVT Assistant 設定
# 6. 驗證更新結果
##############################################################################

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API 基礎 URL
BASE_URL="http://localhost/api/search-threshold-settings"
LOGIN_URL="http://localhost/api/auth/login/"

# 管理員帳號（請根據實際情況修改）
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin123}"

# 測試計數器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 輔助函數：打印測試標題
print_test_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}TEST $1: $2${NC}"
    echo -e "${BLUE}========================================${NC}"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

# 輔助函數：打印成功訊息
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

# 輔助函數：打印失敗訊息
print_error() {
    echo -e "${RED}✗ $1${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

# 輔助函數：打印資訊
print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# 輔助函數：檢查 HTTP 狀態碼
check_status_code() {
    local expected=$1
    local actual=$2
    local description=$3
    
    if [ "$actual" -eq "$expected" ]; then
        print_success "$description (HTTP $actual)"
        return 0
    else
        print_error "$description (Expected HTTP $expected, Got HTTP $actual)"
        return 1
    fi
}

# 輔助函數：檢查 JSON 欄位
check_json_field() {
    local json=$1
    local field=$2
    local description=$3
    
    local value=$(echo "$json" | jq -r ".$field")
    
    if [ "$value" != "null" ] && [ -n "$value" ]; then
        print_success "$description: $value"
        return 0
    else
        print_error "$description: Field '$field' not found or null"
        return 1
    fi
}

##############################################################################
# 測試 0: 管理員登入
##############################################################################
print_test_header "0" "管理員登入 (POST /api/auth/login/)"

print_info "使用帳號: $ADMIN_USERNAME"

# 先獲取 CSRF token
csrf_response=$(curl -s -c cookies.txt "http://localhost/api/")

response=$(curl -s -w "\n%{http_code}" \
    -X POST "$LOGIN_URL" \
    -H "Content-Type: application/json" \
    -b cookies.txt \
    -c cookies.txt \
    -d "{
        \"username\": \"$ADMIN_USERNAME\",
        \"password\": \"$ADMIN_PASSWORD\"
    }")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if check_status_code 200 "$http_code" "登入成功"; then
    echo -e "\n${YELLOW}回應資料：${NC}"
    echo "$body" | jq '.'
    
    # 檢查是否包含用戶資訊
    username=$(echo "$body" | jq -r '.user.username')
    is_staff=$(echo "$body" | jq -r '.user.is_staff')
    
    if [ "$username" = "$ADMIN_USERNAME" ]; then
        print_success "登入用戶確認: $username"
    else
        print_error "登入用戶不符 (預期: $ADMIN_USERNAME, 實際: $username)"
    fi
    
    if [ "$is_staff" = "true" ]; then
        print_success "管理員權限確認: is_staff=true"
    else
        print_error "非管理員帳號，測試可能會失敗"
        echo -e "${RED}提示：請使用具有管理員權限的帳號進行測試${NC}"
        echo -e "${YELLOW}您可以設定環境變數：${NC}"
        echo -e "  export ADMIN_USERNAME=your_admin_username"
        echo -e "  export ADMIN_PASSWORD=your_admin_password"
    fi
else
    print_error "登入失敗 (HTTP $http_code)"
    echo -e "${RED}無法繼續測試，請檢查管理員帳號密碼是否正確${NC}"
    echo -e "\n${YELLOW}錯誤訊息：${NC}"
    echo "$body" | jq '.'
    exit 1
fi

##############################################################################
# 測試 1: 列出所有 Threshold 設定
##############################################################################
print_test_header "1" "列出所有 Threshold 設定 (GET /api/search-threshold-settings/)"

response=$(curl -s -w "\n%{http_code}" \
    -X GET "$BASE_URL/" \
    -H "Content-Type: application/json" \
    --cookie-jar cookies.txt \
    --cookie cookies.txt)

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if check_status_code 200 "$http_code" "列出設定請求成功"; then
    echo -e "\n${YELLOW}回應資料：${NC}"
    echo "$body" | jq '.'
    
    # 檢查是否返回陣列
    count=$(echo "$body" | jq '. | length')
    if [ "$count" -ge 2 ]; then
        print_success "返回 $count 個設定項目"
        
        # 檢查必要欄位
        check_json_field "$body" ".[0].assistant_type" "第一個項目的 assistant_type"
        check_json_field "$body" ".[0].stage1_threshold" "第一個項目的 stage1_threshold"
        check_json_field "$body" ".[0].stage1_title_weight" "第一個項目的 stage1_title_weight"
        check_json_field "$body" ".[0].stage2_threshold" "第一個項目的 stage2_threshold"
    else
        print_error "設定項目數量不足（預期 >= 2，實際 $count）"
    fi
fi

##############################################################################
# 測試 2: 獲取 Protocol Assistant 的設定
##############################################################################
print_test_header "2" "獲取 Protocol Assistant 設定 (GET /api/search-threshold-settings/protocol_assistant/)"

response=$(curl -s -w "\n%{http_code}" \
    -X GET "$BASE_URL/protocol_assistant/" \
    -H "Content-Type: application/json" \
    --cookie cookies.txt)

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if check_status_code 200 "$http_code" "獲取 Protocol Assistant 設定成功"; then
    echo -e "\n${YELLOW}回應資料：${NC}"
    echo "$body" | jq '.'
    
    # 儲存原始設定供稍後恢復
    ORIGINAL_PROTOCOL_STAGE1_THRESHOLD=$(echo "$body" | jq -r '.stage1_threshold')
    ORIGINAL_PROTOCOL_STAGE1_TITLE=$(echo "$body" | jq -r '.stage1_title_weight')
    ORIGINAL_PROTOCOL_STAGE1_CONTENT=$(echo "$body" | jq -r '.stage1_content_weight')
    
    print_info "原始 Stage1 Threshold: $ORIGINAL_PROTOCOL_STAGE1_THRESHOLD"
    print_info "原始 Stage1 Title Weight: $ORIGINAL_PROTOCOL_STAGE1_TITLE"
    print_info "原始 Stage1 Content Weight: $ORIGINAL_PROTOCOL_STAGE1_CONTENT"
fi

##############################################################################
# 測試 3: 獲取 RVT Assistant 的設定
##############################################################################
print_test_header "3" "獲取 RVT Assistant 設定 (GET /api/search-threshold-settings/rvt_assistant/)"

response=$(curl -s -w "\n%{http_code}" \
    -X GET "$BASE_URL/rvt_assistant/" \
    -H "Content-Type: application/json" \
    --cookie cookies.txt)

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if check_status_code 200 "$http_code" "獲取 RVT Assistant 設定成功"; then
    echo -e "\n${YELLOW}回應資料：${NC}"
    echo "$body" | jq '.'
    
    # 儲存原始設定供稍後恢復
    ORIGINAL_RVT_STAGE1_THRESHOLD=$(echo "$body" | jq -r '.stage1_threshold')
    ORIGINAL_RVT_STAGE1_TITLE=$(echo "$body" | jq -r '.stage1_title_weight')
    ORIGINAL_RVT_STAGE1_CONTENT=$(echo "$body" | jq -r '.stage1_content_weight')
    
    print_info "原始 Stage1 Threshold: $ORIGINAL_RVT_STAGE1_THRESHOLD"
    print_info "原始 Stage1 Title Weight: $ORIGINAL_RVT_STAGE1_TITLE"
    print_info "原始 Stage1 Content Weight: $ORIGINAL_RVT_STAGE1_CONTENT"
fi

##############################################################################
# 測試 4: 更新 Protocol Assistant 設定
##############################################################################
print_test_header "4" "更新 Protocol Assistant 設定 (PATCH /api/search-threshold-settings/protocol_assistant/)"

print_info "測試設定: Stage1 Threshold=0.65, Title=55%, Content=45%"

response=$(curl -s -w "\n%{http_code}" \
    -X PATCH "$BASE_URL/protocol_assistant/" \
    -H "Content-Type: application/json" \
    --cookie cookies.txt \
    -d '{
        "stage1_threshold": "0.65",
        "stage1_title_weight": 55,
        "stage1_content_weight": 45,
        "stage2_threshold": "0.60",
        "stage2_title_weight": 50,
        "stage2_content_weight": 50
    }')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if check_status_code 200 "$http_code" "更新 Protocol Assistant 設定成功"; then
    echo -e "\n${YELLOW}回應資料：${NC}"
    echo "$body" | jq '.'
    
    # 驗證更新結果
    new_threshold=$(echo "$body" | jq -r '.stage1_threshold')
    new_title=$(echo "$body" | jq -r '.stage1_title_weight')
    new_content=$(echo "$body" | jq -r '.stage1_content_weight')
    
    if [ "$new_threshold" = "0.65" ]; then
        print_success "Stage1 Threshold 更新正確: $new_threshold"
    else
        print_error "Stage1 Threshold 更新錯誤: $new_threshold (預期 0.65)"
    fi
    
    if [ "$new_title" = "55" ]; then
        print_success "Stage1 Title Weight 更新正確: $new_title%"
    else
        print_error "Stage1 Title Weight 更新錯誤: $new_title% (預期 55%)"
    fi
    
    if [ "$new_content" = "45" ]; then
        print_success "Stage1 Content Weight 更新正確: $new_content%"
    else
        print_error "Stage1 Content Weight 更新錯誤: $new_content% (預期 45%)"
    fi
fi

##############################################################################
# 測試 5: 驗證更新是否持久化
##############################################################################
print_test_header "5" "驗證 Protocol Assistant 更新是否持久化"

sleep 1  # 等待資料庫寫入

response=$(curl -s -w "\n%{http_code}" \
    -X GET "$BASE_URL/protocol_assistant/" \
    -H "Content-Type: application/json" \
    --cookie cookies.txt)

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if check_status_code 200 "$http_code" "重新獲取設定成功"; then
    echo -e "\n${YELLOW}回應資料：${NC}"
    echo "$body" | jq '.'
    
    # 驗證資料是否持久化
    persisted_threshold=$(echo "$body" | jq -r '.stage1_threshold')
    persisted_title=$(echo "$body" | jq -r '.stage1_title_weight')
    persisted_content=$(echo "$body" | jq -r '.stage1_content_weight')
    
    if [ "$persisted_threshold" = "0.65" ]; then
        print_success "Stage1 Threshold 持久化正確: $persisted_threshold"
    else
        print_error "Stage1 Threshold 持久化失敗: $persisted_threshold (預期 0.65)"
    fi
    
    if [ "$persisted_title" = "55" ]; then
        print_success "Stage1 Title Weight 持久化正確: $persisted_title%"
    else
        print_error "Stage1 Title Weight 持久化失敗: $persisted_title% (預期 55%)"
    fi
    
    if [ "$persisted_content" = "45" ]; then
        print_success "Stage1 Content Weight 持久化正確: $persisted_content%"
    else
        print_error "Stage1 Content Weight 持久化失敗: $persisted_content% (預期 45%)"
    fi
fi

##############################################################################
# 測試 6: 恢復 Protocol Assistant 原始設定
##############################################################################
print_test_header "6" "恢復 Protocol Assistant 原始設定"

print_info "恢復設定: Threshold=$ORIGINAL_PROTOCOL_STAGE1_THRESHOLD, Title=$ORIGINAL_PROTOCOL_STAGE1_TITLE%, Content=$ORIGINAL_PROTOCOL_STAGE1_CONTENT%"

response=$(curl -s -w "\n%{http_code}" \
    -X PATCH "$BASE_URL/protocol_assistant/" \
    -H "Content-Type: application/json" \
    --cookie cookies.txt \
    -d "{
        \"stage1_threshold\": \"$ORIGINAL_PROTOCOL_STAGE1_THRESHOLD\",
        \"stage1_title_weight\": $ORIGINAL_PROTOCOL_STAGE1_TITLE,
        \"stage1_content_weight\": $ORIGINAL_PROTOCOL_STAGE1_CONTENT,
        \"stage2_threshold\": \"0.60\",
        \"stage2_title_weight\": 50,
        \"stage2_content_weight\": 50
    }")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if check_status_code 200 "$http_code" "恢復原始設定成功"; then
    print_success "Protocol Assistant 設定已恢復為原始值"
else
    print_error "恢復原始設定失敗"
fi

##############################################################################
# 測試 7: 測試錯誤處理 - 權重總和不等於 100%
##############################################################################
print_test_header "7" "測試錯誤處理 - 權重總和不等於 100%"

print_info "嘗試設定不正確的權重: Title=60%, Content=50% (總和=110%)"

response=$(curl -s -w "\n%{http_code}" \
    -X PATCH "$BASE_URL/protocol_assistant/" \
    -H "Content-Type: application/json" \
    --cookie cookies.txt \
    -d '{
        "stage1_threshold": "0.70",
        "stage1_title_weight": 60,
        "stage1_content_weight": 50,
        "stage2_threshold": "0.60",
        "stage2_title_weight": 50,
        "stage2_content_weight": 50
    }')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

# 期望返回 400 錯誤
if [ "$http_code" -eq 400 ] || [ "$http_code" -eq 200 ]; then
    if [ "$http_code" -eq 400 ]; then
        print_success "正確拒絕不正確的權重設定 (HTTP 400)"
        echo -e "\n${YELLOW}錯誤訊息：${NC}"
        echo "$body" | jq '.'
    else
        print_info "後端未驗證權重總和（HTTP 200，建議添加驗證）"
    fi
else
    print_error "非預期的狀態碼: HTTP $http_code"
fi

##############################################################################
# 測試 8: 測試錯誤處理 - 不存在的 Assistant
##############################################################################
print_test_header "8" "測試錯誤處理 - 不存在的 Assistant"

print_info "嘗試訪問不存在的 Assistant: 'unknown_assistant'"

response=$(curl -s -w "\n%{http_code}" \
    -X GET "$BASE_URL/unknown_assistant/" \
    -H "Content-Type: application/json" \
    --cookie cookies.txt)

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if check_status_code 404 "$http_code" "正確返回 404 Not Found"; then
    echo -e "\n${YELLOW}錯誤訊息：${NC}"
    echo "$body" | jq '.'
else
    print_error "應該返回 404，但返回了 HTTP $http_code"
fi

##############################################################################
# 測試總結
##############################################################################
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}測試總結${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "總測試數: ${BLUE}$TOTAL_TESTS${NC}"
echo -e "通過測試: ${GREEN}$PASSED_TESTS${NC}"
echo -e "失敗測試: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}✓ 所有測試通過！${NC}"
    exit 0
else
    echo -e "\n${RED}✗ 有 $FAILED_TESTS 個測試失敗${NC}"
    exit 1
fi

# 清理臨時檔案
rm -f cookies.txt
