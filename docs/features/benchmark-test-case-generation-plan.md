# 🎯 Protocol Assistant 測試題庫生成計畫

**日期**: 2025-11-21  
**狀態**: 📋 規劃中  
**目標**: 基於現有知識庫內容生成高品質、多樣化的測試題目

---

## 📊 知識庫現況分析

### 1. 內容統計

**總體資料**：
- 總文章數：17 篇
- 平均文章長度：約 5,000 字元
- 最長文章：Google AVL (13,728 字元)
- 包含圖片的文章：5 篇 (最多 11 張圖片)

**主題分布**：
```
┌─────────────────┬────────┬────────────────────────────────┐
│ 主題類別        │ 數量   │ 代表文章                       │
├─────────────────┼────────┼────────────────────────────────┤
│ NVMe 測試       │ 9 篇   │ PyNvme3, UNH-IOL, SNVT2        │
│ PCIe 測試       │ 5 篇   │ PCIeCV, Google AVL             │
│ USB 測試        │ 5 篇   │ (部分文章含 USB 相關內容)      │
│ ULINK 測試工具  │ 2 篇   │ ULINK, Lenovo SSDV Ulink       │
│ 其他測試工具    │ 多篇   │ Oakgate, SANBlaze, WHQL        │
│ 專案特定        │ 多篇   │ Kingston Linux 開卡, Google AVL│
└─────────────────┴────────┴────────────────────────────────┘
```

**內容特性**：
- ✅ **操作步驟完整**：多數文章包含詳細的 SOP（如 ULINK、UNH-IOL）
- ✅ **圖文並茂**：重要步驟有截圖說明（如 Burn in Test 11 張圖）
- ✅ **工具導向**：大部分是測試工具的使用指南
- ✅ **技術深度**：涵蓋從基礎到進階的測試知識
- ⚠️ **專有名詞多**：大量專業術語和產品型號
- ⚠️ **文檔異質性**：有的是完整 SOP，有的是簡短說明

---

## 🎯 出題策略設計

### 核心原則

1. **基於真實內容**：題目答案必須在知識庫中存在
2. **覆蓋廣度**：涵蓋所有主要主題和文章
3. **難度分級**：簡單、中等、困難三個級別
4. **類型多樣**：事實、程序、對比、故障排除等
5. **可驗證性**：有明確的正確答案或預期文檔

---

## 📝 題目類型與範例

### 類型 1: **事實查詢 (Fact Query)**
> 測試搜尋是否能找到包含特定資訊的文檔

**簡單難度**：
```python
{
    "question": "ULINK 測試工具的完整名稱是什麼？",
    "question_type": "fact",
    "difficulty_level": "easy",
    "expected_document_ids": [28],  # ULINK 文章
    "expected_keywords": ["ULINK", "DriveMaster"],
    "category": "測試工具",
    "min_required_matches": 1
}
```

**中等難度**：
```python
{
    "question": "UNH-IOL 測試的原廠下載路徑是什麼？",
    "question_type": "fact",
    "difficulty_level": "medium",
    "expected_document_ids": [10],  # UNH-IOL 文章
    "expected_keywords": ["UNH-IOL", "unh-iol.atlassian.net"],
    "category": "測試工具",
    "min_required_matches": 1
}
```

**困難難度**：
```python
{
    "question": "在 Oakgate Gen4 平台上，如何套入 Debug Script (.so 檔)？",
    "question_type": "fact",
    "difficulty_level": "hard",
    "expected_document_ids": [35, 29],  # Oakgate套入Debug Script + Oakgate
    "expected_keywords": ["Oakgate", "Debug Script", ".so"],
    "category": "測試工具進階",
    "min_required_matches": 1,
    "acceptable_document_ids": [35, 29]  # 兩篇都可接受
}
```

---

### 類型 2: **程序查詢 (Procedure Query)**
> 測試搜尋是否能找到包含操作步驟的文檔

**簡單難度**：
```python
{
    "question": "如何安裝 ULINK 的 DriveMaster？",
    "question_type": "procedure",
    "difficulty_level": "easy",
    "expected_document_ids": [28],  # ULINK 文章
    "expected_keywords": ["DriveMaster", "安裝", "ULINK"],
    "category": "安裝設定",
    "min_required_matches": 1
}
```

**中等難度**：
```python
{
    "question": "如何設定 ULINK 的 PowerHub？",
    "question_type": "procedure",
    "difficulty_level": "medium",
    "expected_document_ids": [28],
    "expected_keywords": ["PowerHub", "設定", "PWRCTRL", "印表機"],
    "category": "安裝設定",
    "min_required_matches": 1
}
```

**困難難度**：
```python
{
    "question": "執行 UNH-IOL 測試的完整 SOP 步驟是什麼？",
    "question_type": "procedure",
    "difficulty_level": "hard",
    "expected_document_ids": [10],
    "expected_keywords": ["UNH-IOL", "SOP", "sudo su", "install.sh"],
    "category": "測試執行",
    "min_required_matches": 1
}
```

---

### 類型 3: **工具比較 (Comparison Query)**
> 測試搜尋是否能找到多個相關文檔進行對比

**中等難度**：
```python
{
    "question": "ULINK 和 Oakgate 這兩種測試工具有什麼差異？",
    "question_type": "comparison",
    "difficulty_level": "medium",
    "expected_document_ids": [28, 29],  # ULINK + Oakgate
    "expected_keywords": ["ULINK", "Oakgate", "測試"],
    "category": "工具對比",
    "min_required_matches": 2  # 必須找到兩篇
}
```

**困難難度**：
```python
{
    "question": "PyNvme3 和 UNH-IOL 在測試 NVMe SSD 時的應用場景有何不同？",
    "question_type": "comparison",
    "difficulty_level": "hard",
    "expected_document_ids": [34, 10],  # PyNvme3 + UNH-IOL
    "expected_keywords": ["PyNvme3", "UNH-IOL", "NVMe"],
    "category": "測試工具對比",
    "min_required_matches": 2
}
```

---

### 類型 4: **環境設定 (Configuration Query)**
> 測試搜尋是否能找到設定和準備相關的資訊

**簡單難度**：
```python
{
    "question": "執行 CrystalDiskMark 測試前需要做哪些環境準備？",
    "question_type": "configuration",
    "difficulty_level": "easy",
    "expected_document_ids": [16],  # CrystalDiskMark 5
    "expected_keywords": ["CrystalDiskMark", "Secure Boot", "BIOS"],
    "category": "測試準備",
    "min_required_matches": 1
}
```

**中等難度**：
```python
{
    "question": "WHQL 測試需要安裝什麼樣的 Server OS 環境？",
    "question_type": "configuration",
    "difficulty_level": "medium",
    "expected_document_ids": [32],  # WHQL
    "expected_keywords": ["WHQL", "Server OS", "安裝"],
    "category": "測試準備",
    "min_required_matches": 1
}
```

**困難難度**：
```python
{
    "question": "如何設定 SANBlaze 測試環境並登入網頁介面？",
    "question_type": "configuration",
    "difficulty_level": "hard",
    "expected_document_ids": [33],  # SANBlaze
    "expected_keywords": ["SANBlaze", "10.252.21.63", "vlun"],
    "category": "測試準備",
    "min_required_matches": 1
}
```

---

### 類型 5: **專案特定 (Project-Specific Query)**
> 測試搜尋是否能找到特定客戶或專案的文檔

**中等難度**：
```python
{
    "question": "Kingston Linux 開卡流程的第一步是什麼？",
    "question_type": "project_specific",
    "difficulty_level": "medium",
    "expected_document_ids": [25],  # Kingston Linux 開卡
    "expected_keywords": ["Kingston", "Linux", "BOM", "開卡"],
    "category": "專案流程",
    "min_required_matches": 1
}
```

**困難難度**：
```python
{
    "question": "Google AVL 測試中，Chromebook NB 的型號有哪些？",
    "question_type": "project_specific",
    "difficulty_level": "hard",
    "expected_document_ids": [26],  # Google AVL
    "expected_keywords": ["Google AVL", "Chromebook", "HP Elite"],
    "category": "專案規格",
    "min_required_matches": 1
}
```

---

### 類型 6: **故障排除 (Troubleshooting Query)**
> 測試搜尋是否能找到問題解決相關的資訊

**中等難度**：
```python
{
    "question": "當 ULINK 安裝失敗時，有哪些常見的注意事項？",
    "question_type": "troubleshooting",
    "difficulty_level": "medium",
    "expected_document_ids": [28],
    "expected_keywords": ["ULINK", "安裝", "注意事項", "DriveMaster"],
    "category": "問題排除",
    "min_required_matches": 1
}
```

**困難難度**：
```python
{
    "question": "如果 Oakgate 測試時發現 Debug Script 無法載入，應該檢查什麼？",
    "question_type": "troubleshooting",
    "difficulty_level": "hard",
    "expected_document_ids": [35, 29],
    "expected_keywords": ["Oakgate", "Debug Script", ".so"],
    "category": "問題排除",
    "min_required_matches": 1
}
```

---

### 類型 7: **版本特定 (Version-Specific Query)**
> 測試搜尋是否能區分不同版本的資訊

**困難難度**：
```python
{
    "question": "DriveMaster 2012 版本對應的 ULINK Script 是哪個？",
    "question_type": "version_specific",
    "difficulty_level": "hard",
    "expected_document_ids": [28],
    "expected_keywords": ["DriveMaster", "2012", "Compliance v2.6"],
    "category": "版本管理",
    "min_required_matches": 1
}
```

---

### 類型 8: **路徑查詢 (Path Query)**
> 測試搜尋是否能找到檔案路徑或網址

**簡單難度**：
```python
{
    "question": "ULINK 的測試腳本存放在 NAS 的哪個路徑？",
    "question_type": "path",
    "difficulty_level": "easy",
    "expected_document_ids": [28],
    "expected_keywords": ["ULINK", "nas01", "TestTools", "Release"],
    "category": "資源路徑",
    "min_required_matches": 1
}
```

**中等難度**：
```python
{
    "question": "PyNvme3 的 User Guide 網址是什麼？",
    "question_type": "path",
    "difficulty_level": "medium",
    "expected_document_ids": [34],
    "expected_keywords": ["PyNvme3", "pynv.me", "user-guide"],
    "category": "資源路徑",
    "min_required_matches": 1
}
```

---

## 🎲 題目生成策略

### 自動生成方法

#### 方法 1: **基於標題生成**
```python
def generate_questions_from_titles():
    """從文章標題生成基礎問題"""
    
    patterns = [
        ("如何使用 {title}？", "procedure", "medium"),
        ("{title} 的主要功能是什麼？", "fact", "easy"),
        ("{title} 測試的 SOP 是什麼？", "procedure", "medium"),
        ("執行 {title} 需要哪些準備工作？", "configuration", "medium"),
    ]
    
    # 範例：對 "ULINK" 文章生成
    questions = [
        "如何使用 ULINK？",
        "ULINK 的主要功能是什麼？",
        "ULINK 測試的 SOP 是什麼？",
        "執行 ULINK 需要哪些準備工作？",
    ]
```

#### 方法 2: **基於關鍵段落生成**
```python
def extract_qa_from_headings(content):
    """從 Markdown 標題提取問答對"""
    
    # 尋找 ## == 標記的重要段落
    # 如：## ==**ULINK User Guide**==
    #     ## ==SATA_ULINK 安裝和腳本注意事項==
    
    headings = re.findall(r'## ==(.+?)==', content)
    
    for heading in headings:
        question = f"關於 {heading}，請說明相關內容"
        # 生成對應的測試題目
```

#### 方法 3: **基於步驟序列生成**
```python
def generate_step_questions(content):
    """從步驟式內容生成程序問題"""
    
    # 尋找包含步驟的段落
    # Step 1, Step 2, ... or 1.x, 2.x, ...
    
    step_patterns = [
        r'### (\d+\..+?)(?=\n|$)',  # ### 1.安裝DriveMaster
        r'#### Step (\d+)',          # #### Step 1
        r'\(\d+\) (.+?)(?=\n|$)',    # (1) 輸入sudo su
    ]
    
    # 生成問題：
    # "執行 XXX 的第一步是什麼？"
    # "完成 XXX 需要經過哪些步驟？"
```

#### 方法 4: **基於工具對比生成**
```python
def generate_comparison_questions(all_articles):
    """找出相同類別的文章，生成對比問題"""
    
    tool_articles = {
        'ULINK': 28,
        'Oakgate': 29,
        'SANBlaze': 33,
        'PyNvme3': 34,
    }
    
    # 生成問題：
    # "ULINK 和 Oakgate 有什麼不同？"
    # "什麼時候應該使用 PyNvme3 而不是 UNH-IOL？"
```

---

## 📊 題目數量規劃

### 目標題庫規模

**總計目標**：150-200 題

**按難度分布**：
- 簡單 (Easy): 60 題 (40%)
- 中等 (Medium): 70 題 (45%)
- 困難 (Hard): 20 題 (15%)

**按類型分布**：
```
┌─────────────────┬────────┬──────────────────────┐
│ 題目類型        │ 數量   │ 主要來源文章         │
├─────────────────┼────────┼──────────────────────┤
│ 事實查詢        │ 40 題  │ 所有文章             │
│ 程序查詢        │ 50 題  │ SOP 類文章           │
│ 工具比較        │ 15 題  │ 多篇工具文章         │
│ 環境設定        │ 25 題  │ 安裝設定類文章       │
│ 專案特定        │ 15 題  │ Kingston, Google AVL │
│ 故障排除        │ 15 題  │ 進階文章             │
│ 版本特定        │ 10 題  │ DriveMaster, IOL     │
│ 路徑查詢        │ 20 題  │ 包含路徑的文章       │
└─────────────────┴────────┴──────────────────────┘
```

**按文章覆蓋**：
- 每篇文章至少 5-10 題
- 重要文章（如 ULINK, UNH-IOL）15-20 題
- 簡短文章（如 Cup）3-5 題

---

## 🔄 題目生成流程

### Phase 1: 手動精選題目 (Week 1)
**目標**：建立 50 題高品質基準題目

1. **選擇核心文章** (10 篇)
   - ULINK (28)
   - UNH-IOL (10)
   - CrystalDiskMark 5 (16)
   - Oakgate (29)
   - PyNvme3 (34)
   - SANBlaze (33)
   - WHQL (32)
   - Kingston Linux 開卡 (25)
   - Google AVL (26)
   - Lenovo SSDV Ulink (31)

2. **每篇文章產出 5 題**
   - 2 題簡單 (事實查詢)
   - 2 題中等 (程序或設定)
   - 1 題困難 (對比或故障排除)

3. **人工驗證**
   - 使用現有搜尋系統測試
   - 確認預期文檔是否能被找到
   - 調整關鍵字和閾值

### Phase 2: 半自動生成題目 (Week 2)
**目標**：擴充至 100 題

1. **基於範本生成**
   - 使用 Phase 1 的題目作為範本
   - 應用於剩餘文章

2. **自動提取關鍵資訊**
   - 標題、標題層級
   - 步驟序列
   - 檔案路徑
   - 版本號碼

3. **AI 輔助生成**
   - 使用 GPT 模型閱讀文章內容
   - 生成問題候選
   - 人工篩選和調整

### Phase 3: 全自動生成題目 (Week 3)
**目標**：達到 150+ 題

1. **建立生成規則引擎**
   ```python
   class QuestionGenerator:
       def __init__(self, article):
           self.article = article
           self.content = article.content
           self.title = article.title
       
       def generate_all(self):
           questions = []
           questions.extend(self.generate_fact_questions())
           questions.extend(self.generate_procedure_questions())
           questions.extend(self.generate_path_questions())
           return questions
   ```

2. **批量生成和驗證**
   - 對每篇文章自動生成 10-15 題
   - 自動執行搜尋驗證
   - 過濾低品質題目

3. **人工審核**
   - 審查自動生成的題目
   - 調整不合理的預期答案
   - 補充遺漏的重要問題

---

## ✅ 品質檢查標準

### 好題目的特徵
- ✅ **明確性**：問題表述清晰，沒有歧義
- ✅ **可答性**：答案明確存在於知識庫中
- ✅ **實用性**：反映真實用戶的查詢場景
- ✅ **可驗證**：有明確的正確/錯誤判斷標準
- ✅ **覆蓋性**：涵蓋文章的核心內容

### 應避免的題目類型
- ❌ **過於簡單**："ULINK 是什麼？"（太籠統）
- ❌ **超出範圍**："ULINK 的市場價格是多少？"（知識庫沒有）
- ❌ **需要推理**："哪個工具最好？"（主觀判斷）
- ❌ **過於細節**："ULINK 安裝程式的檔案大小？"（不重要）
- ❌ **時效性強**："最新版本的 IOL 是什麼？"（會過時）

---

## 🎯 具體題目範例（基於現有文章）

**📊 已設計題目總覽**：
- **ULINK** (ID: 28): 5 題（路徑、安裝、設定、腳本、版本）
- **UNH-IOL** (ID: 10): 4 題（路徑、執行、目錄、**密碼** 🆕）
- **CrystalDiskMark 5** (ID: 16): 3 題（BIOS 設定、異常排除、**SOP 流程** 🆕）
- **Burn in Test** (ID: 15): 1 題（**SOP 流程** 🆕）
- **對比類**: 2 題（ULINK vs Oakgate、NVMe 測試工具對比）

**目前共設計**: **15 題** (5+4+3+1+2)

---

### 來源：ULINK (ID: 28)

#### 題目 1 (簡單)
```json
{
  "question": "ULINK 測試的安裝程式和測試腳本存放在 NAS 的哪個路徑？",
  "question_type": "path",
  "difficulty_level": "easy",
  "expected_document_ids": [28],
  "expected_keywords": ["ULINK", "nas01", "TestTools", "Release"],
  "expected_answer_summary": "\\nas01\\smitw\\VCT\\Public\\TestTools\\Release\\Ulink",
  "category": "測試工具",
  "tags": ["ULINK", "路徑", "NAS"],
  "min_required_matches": 1
}
```

#### 題目 2 (簡單)
```json
{
  "question": "安裝 ULINK 的 DriveMaster 時需要注意什麼？",
  "question_type": "configuration",
  "difficulty_level": "easy",
  "expected_document_ids": [28],
  "expected_keywords": ["DriveMaster", "安裝", "一台OS", "一種版本"],
  "expected_answer_summary": "一台 OS 只能安裝一種版本的 DriveMaster",
  "category": "安裝設定",
  "tags": ["ULINK", "DriveMaster", "安裝"],
  "min_required_matches": 1
}
```

#### 題目 3 (中等)
```json
{
  "question": "如何設定 ULINK 的 PowerHub 印表機？",
  "question_type": "procedure",
  "difficulty_level": "medium",
  "expected_document_ids": [28],
  "expected_keywords": ["PowerHub", "印表機", "PWRCTRL", "USB001"],
  "expected_answer_summary": "搜尋 Print → 新增印表機 → 手動模式 → 選擇 USB001 → Generic/Text Only → 改名為 PWRCTRL → Reboot",
  "category": "安裝設定",
  "tags": ["ULINK", "PowerHub", "設定"],
  "min_required_matches": 1
}
```

#### 題目 4 (中等)
```json
{
  "question": "SATA ULINK Script 完整版本需要包含哪些部分？",
  "question_type": "fact",
  "difficulty_level": "medium",
  "expected_document_ids": [28],
  "expected_keywords": ["SATA ULINK", "TCG", "SMI_Comreset", "Script"],
  "expected_answer_summary": "SATA 部分、TCG Script、SMI_Comreset Script",
  "category": "測試腳本",
  "tags": ["ULINK", "SATA", "Script"],
  "min_required_matches": 1
}
```

#### 題目 5 (困難)
```json
{
  "question": "DriveMaster 2012 版本的 Key 對應哪個 ULINK Script？",
  "question_type": "version_specific",
  "difficulty_level": "hard",
  "expected_document_ids": [28],
  "expected_keywords": ["DriveMaster", "2012", "Compliance v2.6", "Key"],
  "expected_answer_summary": "DriveMaster 2012 對應 Compliance v2.6 Script",
  "category": "版本管理",
  "tags": ["ULINK", "DriveMaster", "版本"],
  "min_required_matches": 1
}
```

---

### 來源：UNH-IOL (ID: 10)

#### 題目 6 (簡單)
```json
{
  "question": "UNH-IOL 的原廠下載路徑是什麼？",
  "question_type": "path",
  "difficulty_level": "easy",
  "expected_document_ids": [10],
  "expected_keywords": ["UNH-IOL", "atlassian.net", "servicedesk"],
  "expected_answer_summary": "https://unh-iol.atlassian.net/servicedesk/customer/portals",
  "category": "測試工具",
  "tags": ["UNH-IOL", "網址"],
  "min_required_matches": 1
}
```

#### 題目 7 (中等)
```json
{
  "question": "執行 UNH-IOL 測試的第一步指令是什麼？",
  "question_type": "procedure",
  "difficulty_level": "medium",
  "expected_document_ids": [10],
  "expected_keywords": ["UNH-IOL", "sudo su", "密碼", "1"],
  "expected_answer_summary": "輸入 sudo su，密碼為 1",
  "category": "測試執行",
  "tags": ["UNH-IOL", "Linux", "指令"],
  "min_required_matches": 1
}
```

#### 題目 8 (困難)
```json
{
  "question": "UNH-IOL 測試目錄中包含哪些主要檔案或資料夾？",
  "question_type": "fact",
  "difficulty_level": "hard",
  "expected_document_ids": [10],
  "expected_keywords": ["UNH-IOL", "nvme", "install.sh"],
  "expected_answer_summary": "包含 nvme 資料夾和 install.sh 檔案",
  "category": "測試工具",
  "tags": ["UNH-IOL", "目錄結構"],
  "min_required_matches": 1
}
```

#### 題目 8-1 (簡單) 🆕
```json
{
  "question": "UNH-IOL 測試的密碼是什麼？",
  "question_type": "fact",
  "difficulty_level": "easy",
  "expected_document_ids": [10],
  "expected_keywords": ["UNH-IOL", "密碼", "sudo su", "1"],
  "expected_answer_summary": "密碼是 1",
  "category": "測試工具",
  "tags": ["UNH-IOL", "密碼", "登入"],
  "min_required_matches": 1
}
```

---

### 來源：CrystalDiskMark 5 (ID: 16)

#### 題目 9 (簡單)
```json
{
  "question": "執行 CrystalDiskMark 測試前，BIOS 設定中需要關閉什麼功能？",
  "question_type": "configuration",
  "difficulty_level": "easy",
  "expected_document_ids": [16],
  "expected_keywords": ["CrystalDiskMark", "BIOS", "Secure Boot", "Disabled"],
  "expected_answer_summary": "需要在 BIOS 設定中關閉 Secure Boot",
  "category": "測試準備",
  "tags": ["CrystalDiskMark", "BIOS", "設定"],
  "min_required_matches": 1
}
```

#### 題目 10 (中等)
```json
{
  "question": "CrystalDiskMark 測試過程中不應該出現哪些異常？",
  "question_type": "troubleshooting",
  "difficulty_level": "medium",
  "expected_document_ids": [16],
  "expected_keywords": ["BSOD", "Black screen", "hang up"],
  "expected_answer_summary": "不應該出現 BSOD、Black screen、hang up 等異常",
  "category": "問題排除",
  "tags": ["CrystalDiskMark", "異常", "測試"],
  "min_required_matches": 1
}
```

#### 題目 10-1 (中等) 🆕
```json
{
  "question": "CrystalDiskMark 5 的完整測試流程或 SOP 是什麼？",
  "question_type": "procedure",
  "difficulty_level": "medium",
  "expected_document_ids": [16],
  "expected_keywords": ["CrystalDiskMark", "SOP", "測試流程", "BIOS", "Driver"],
  "expected_answer_summary": "包含 BIOS 設定（關閉 Secure Boot）、Driver 安裝、執行測試、避免異常等步驟",
  "category": "測試執行",
  "tags": ["CrystalDiskMark", "SOP", "流程"],
  "min_required_matches": 1
}
```

---

### 來源：Burn in Test (ID: 15)

#### 題目 10-2 (中等) 🆕
```json
{
  "question": "Burn in Test 的測試 SOP 或操作流程是什麼？",
  "question_type": "procedure",
  "difficulty_level": "medium",
  "expected_document_ids": [15],
  "expected_keywords": ["Burn in Test", "SOP", "測試流程", "壓力測試"],
  "expected_answer_summary": "Burn in Test 的完整操作步驟，包含軟體啟動、測試項目選擇、參數設定、執行測試等流程",
  "category": "測試執行",
  "tags": ["Burn in Test", "SOP", "壓力測試"],
  "min_required_matches": 1
}
```

---

### 來源：多篇文章（對比類問題）

#### 題目 11 (困難)
```json
{
  "question": "ULINK 和 Oakgate 這兩種測試工具的主要差異是什麼？",
  "question_type": "comparison",
  "difficulty_level": "hard",
  "expected_document_ids": [28, 29],
  "expected_keywords": ["ULINK", "Oakgate", "測試", "DriveMaster"],
  "acceptable_document_ids": [28, 29, 35],
  "category": "工具對比",
  "tags": ["ULINK", "Oakgate", "對比"],
  "min_required_matches": 2
}
```

#### 題目 12 (困難)
```json
{
  "question": "測試 NVMe SSD 時，可以使用哪些工具？各有什麼特點？",
  "question_type": "comparison",
  "difficulty_level": "hard",
  "expected_document_ids": [34, 10, 29, 30],  # PyNvme3, UNH-IOL, Oakgate, SNVT2
  "expected_keywords": ["NVMe", "PyNvme3", "UNH-IOL", "測試工具"],
  "category": "工具對比",
  "tags": ["NVMe", "測試工具", "對比"],
  "min_required_matches": 2
}
```

---

## 🔧 實作工具

### 題目生成腳本範例

```python
# backend/scripts/generate_benchmark_test_cases.py

from api.models import ProtocolGuide, BenchmarkTestCase
import re

class TestCaseGenerator:
    """測試題目生成器"""
    
    def __init__(self):
        self.guides = ProtocolGuide.objects.all()
        self.generated_cases = []
    
    def generate_all(self):
        """生成所有題目"""
        for guide in self.guides:
            print(f"處理文章: {guide.title} (ID: {guide.id})")
            
            # 事實查詢
            self.generated_cases.extend(
                self.generate_fact_questions(guide)
            )
            
            # 程序查詢
            if self._has_procedure_content(guide):
                self.generated_cases.extend(
                    self.generate_procedure_questions(guide)
                )
            
            # 路徑查詢
            if self._has_path_content(guide):
                self.generated_cases.extend(
                    self.generate_path_questions(guide)
                )
        
        return self.generated_cases
    
    def generate_fact_questions(self, guide):
        """生成事實查詢題目"""
        questions = []
        
        # 範本 1: 基本功能
        questions.append({
            'question': f"{guide.title} 的主要功能是什麼？",
            'question_type': 'fact',
            'difficulty_level': 'easy',
            'expected_document_ids': [guide.id],
            'category': '測試工具',
        })
        
        # 範本 2: 使用場景
        if '測試' in guide.content or 'Test' in guide.content:
            questions.append({
                'question': f"什麼情況下需要使用 {guide.title}？",
                'question_type': 'fact',
                'difficulty_level': 'medium',
                'expected_document_ids': [guide.id],
                'category': '測試場景',
            })
        
        return questions
    
    def generate_procedure_questions(self, guide):
        """生成程序查詢題目"""
        questions = []
        
        # 檢測 SOP 標記
        if 'SOP' in guide.content or '步驟' in guide.content:
            questions.append({
                'question': f"如何執行 {guide.title} 測試？",
                'question_type': 'procedure',
                'difficulty_level': 'medium',
                'expected_document_ids': [guide.id],
                'category': '測試執行',
            })
        
        # 檢測安裝步驟
        if '安裝' in guide.content or 'install' in guide.content.lower():
            questions.append({
                'question': f"如何安裝和設定 {guide.title}？",
                'question_type': 'procedure',
                'difficulty_level': 'medium',
                'expected_document_ids': [guide.id],
                'category': '安裝設定',
            })
        
        return questions
    
    def generate_path_questions(self, guide):
        """生成路徑查詢題目"""
        questions = []
        
        # 提取 NAS 路徑
        nas_paths = re.findall(r'\\\\nas\d+\\[^\s]+', guide.content)
        if nas_paths:
            questions.append({
                'question': f"{guide.title} 的檔案存放在哪個 NAS 路徑？",
                'question_type': 'path',
                'difficulty_level': 'easy',
                'expected_document_ids': [guide.id],
                'expected_keywords': ['nas', guide.title],
                'category': '資源路徑',
            })
        
        # 提取網址
        urls = re.findall(r'https?://[^\s]+', guide.content)
        if urls:
            questions.append({
                'question': f"{guide.title} 的官方文件或下載網址是什麼？",
                'question_type': 'path',
                'difficulty_level': 'easy',
                'expected_document_ids': [guide.id],
                'category': '資源路徑',
            })
        
        return questions
    
    def _has_procedure_content(self, guide):
        """判斷是否包含程序性內容"""
        keywords = ['步驟', 'Step', 'SOP', '安裝', 'install', '設定', 'setting']
        return any(keyword in guide.content for keyword in keywords)
    
    def _has_path_content(self, guide):
        """判斷是否包含路徑資訊"""
        return '\\\\nas' in guide.content or 'http' in guide.content
    
    def save_to_database(self):
        """儲存題目到資料庫"""
        for case_data in self.generated_cases:
            BenchmarkTestCase.objects.create(**case_data)
        
        print(f"✅ 已生成 {len(self.generated_cases)} 題測試題目")

# 使用方式
if __name__ == '__main__':
    generator = TestCaseGenerator()
    generator.generate_all()
    generator.save_to_database()
```

---

## 📈 預期成果

### 量化目標
- ✅ 總題目數：150-200 題
- ✅ 文章覆蓋率：100% (所有 17 篇文章)
- ✅ 難度分布：簡單 40%, 中等 45%, 困難 15%
- ✅ 類型多樣性：至少 8 種題目類型

### 質化目標
- ✅ **真實性**：反映實際用戶查詢場景
- ✅ **完整性**：涵蓋文章的核心知識點
- ✅ **可驗證性**：每題都有明確的評分標準
- ✅ **可擴展性**：新增文章時可輕鬆生成對應題目

### 使用場景
1. **開發階段**：驗證搜尋演算法改進效果
2. **回歸測試**：確保新版本不降低搜尋品質
3. **問題診斷**：發現特定類型查詢的弱點
4. **知識庫評估**：識別文檔內容的不足之處

---

## ⏭️ 下一步行動

### 立即開始（本週）
1. ✅ 確認出題策略和範例題目
2. ✅ 選擇 10 篇核心文章
3. ✅ 手動產出首批 50 題高品質題目
4. ✅ 使用現有搜尋系統驗證題目品質

### 短期計劃（2 週內）
1. ✅ 開發半自動題目生成工具
2. ✅ 擴充題庫至 100 題
3. ✅ 建立題目品質檢查流程
4. ✅ 整合到跑分系統

### 中期計劃（4 週內）
1. ✅ 實作全自動題目生成引擎
2. ✅ 達成 150+ 題目標
3. ✅ 建立持續更新機制
4. ✅ 完成首輪完整跑分測試

---

**📅 更新日期**: 2025-11-21  
**📝 版本**: v1.0  
**✍️ 作者**: AI Platform Team  
**🎯 用途**: Protocol Assistant 搜尋演算法跑分系統 - 測試題庫規劃
