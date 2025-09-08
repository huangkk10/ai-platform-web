#!/bin/bash

# Docker 安裝腳本 - Ubuntu/Debian 系統
# 作者: huangkk10
# 日期: 2025-09-08
# 用途: 自動安裝 Docker CE 並設定使用者權限
# 說明文件: docs/guide/docker-installation.md

set -e  # 遇到錯誤立即停止

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 輸出函數
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查是否為 root 使用者
if [[ $EUID -eq 0 ]]; then
   print_error "請不要以 root 使用者執行此腳本，請使用一般使用者並在需要時輸入 sudo 密碼"
   exit 1
fi

# 檢查系統
print_info "檢查系統資訊..."
if [[ ! -f /etc/os-release ]]; then
    print_error "無法檢測系統版本"
    exit 1
fi

source /etc/os-release
print_info "系統: $NAME $VERSION"

# 檢查是否為 Ubuntu 或 Debian
if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
    print_warning "此腳本主要針對 Ubuntu/Debian 系統，其他系統可能需要調整"
fi

print_info "開始安裝 Docker..."

# 步驟 1: 更新套件清單並安裝依賴
print_info "步驟 1/7: 更新套件清單並安裝依賴套件..."
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 步驟 2: 新增 Docker 官方 GPG key
print_info "步驟 2/7: 新增 Docker 官方 GPG key..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 步驟 3: 新增 Docker repository
print_info "步驟 3/7: 新增 Docker repository..."
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 步驟 4: 更新套件清單並安裝 Docker
print_info "步驟 4/7: 安裝 Docker CE 及相關組件..."
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 步驟 5: 啟動並啟用 Docker 服務
print_info "步驟 5/7: 啟動 Docker 服務..."
sudo systemctl start docker
sudo systemctl enable docker

# 步驟 6: 將使用者加入 docker 群組
print_info "步驟 6/7: 將使用者 $USER 加入 docker 群組..."
sudo usermod -aG docker $USER

# 步驟 7: 驗證安裝
print_info "步驟 7/7: 驗證 Docker 安裝..."

# 檢查 Docker 版本
DOCKER_VERSION=$(docker --version)
COMPOSE_VERSION=$(docker compose version)

print_success "Docker 安裝完成！"
print_info "Docker 版本: $DOCKER_VERSION"
print_info "Docker Compose 版本: $COMPOSE_VERSION"

# 測試 Docker 運行
print_info "測試 Docker 運行..."
if sudo docker run hello-world > /dev/null 2>&1; then
    print_success "Docker 測試運行成功！"
else
    print_warning "Docker 測試運行失敗，請檢查安裝"
fi

# 提示使用者重新登入
print_warning "重要提示："
print_warning "1. 為了不使用 sudo 執行 docker 命令，請執行以下其中一個步驟："
print_warning "   a) 登出並重新登入"
print_warning "   b) 執行: newgrp docker"
print_warning "   c) 執行: exec su - \$USER"
print_warning "2. 然後可以執行 'docker run hello-world' 測試"

# 顯示有用的 Docker 命令
print_info ""
print_info "常用 Docker 命令："
print_info "  docker --version          # 檢查版本"
print_info "  docker info               # 檢查系統資訊"
print_info "  docker ps                 # 列出運行中的容器"
print_info "  docker images             # 列出映像檔"
print_info "  docker run hello-world    # 測試運行"
print_info "  docker compose --help     # Docker Compose 幫助"

print_success "Docker 安裝腳本執行完成！"