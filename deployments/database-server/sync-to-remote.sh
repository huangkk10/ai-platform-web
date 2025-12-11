#!/bin/bash
# =============================================================================
# 同步資料庫配置到遠端主機
# 用途：將 deployments/database-server/ 的配置同步到 10.10.173.29
# =============================================================================

set -e

# 配置
REMOTE_HOST="10.10.173.29"
REMOTE_USER="svd-ai"
REMOTE_DIR="~/postgres-db-server"
LOCAL_DIR="$(dirname "$0")"

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  資料庫配置同步腳本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "本機目錄: ${YELLOW}${LOCAL_DIR}${NC}"
echo -e "遠端主機: ${YELLOW}${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}${NC}"
echo ""

# 確認同步
read -p "確定要同步配置到遠端主機嗎？(y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}已取消同步${NC}"
    exit 0
fi

# 檢查遠端連線
echo -e "\n${GREEN}[1/4] 檢查遠端連線...${NC}"
if ssh -o ConnectTimeout=5 -o BatchMode=yes ${REMOTE_USER}@${REMOTE_HOST} "echo 'SSH 連線成功'" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH 連線正常${NC}"
else
    echo -e "${RED}✗ SSH 連線失敗，請確認：${NC}"
    echo "  1. 已設定 SSH key，或"
    echo "  2. 使用 sshpass 或手動輸入密碼"
    echo ""
    echo "提示：可以使用以下命令設定 SSH key："
    echo "  ssh-copy-id ${REMOTE_USER}@${REMOTE_HOST}"
    exit 1
fi

# 建立遠端目錄
echo -e "\n${GREEN}[2/4] 建立遠端目錄...${NC}"
ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_DIR}/scripts"
echo -e "${GREEN}✓ 目錄已建立${NC}"

# 同步檔案
echo -e "\n${GREEN}[3/4] 同步配置檔案...${NC}"
rsync -avz --progress \
    --exclude '.env' \
    --exclude '*.dump' \
    --exclude '*.sql.backup' \
    "${LOCAL_DIR}/" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"

echo -e "${GREEN}✓ 檔案同步完成${NC}"

# 顯示遠端檔案
echo -e "\n${GREEN}[4/4] 遠端檔案列表：${NC}"
ssh ${REMOTE_USER}@${REMOTE_HOST} "ls -la ${REMOTE_DIR}/ && echo '' && ls -la ${REMOTE_DIR}/scripts/"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  同步完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "下一步操作（在遠端主機上執行）："
echo -e "  ${YELLOW}ssh ${REMOTE_USER}@${REMOTE_HOST}${NC}"
echo -e "  ${YELLOW}cd ${REMOTE_DIR}${NC}"
echo -e "  ${YELLOW}docker compose up -d${NC}"
echo ""
