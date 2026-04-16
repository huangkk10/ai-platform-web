---
name: ai-platform-infra
description: 'AI Platform Web 專案基礎架構知識。Use when: asking about service IPs, ports, endpoints, Dify configuration, database connection, web server address, git branch strategy, dev vs production environment, docker-compose setup, nginx routing, deployment, environment variables, or any infrastructure-related questions for this project.'
argument-hint: 'What infrastructure info do you need? (e.g., IPs, ports, branch, Dify config)'
---

# AI Platform Web — Infrastructure Skill

## 概述

本 skill 提供 `ai-platform-web` 專案的完整基礎架構資訊，包含服務 IP、Port、環境設定、分支策略等。

## 何時使用

- 詢問服務 IP / Port / URL
- 切換或確認 git branch
- 設定 Dify API 連線
- 部署到開發機或生產機
- 設定環境變數 (`.env`)
- Docker Compose 啟動/配置問題

## 快速參考

| 服務 | IP | 角色 |
|------|----|------|
| Dify (AI PC) | `10.253.43.244` | LLM / RAG 服務 |
| Web Server    | `10.10.172.127` | Django + React + Nginx（本機） |
| Database      | `10.10.172.123`  | PostgreSQL 獨立主機 |

**開發機 → 使用 `develop` branch**  
**生產機 → 使用 `main` branch**

## 參考文件

- 完整 IP/Port 清單：[references/infrastructure.md](./references/infrastructure.md)
- 專案架構與 Nginx 路由：[references/architecture.md](./references/architecture.md)
- Git 分支策略與部署流程：[references/branch-strategy.md](./references/branch-strategy.md)

## 使用流程

1. 讀取對應的 reference 文件取得詳細資訊
2. 根據環境（develop / main）套用對應設定
3. 如需修改 IP，更新 `config/settings.yaml` 與 `docker-compose.yml`
