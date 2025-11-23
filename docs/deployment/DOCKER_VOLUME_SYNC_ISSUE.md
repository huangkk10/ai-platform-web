# Docker Volume 掛載同步延遲問題診斷與解決方案

## 📋 問題描述

在開發過程中發現，編輯宿主機上的檔案後，Docker 容器內的檔案沒有即時更新，導致：
- 修改代碼後需要手動重啟容器
- 使用 `docker cp` 強制複製檔案
- 開發效率降低

## 🔍 根本原因分析

### 1. 檔案權限問題 ⚠️ **主要原因**

```bash
# 檢查檔案權限
$ ls -la backend/api/views/viewsets/benchmark_viewsets.py
-rw-r--r-- 1 root root 21331 十一 23 14:19 benchmark_viewsets.py
```

**問題**：
- 檔案所有者是 `root:root`
- 開發者以 `user` 身份編輯
- 導致權限不一致

### 2. 編輯器寫入行為

**VSCode/大多數編輯器的寫入流程**：
1. 建立暫時檔案 `.filename.swp`
2. 寫入新內容到暫時檔案
3. 刪除原檔案 ❌ **inode 消失**
4. 重新命名暫時檔案為原檔案名 ✅ **新 inode**

### 3. Docker Volume 掛載機制

**Docker 追蹤檔案的方式**：
- 使用 **inode** 而非檔案名稱
- 當檔案被刪除並重建時，inode 改變
- 容器內的掛載仍指向**舊 inode**
- 結果：容器看到的是**已刪除的舊檔案內容**

```
宿主機              容器內
-------             -------
舊檔案 (inode 123) → 容器看到 (inode 123)
  ↓ 編輯器刪除
舊檔案被刪除
  ↓ 編輯器重建
新檔案 (inode 456)   容器仍看到 (inode 123 - 已刪除)
```

## ✅ 解決方案

### 方案 1：修正檔案權限（推薦）⭐

**原理**：確保檔案所有者與開發者一致

```bash
# 將整個專案目錄的所有權改回當前用戶
sudo chown -R $USER:$USER /home/user/codes/ai-platform-web/backend
sudo chown -R $USER:$USER /home/user/codes/ai-platform-web/library

# 驗證
ls -la backend/api/views/viewsets/benchmark_viewsets.py
# 應該顯示：-rw-r--r-- 1 user user ...
```

**優點**：
- ✅ 一次性解決
- ✅ 不影響效能
- ✅ 符合最佳實踐

**缺點**：
- ❌ 需要 sudo 權限

---

### 方案 2：配置編輯器直接寫入模式

**VSCode 配置** (`.vscode/settings.json`):
```json
{
  "files.useExperimentalFileWatcher": true,
  "files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/.git/subtree-cache/**": true,
    "**/node_modules/*/**": true
  }
}
```

**Vim 配置** (`~/.vimrc`):
```vim
" 關閉備份和交換檔案
set nobackup
set nowritebackup
set noswapfile

" 使用直接寫入而不是 rename
set backupcopy=yes
```

**優點**：
- ✅ 不需要修改權限
- ✅ 每個開發者可獨立配置

**缺點**：
- ❌ 需要每個編輯器都配置
- ❌ 可能影響某些編輯器功能（如 undo）

---

### 方案 3：使用 Docker delegated 掛載模式

**修改 `docker-compose.yml`**:
```yaml
services:
  django:
    volumes:
      # 原本：
      # - ./backend:/app
      
      # 改為（macOS/Windows）：
      - ./backend:/app:delegated
      - ./library:/app/library:delegated
      
      # 或（Linux - 使用 cached）：
      - ./backend:/app:cached
      - ./library:/app/library:cached
```

**delegated 模式**：
- 容器的寫入**延遲**同步回宿主機
- 適合 macOS/Windows（宿主機讀取為主）

**cached 模式**：
- 宿主機的寫入**延遲**同步到容器
- 適合 Linux（容器讀取為主）

**優點**：
- ✅ 提升效能
- ✅ 減少同步延遲

**缺點**：
- ❌ 仍可能有短暫延遲
- ❌ 不保證即時一致性

---

### 方案 4：使用 Django runserver 的 auto-reload

**原理**：Django 開發服務器會監聽檔案變更

```bash
# docker-compose.yml 中已配置
command: python manage.py runserver 0.0.0.0:8000
```

**檢查 settings.py**：
```python
# backend/ai_platform/settings.py
DEBUG = True  # 必須為 True

# Django 會自動監聽這些目錄的變更
import sys
if DEBUG:
    INSTALLED_APPS += ['django_extensions']
```

**手動觸發重載**（如果 auto-reload 失效）：
```bash
# 方法 1：觸碰檔案更新時間戳
touch backend/manage.py

# 方法 2：重啟 Django 容器
docker restart ai-django
```

**優點**：
- ✅ 開發時自動重載
- ✅ 不需額外配置

**缺點**：
- ❌ 依賴 Django 的檔案監聽
- ❌ 遇到 inode 問題仍會失效

---

## 🔧 實際執行步驟（推薦順序）

### Step 1：修正權限（必做）

```bash
cd /home/user/codes/ai-platform-web

# 修正所有權
sudo chown -R $USER:$USER backend/
sudo chown -R $USER:$USER library/
sudo chown -R $USER:$USER config/

# 驗證
ls -la backend/api/views/viewsets/ | head -5
```

### Step 2：配置 VSCode（建議）

```bash
# 創建或編輯專案設定
mkdir -p .vscode
cat > .vscode/settings.json << 'EOF'
{
  "files.useExperimentalFileWatcher": true,
  "files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/node_modules/*/**": true,
    "**/__pycache__/**": true,
    "**/venv/**": true
  }
}
EOF
```

### Step 3：優化 Docker 掛載（可選）

```yaml
# docker-compose.yml
services:
  django:
    volumes:
      - ./backend:/app:cached
      - ./library:/app/library:cached
      - ./config:/app/config:cached
```

```bash
# 重啟容器以應用變更
docker compose down
docker compose up -d
```

### Step 4：驗證同步

```bash
# Terminal 1：監聽容器內檔案
docker exec ai-django sh -c 'while true; do stat -c "%Y %n" /app/api/views/viewsets/benchmark_viewsets.py; sleep 1; done'

# Terminal 2：編輯宿主機檔案
echo "# test sync" >> backend/api/views/viewsets/benchmark_viewsets.py

# 觀察 Terminal 1 是否立即顯示時間戳變更
```

## 📊 問題診斷指令

### 檢查檔案權限
```bash
# 宿主機
ls -la backend/api/views/viewsets/benchmark_viewsets.py

# 容器內
docker exec ai-django ls -la /app/api/views/viewsets/benchmark_viewsets.py
```

### 檢查 inode
```bash
# 宿主機
stat backend/api/views/viewsets/benchmark_viewsets.py | grep Inode

# 容器內
docker exec ai-django stat /app/api/views/viewsets/benchmark_viewsets.py | grep Inode
```

### 檢查時間戳
```bash
# 宿主機
stat backend/api/views/viewsets/benchmark_viewsets.py | grep Modify

# 容器內
docker exec ai-django stat /app/api/views/viewsets/benchmark_viewsets.py | grep Modify
```

### 測試同步
```bash
# 1. 記錄修改前的內容
docker exec ai-django tail -5 /app/api/views/viewsets/benchmark_viewsets.py

# 2. 在宿主機修改檔案
echo "# sync test" >> backend/api/views/viewsets/benchmark_viewsets.py

# 3. 立即檢查容器內容
docker exec ai-django tail -5 /app/api/views/viewsets/benchmark_viewsets.py

# 如果內容不同 → 同步延遲
# 如果內容相同 → 同步正常
```

## 🎯 常見錯誤情境

### 情境 1：使用 sudo 編輯檔案

```bash
# ❌ 錯誤
sudo vim backend/api/views/viewsets/benchmark_viewsets.py

# 結果：檔案變成 root:root
# 解決：sudo chown user:user filename
```

### 情境 2：從容器內複製檔案到宿主機

```bash
# ❌ 錯誤
docker cp ai-django:/app/some_file.py backend/

# 結果：檔案變成 root:root
# 解決：sudo chown $USER:$USER backend/some_file.py
```

### 情境 3：VSCode Remote Containers

```bash
# 使用 Remote Containers 擴展時
# 檔案可能屬於容器內的 user
# 解決：在 devcontainer.json 設定 remoteUser
```

## 📚 相關資源

- [Docker Volumes 官方文檔](https://docs.docker.com/storage/volumes/)
- [Docker Compose Volumes 配置](https://docs.docker.com/compose/compose-file/compose-file-v3/#volumes)
- [VSCode Docker 開發最佳實踐](https://code.visualstudio.com/docs/containers/overview)

## ✅ 驗證清單

- [ ] 檔案所有者是當前用戶（非 root）
- [ ] VSCode/編輯器已配置檔案監聽
- [ ] Docker volume 使用 cached 模式（Linux）
- [ ] Django runserver auto-reload 正常運作
- [ ] 編輯檔案後容器內立即同步
- [ ] 不需要手動 `docker cp` 或重啟容器

---

**更新日期**：2025-11-23  
**問題狀態**：✅ 已解決  
**解決方案**：修正檔案權限 + VSCode 配置
