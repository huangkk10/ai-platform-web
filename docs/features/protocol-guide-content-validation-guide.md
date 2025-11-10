# Protocol Guide 內容規範與補救指南

**文檔日期**：2025-11-10  
**目的**：確保所有 Protocol Guide 都能被搜尋系統正確索引  
**適用對象**：知識庫管理員、內容創建者

---

## 🎯 問題背景

### 當前系統限制

Protocol Assistant 使用 **Section 級向量搜尋系統**，要求文檔必須符合以下條件：

```
✅ 必須條件：
├─ Markdown 標題結構（# ## ###）
├─ 內容長度 > 10 字元
└─ 至少包含 1 個標題

❌ 不符合條件會導致：
├─ Section 向量無法生成
├─ 無法被搜尋系統找到
└─ 不會出現在引用來源中
```

### 實際案例："Cup" 檔案問題

```
問題檔案：Cup
├─ 內容：只有字母 "a"
├─ 沒有 Markdown 標題
├─ Section 向量：0 個
└─ 結果：無法被搜尋到 ❌
```

---

## 📋 配套方案（不改 Code）

### 方案 1：建立內容規範與審查機制 ⭐ 推薦

#### 1.1 內容創建規範

**最小內容要求**（強制性）：

```markdown
# [主題名稱]

## 基本資訊
[至少 50 字的描述]

## 詳細說明
[至少 100 字的內容]

## 參考資料
- 相關連結 1
- 相關連結 2
```

**推薦結構**：

```markdown
# [主題名稱]

## 目錄
1. 概述
2. 操作步驟
3. 注意事項
4. 常見問題

## 1. 概述
[背景介紹]

### 1.1 目的
[說明目的]

### 1.2 適用範圍
[適用情況]

## 2. 操作步驟
### 2.1 準備階段
[準備工作]

### 2.2 執行階段
[執行步驟]

### 2.3 驗證階段
[驗證方法]

## 3. 注意事項
- 注意點 1
- 注意點 2

## 4. 常見問題
### Q1: [問題]
A: [答案]

### Q2: [問題]
A: [答案]

## 參考資料
- [相關文檔]
- [外部連結]
```

#### 1.2 創建前檢查清單

**在提交前，確認以下項目**：

```
☐ 包含至少 1 個一級標題（# 標題）
☐ 包含至少 2 個二級標題（## 標題）
☐ 每個段落至少 50 字元
☐ 總內容長度 > 200 字元
☐ 使用正確的 Markdown 語法
☐ 標題階層合理（不要跳級）
```

---

### 方案 2：使用內容模板系統

#### 2.1 建立標準模板

**在前端添加快速模板按鈕**（不改 code，用戶手動複製）：

創建檔案：`docs/templates/protocol-guide-templates.md`

```markdown
# Protocol Guide 內容模板

## 模板 1：標準操作流程（SOP）

### 複製以下內容開始創建：

\`\`\`markdown
# [流程名稱] SOP

## 1. 概述
[簡要說明此流程的目的和適用場景]

## 2. 前置準備
### 2.1 硬體需求
- 設備 1
- 設備 2

### 2.2 軟體需求
- 軟體 1
- 軟體 2

### 2.3 文件準備
- 文件 1
- 文件 2

## 3. 操作步驟
### 3.1 步驟一
[詳細說明]

### 3.2 步驟二
[詳細說明]

### 3.3 步驟三
[詳細說明]

## 4. 驗證方法
[如何確認操作成功]

## 5. 注意事項
- 注意點 1
- 注意點 2

## 6. 常見問題
### Q1: [問題]
A: [答案]

## 7. 參考資料
- [相關文檔連結]
\`\`\`

---

## 模板 2：技術文檔

### 複製以下內容開始創建：

\`\`\`markdown
# [技術主題]

## 1. 簡介
### 1.1 背景
[技術背景]

### 1.2 目的
[文檔目的]

## 2. 技術規格
### 2.1 系統要求
[系統需求]

### 2.2 相容性
[相容性資訊]

## 3. 架構說明
### 3.1 整體架構
[架構圖和說明]

### 3.2 核心組件
[主要組件]

## 4. 使用方法
### 4.1 基本用法
[基本操作]

### 4.2 進階用法
[進階功能]

## 5. 範例
### 5.1 範例一
[程式碼或操作範例]

### 5.2 範例二
[程式碼或操作範例]

## 6. 故障排除
### 6.1 常見錯誤
[錯誤說明和解決方法]

### 6.2 除錯技巧
[除錯方法]

## 7. 附錄
### 7.1 術語表
[專有名詞解釋]

### 7.2 參考資料
[外部資源]
\`\`\`

---

## 模板 3：簡短說明（最小模板）

### 適用於簡短內容，但仍符合搜尋要求：

\`\`\`markdown
# [主題名稱]

## 基本資訊
[簡要描述，至少 50 字]

## 詳細說明
[詳細內容，至少 100 字]

## 使用方法
1. 步驟一
2. 步驟二
3. 步驟三

## 注意事項
- 注意點 1
- 注意點 2

## 參考資料
- [相關連結]
\`\`\`
```

#### 2.2 模板使用指南

在知識庫管理頁面添加說明：

```markdown
📝 創建新 Protocol Guide 前，請參考：
   docs/templates/protocol-guide-templates.md

✅ 確保您的內容包含：
   • 至少 1 個一級標題（# 標題）
   • 至少 2 個二級標題（## 標題）
   • 結構化的內容組織
```

---

### 方案 3：現有內容補救流程

#### 3.1 識別問題檔案

**使用診斷腳本**：

```bash
#!/bin/bash
# check_all_guides.sh - 檢查所有 Protocol Guide 的向量狀態

echo "========================================"
echo "Protocol Guide 向量完整性檢查"
echo "========================================"
echo ""

# 查詢所有 Protocol Guide
GUIDES=$(docker exec postgres_db psql -U postgres -d ai_platform -t -A -c \
  "SELECT id, title FROM protocol_guide ORDER BY id;")

echo "ID | 標題 | 內容長度 | Section數量 | 狀態"
echo "---|------|---------|------------|-----"

while IFS='|' read -r id title; do
    # 獲取內容長度
    LENGTH=$(docker exec postgres_db psql -U postgres -d ai_platform -t -A -c \
      "SELECT LENGTH(content) FROM protocol_guide WHERE id=$id;")
    
    # 獲取 Section 數量
    SECTIONS=$(docker exec postgres_db psql -U postgres -d ai_platform -t -A -c \
      "SELECT COUNT(*) FROM document_section_embeddings 
       WHERE source_table='protocol_guide' AND document_id='$id';")
    
    # 判斷狀態
    if [ "$SECTIONS" -eq 0 ]; then
        STATUS="❌ 需要修復"
        echo "$id | $title | $LENGTH | $SECTIONS | $STATUS"
    elif [ "$LENGTH" -lt 100 ]; then
        STATUS="⚠️  內容過短"
        echo "$id | $title | $LENGTH | $SECTIONS | $STATUS"
    else
        STATUS="✅ 正常"
    fi
done <<< "$GUIDES"

echo ""
echo "========================================"
echo "統計摘要"
echo "========================================"

TOTAL=$(echo "$GUIDES" | wc -l)
NEED_FIX=$(docker exec postgres_db psql -U postgres -d ai_platform -t -A -c \
  "SELECT COUNT(DISTINCT pg.id) 
   FROM protocol_guide pg
   LEFT JOIN document_section_embeddings dse 
     ON dse.source_table='protocol_guide' AND dse.document_id=CAST(pg.id AS VARCHAR)
   WHERE dse.id IS NULL;")

echo "總計檔案數: $TOTAL"
echo "需要修復: $NEED_FIX"
echo "正常檔案: $((TOTAL - NEED_FIX))"
```

#### 3.2 批量補救腳本

**對於簡短內容的檔案，快速添加結構**：

```bash
#!/bin/bash
# fix_short_guide.sh - 修復簡短的 Protocol Guide

GUIDE_ID=$1

if [ -z "$GUIDE_ID" ]; then
    echo "用法: ./fix_short_guide.sh <guide_id>"
    exit 1
fi

echo "正在修復 Protocol Guide ID: $GUIDE_ID"

# 獲取現有標題和內容
TITLE=$(docker exec postgres_db psql -U postgres -d ai_platform -t -A -c \
  "SELECT title FROM protocol_guide WHERE id=$GUIDE_ID;")

OLD_CONTENT=$(docker exec postgres_db psql -U postgres -d ai_platform -t -A -c \
  "SELECT content FROM protocol_guide WHERE id=$GUIDE_ID;")

echo "原始標題: $TITLE"
echo "原始內容: $OLD_CONTENT"
echo ""

# 生成新的結構化內容
NEW_CONTENT="# $TITLE

## 基本資訊
原始內容：$OLD_CONTENT

（此部分內容待補充，請編輯以添加更多詳細資訊）

## 詳細說明
待補充...

## 使用方法
1. 待補充
2. 待補充

## 注意事項
- 待補充

## 參考資料
- 待補充
"

# 更新資料庫（需要 Python）
docker exec -it ai-django python manage.py shell << EOF
from api.models import ProtocolGuide
from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService

# 獲取並更新
guide = ProtocolGuide.objects.get(id=$GUIDE_ID)
guide.content = """$NEW_CONTENT"""
guide.save()

# 重新生成向量
service = SectionVectorizationService()
result = service.vectorize_document_sections(
    source_table='protocol_guide',
    source_id=$GUIDE_ID,
    markdown_content=guide.content,
    metadata={'title': guide.title}
)

print(f"✅ 修復完成！生成了 {result} 個 sections")
EOF

echo ""
echo "✅ 修復完成！請到前端檢查並補充內容。"
```

---

### 方案 4：建立內容品質監控系統

#### 4.1 定期檢查腳本（Cron Job）

```bash
#!/bin/bash
# daily_guide_check.sh - 每日檢查 Protocol Guide 品質

LOG_FILE="/home/user/codes/ai-platform-web/logs/guide_quality_$(date +%Y%m%d).log"

{
    echo "========================================"
    echo "Protocol Guide 品質檢查報告"
    echo "日期: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================"
    echo ""
    
    # 檢查缺少 Section 向量的檔案
    echo "🔍 檢查缺少 Section 向量的檔案..."
    PROBLEM_GUIDES=$(docker exec postgres_db psql -U postgres -d ai_platform -t -A -c \
      "SELECT pg.id, pg.title, LENGTH(pg.content) as content_length
       FROM protocol_guide pg
       LEFT JOIN document_section_embeddings dse 
         ON dse.source_table='protocol_guide' AND dse.document_id=CAST(pg.id AS VARCHAR)
       WHERE dse.id IS NULL
       ORDER BY pg.created_at DESC;")
    
    if [ -z "$PROBLEM_GUIDES" ]; then
        echo "✅ 所有檔案都有 Section 向量"
    else
        echo "❌ 發現問題檔案："
        echo "ID | 標題 | 內容長度"
        echo "$PROBLEM_GUIDES" | while IFS='|' read -r id title length; do
            echo "$id | $title | $length 字元"
        done
        
        # 發送警告通知（可選）
        echo ""
        echo "⚠️  建議：請檢查並修復以上檔案"
    fi
    
    echo ""
    echo "========================================"
    
} | tee "$LOG_FILE"

# 如果有問題，可以發送郵件或 Slack 通知
if [ ! -z "$PROBLEM_GUIDES" ]; then
    # 範例：發送通知
    # mail -s "Protocol Guide 品質警告" admin@example.com < "$LOG_FILE"
    echo "📧 品質報告已儲存: $LOG_FILE"
fi
```

**設定 Cron Job**：

```bash
# 編輯 crontab
crontab -e

# 添加每日檢查（每天早上 9:00）
0 9 * * * /home/user/codes/ai-platform-web/daily_guide_check.sh
```

#### 4.2 儀表板監控指標

**在 Django Admin 或前端顯示的統計資訊**：

```python
# 可以在 Django Admin 添加統計面板

from django.db import connection

def get_guide_quality_stats():
    """獲取 Protocol Guide 品質統計"""
    with connection.cursor() as cursor:
        # 總計
        cursor.execute("SELECT COUNT(*) FROM protocol_guide")
        total = cursor.fetchone()[0]
        
        # 有 Section 向量的
        cursor.execute("""
            SELECT COUNT(DISTINCT pg.id)
            FROM protocol_guide pg
            JOIN document_section_embeddings dse 
              ON dse.source_table='protocol_guide' 
              AND dse.document_id=CAST(pg.id AS VARCHAR)
        """)
        with_vectors = cursor.fetchone()[0]
        
        # 需要修復的
        need_fix = total - with_vectors
        
        return {
            'total': total,
            'with_vectors': with_vectors,
            'need_fix': need_fix,
            'health_rate': f"{(with_vectors/total*100):.1f}%" if total > 0 else "0%"
        }
```

---

## 📝 使用者操作指南

### 對於內容創建者

**創建新 Protocol Guide 時**：

1. **使用模板**
   - 複製適合的模板（SOP / 技術文檔 / 簡短說明）
   - 填寫所有必要欄位

2. **自我檢查**
   ```
   ☐ 包含至少 3 個標題
   ☐ 每個段落有實質內容（不是"待補充"）
   ☐ 總長度 > 200 字元
   ☐ 使用正確的 Markdown 語法
   ```

3. **提交前預覽**
   - 確認標題階層正確
   - 確認內容可讀性

### 對於管理員

**定期維護任務**：

1. **每週檢查**（建議每週一）
   ```bash
   ./check_all_guides.sh
   ```

2. **發現問題時**
   ```bash
   # 方法 1：快速修復（添加基本結構）
   ./fix_short_guide.sh <guide_id>
   
   # 方法 2：聯繫原作者補充內容
   # 方法 3：刪除無效檔案
   ```

3. **每月報告**
   - 統計品質指標
   - 識別常見問題
   - 改進模板和規範

---

## 🎯 最佳實踐建議

### Do's ✅

1. **使用標準模板**
   - 節省時間
   - 確保結構完整
   - 易於搜尋

2. **分層組織內容**
   ```markdown
   # 一級標題（主題）
   ## 二級標題（章節）
   ### 三級標題（小節）
   ```

3. **提供充足的上下文**
   - 背景說明
   - 操作步驟
   - 注意事項
   - 參考資料

4. **定期更新維護**
   - 過時內容及時更新
   - 補充新的資訊
   - 修正錯誤

### Don'ts ❌

1. **不要只寫標題沒有內容**
   ```markdown
   ❌ # Cup
      （沒有任何內容）
   
   ✅ # Cup
      ## 基本資訊
      Cup 是...
   ```

2. **不要使用純文字（無結構）**
   ```markdown
   ❌ 這是一段沒有標題的文字...
   
   ✅ # 主題
      ## 段落一
      內容...
   ```

3. **不要跳過標題層級**
   ```markdown
   ❌ # 標題 1
      ### 標題 3（跳過了 ##）
   
   ✅ # 標題 1
      ## 標題 2
      ### 標題 3
   ```

4. **不要使用非標準 Markdown**
   ```markdown
   ❌ <h1>標題</h1>（HTML）
   
   ✅ # 標題（Markdown）
   ```

---

## 📊 成效追蹤

### 關鍵指標

1. **向量完整率**
   ```
   目標：> 95%
   計算：(有 Section 向量的檔案數 / 總檔案數) × 100%
   ```

2. **平均內容長度**
   ```
   目標：> 500 字元
   監控：過短的檔案可能需要補充
   ```

3. **搜尋成功率**
   ```
   目標：> 90%
   計算：(成功找到的查詢 / 總查詢數) × 100%
   ```

### 改善循環

```
發現問題 → 修復內容 → 驗證向量 → 測試搜尋 → 更新規範
    ↑                                              ↓
    └──────────────── 持續改善 ←────────────────────┘
```

---

## 📚 相關資源

- **診斷工具**：`./diagnose_cup_missing.sh`
- **完整性檢查**：`./check_all_guides.sh`
- **修復腳本**：`./fix_short_guide.sh`
- **內容模板**：`docs/templates/protocol-guide-templates.md`
- **技術文檔**：`docs/debugging/protocol-assistant-citation-missing.md`

---

## 🎓 培訓建議

### 新用戶入職培訓

1. **第 1 天：理解系統**
   - Section 向量搜尋原理
   - Markdown 基本語法
   - 為什麼需要結構化內容

2. **第 2 天：實作練習**
   - 使用模板創建測試檔案
   - 運行診斷腳本驗證
   - 測試搜尋功能

3. **第 3 天：最佳實踐**
   - 審查現有優質檔案
   - 學習常見錯誤
   - 建立個人檢查清單

---

## 🔄 持續改進

### 階段 1：短期（立即執行）

- [x] 建立內容規範文檔
- [x] 創建診斷工具
- [x] 提供修復腳本
- [ ] 培訓現有用戶

### 階段 2：中期（1-2 週）

- [ ] 補救所有現有問題檔案
- [ ] 建立品質監控系統
- [ ] 設定定期檢查 Cron Job
- [ ] 收集用戶反饋

### 階段 3：長期（1 個月後）

- [ ] 分析品質趨勢
- [ ] 優化模板和規範
- [ ] 考慮前端驗證機制
- [ ] 評估是否需要代碼改進

---

## 💡 未來改進方向（需要改 Code）

當以上方案實施一段時間後，如果仍有問題，可以考慮：

1. **前端即時驗證**
   - 在編輯器中即時檢查 Markdown 結構
   - 警告用戶內容過短或缺少標題

2. **自動 Fallback 機制**
   - Section 搜尋無結果時，自動使用整篇向量
   - 提升對非標準內容的容錯性

3. **智能內容建議**
   - AI 自動生成標題結構建議
   - 提供內容擴充建議

---

**文檔版本**：v1.0  
**最後更新**：2025-11-10  
**維護者**：AI Platform Team  
**狀態**：✅ 已發布，可立即使用
