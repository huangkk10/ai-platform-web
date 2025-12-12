# Markdown 編輯器滾輪同步設計文檔

## 📋 文檔資訊
- **建立日期**：2025-12-12
- **版本**：V16 已實作
- **檔案位置**：`frontend/src/components/editor/MarkdownEditorLayout.jsx`
- **狀態**：✅ 實作完成，待測試

---

## 🎯 目標

當用戶滾動**左邊編輯器**時，**右邊預覽區**應該顯示對應的內容位置，實現「**內容對齊**」而非單純的「比例對齊」。

### 期望效果
- 編輯器滾到 `## Chromebook NB` → 預覽區顯示 `Chromebook NB` 標題
- 編輯器滾到某張圖片的位置 → 預覽區顯示該圖片
- Summary 區塊應該正確對應，不會造成後續內容錯位

---

## 📊 問題分析

### 左右兩邊的高度差異來源

| 元素類型 | 左邊編輯器高度 | 右邊預覽區高度 | 高度差異 |
|---------|--------------|--------------|---------|
| `:::summary...:::` | N 行 × 24px（約 200-400px） | 渲染後區塊（約 300-500px） | **預覽區更高** |
| `![IMG:xxx]` 圖片標記 | 1 行 × 24px | 圖片渲染（約 100-120px） | **預覽區更高** |
| 一般文字 | 每行 24px | 每行約 24px | **相近** |
| 標題 `## xxx` | 1 行 × 24px | 渲染後標題（約 30-40px） | **略有差異** |
| 程式碼區塊 | N 行 × 24px | 渲染後區塊（含邊框padding） | **可能不同** |

### 為什麼「純比例同步」不準確？

```
假設總高度：
- 編輯器：1000px
- 預覽區：1500px（因為 summary 和圖片渲染後變大）

純比例同步問題：
- 編輯器滾到 50%（500px）
- 預覽區也滾到 50%（750px）
- 但 500px 在編輯器可能是 "## Chrome Server"
- 而 750px 在預覽區可能已經是 "## Chrome Offline" 了

原因：Summary 在編輯器佔 20%，但在預覽區可能佔 30%
導致後續內容的比例位置全部錯開
```

---

## 🧠 解決方案設計

### 方案：區段映射同步（V16）

#### 核心思路
**不用「總高度比例」，改用「內容區段映射」**

將內容分成多個區段，每個區段獨立計算比例：

```
┌─────────────────────────────────────────────────────────────┐
│                     內容區段示意圖                           │
├─────────────────────────┬───────────────────────────────────┤
│      左邊編輯器          │         右邊預覽區                 │
├─────────────────────────┼───────────────────────────────────┤
│ [區段0: Summary前]       │ [區段0: Summary前]                 │
│ Line 0-5: 空白或標題     │ 對應內容                          │
├─────────────────────────┼───────────────────────────────────┤
│ [區段1: Summary區塊]     │ [區段1: Summary渲染區塊]           │
│ Line 6: :::summary      │ ┌─────────────────────────┐       │
│ Line 7: # AVL SOP       │ │ 📋 # AVL SOP            │       │
│ Line 8: ## Chromebook   │ │ • AVL SOP               │       │
│ ...                     │ │ ■ Chromebook NB         │       │
│ Line 25: :::            │ │ ■ Chrome image 燒錄      │       │
│                         │ │ ...                     │       │
│                         │ └─────────────────────────┘       │
├─────────────────────────┼───────────────────────────────────┤
│ [區段2: Summary後內容]   │ [區段2: Summary後內容]             │
│ Line 26: ## Chromebook  │ <h2>Chromebook NB</h2>            │
│ Line 27-50: 內容...     │ 內容渲染...                       │
│ Line 51: [IMG:163]      │ <img src="...">                   │
│ Line 52-100: 更多內容   │ 更多內容渲染...                   │
└─────────────────────────┴───────────────────────────────────┘
```

#### 同步邏輯

```javascript
// 當編輯器滾動時
function onEditorScroll(editorScrollTop) {
  const currentLine = editorScrollTop / lineHeight;
  
  // 判斷當前在哪個區段
  if (currentLine < summaryStartLine) {
    // 區段0：Summary 前
    // 用這個區段的比例同步
    ratio = editorScrollTop / summaryStartPx;
    previewScrollTop = ratio * previewSummaryStartPx;
    
  } else if (currentLine <= summaryEndLine) {
    // 區段1：在 Summary 區塊內
    // 線性映射到預覽區的 Summary 區塊內
    progress = (editorScrollTop - summaryStartPx) / summaryEditorHeight;
    previewScrollTop = previewSummaryStartPx + progress * previewSummaryHeight;
    
  } else {
    // 區段2：Summary 後
    // 用「扣除 Summary 後的內容」比例同步
    editorAfterSummary = editorScrollTop - summaryEndPx;
    editorContentAfterSummary = editorTotalHeight - summaryEndPx;
    previewContentAfterSummary = previewTotalHeight - previewSummaryEndPx;
    
    ratio = editorAfterSummary / editorContentAfterSummary;
    previewScrollTop = previewSummaryEndPx + ratio * previewContentAfterSummary;
  }
}
```

---

## 📐 詳細計算方法

### Step 1：解析編輯器內容結構

```javascript
function parseEditorContent(content, editorEl) {
  const lines = content.split('\n');
  const lineHeight = editorEl.scrollHeight / lines.length;
  
  const structure = {
    summary: null,      // { startLine, endLine, startPx, endPx, heightPx }
    images: [],         // [{ line, heightPx }]
    headings: [],       // [{ line, level, text, heightPx }]
  };
  
  let inSummary = false;
  let summaryStart = -1;
  
  lines.forEach((line, idx) => {
    // 檢測 Summary 開始
    if (line.trim().startsWith(':::summary')) {
      inSummary = true;
      summaryStart = idx;
    }
    
    // 檢測 Summary 結束
    if (inSummary && line.trim() === ':::' && idx !== summaryStart) {
      structure.summary = {
        startLine: summaryStart,
        endLine: idx,
        startPx: summaryStart * lineHeight,
        endPx: (idx + 1) * lineHeight,
        heightPx: (idx - summaryStart + 1) * lineHeight
      };
      inSummary = false;
    }
    
    // 檢測圖片
    if (line.match(/!\[.*?\]\(.*?\)|\[IMG:\d+\]/)) {
      structure.images.push({
        line: idx,
        heightPx: lineHeight
      });
    }
    
    // 檢測標題
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      structure.headings.push({
        line: idx,
        level: headingMatch[1].length,
        text: headingMatch[2].trim(),
        heightPx: lineHeight
      });
    }
  });
  
  return structure;
}
```

### Step 2：從預覽區 DOM 取得對應元素位置

```javascript
function parsePreviewStructure(previewEl) {
  const structure = {
    summary: null,
    images: [],
    headings: [],
  };
  
  // Summary 區塊
  const summaryBlock = previewEl.querySelector('.markdown-summary-block');
  if (summaryBlock) {
    structure.summary = {
      startPx: summaryBlock.offsetTop,
      endPx: summaryBlock.offsetTop + summaryBlock.offsetHeight,
      heightPx: summaryBlock.offsetHeight
    };
  }
  
  // 標題元素
  previewEl.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(el => {
    structure.headings.push({
      level: parseInt(el.tagName.charAt(1)),
      text: el.textContent.trim(),
      offsetTop: el.offsetTop,
      heightPx: el.offsetHeight
    });
  });
  
  // 圖片元素
  previewEl.querySelectorAll('img').forEach(el => {
    structure.images.push({
      offsetTop: el.offsetTop,
      heightPx: el.offsetHeight
    });
  });
  
  return structure;
}
```

### Step 3：滾動同步計算

```javascript
function calculatePreviewScrollTop(editorScrollTop, editorStructure, previewStructure, editorEl, previewEl) {
  const editorMax = editorEl.scrollHeight - editorEl.clientHeight;
  const previewMax = previewEl.scrollHeight - previewEl.clientHeight;
  
  // 沒有 Summary 的情況：純比例同步
  if (!editorStructure.summary || !previewStructure.summary) {
    return (editorScrollTop / editorMax) * previewMax;
  }
  
  const editorSummary = editorStructure.summary;
  const previewSummary = previewStructure.summary;
  
  // 區段判斷
  if (editorScrollTop < editorSummary.startPx) {
    // 區段0：Summary 前
    if (editorSummary.startPx === 0) return 0;
    const ratio = editorScrollTop / editorSummary.startPx;
    return ratio * previewSummary.startPx;
    
  } else if (editorScrollTop < editorSummary.endPx) {
    // 區段1：Summary 內
    const progress = (editorScrollTop - editorSummary.startPx) / editorSummary.heightPx;
    return previewSummary.startPx + progress * previewSummary.heightPx;
    
  } else {
    // 區段2：Summary 後
    const editorAfter = editorScrollTop - editorSummary.endPx;
    const editorRemaining = editorMax - editorSummary.endPx;
    const previewRemaining = previewMax - previewSummary.endPx;
    
    if (editorRemaining <= 0) return previewSummary.endPx;
    
    const ratio = editorAfter / editorRemaining;
    return previewSummary.endPx + ratio * previewRemaining;
  }
}
```

---

## 🔧 實作細節

### 防止回拉的機制

```javascript
let scrollSource = null;  // 'editor' | 'preview' | null
let resetTimer = null;

function onEditorScroll() {
  // 如果是由 preview 觸發的程式化滾動，忽略
  if (scrollSource === 'preview') return;
  
  scrollSource = 'editor';
  clearTimeout(resetTimer);
  
  // 計算並設定預覽區滾動位置
  const targetScrollTop = calculatePreviewScrollTop(...);
  previewEl.scrollTop = targetScrollTop;
  
  // 50ms 後重置標記，允許下次滾動
  resetTimer = setTimeout(() => {
    scrollSource = null;
  }, 50);
}

function onPreviewScroll() {
  // 如果是由 editor 觸發的程式化滾動，忽略
  if (scrollSource === 'editor') return;
  
  scrollSource = 'preview';
  clearTimeout(resetTimer);
  
  // 反向計算並設定編輯器滾動位置
  const targetScrollTop = calculateEditorScrollTop(...);
  editorEl.scrollTop = targetScrollTop;
  
  resetTimer = setTimeout(() => {
    scrollSource = null;
  }, 50);
}
```

### 效能優化

```javascript
// 1. 使用 passive 事件監聽
editorEl.addEventListener('scroll', onEditorScroll, { passive: true });

// 2. 緩存結構解析結果（內容變化時才重新解析）
let cachedEditorStructure = null;
let cachedPreviewStructure = null;
let lastContent = null;

function getStructures() {
  const content = formData?.content || '';
  
  if (content !== lastContent) {
    cachedEditorStructure = parseEditorContent(content, editorEl);
    cachedPreviewStructure = parsePreviewStructure(previewEl);
    lastContent = content;
  }
  
  return { editor: cachedEditorStructure, preview: cachedPreviewStructure };
}

// 3. 使用 requestAnimationFrame 節流（可選）
let rafId = null;

function onEditorScroll() {
  if (rafId) return;
  
  rafId = requestAnimationFrame(() => {
    // 執行同步邏輯
    rafId = null;
  });
}
```

---

## ❓ 待確認事項

### 1. 同步精度選擇

| 選項 | 說明 | 複雜度 | 效果 |
|------|------|--------|------|
| **A) 標題對齊** | 滾到 `## Chromebook NB` 就對齊該標題 | 高 | 最精確 |
| **B) 區段比例** | Summary 前/中/後分段比例同步 | 中 | 較準確 |
| **C) 大致對齊** | 只處理 Summary，其他純比例 | 低 | 基本準確 |

**建議**：先實作 **B) 區段比例**，測試效果後再決定是否升級到 A

### 2. 圖片處理

| 選項 | 說明 |
|------|------|
| **暫時忽略** | 先不處理圖片高度差異 |
| **一併處理** | 將圖片也視為獨立區段 |

**建議**：先暫時忽略，確認 Summary 處理正確後再加入圖片

### 3. 回拉容忍度

| 選項 | 說明 |
|------|------|
| **完全不能回拉** | 用戶滾動方向必須一致 |
| **允許輕微調整** | 為了對齊可以有小幅位置修正 |

**建議**：使用 scrollSource 機制，應該可以避免回拉

---

## 📝 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| V9 | 2025-12-12 | 業界推薦方案：移除監聽器後設定 scrollTop |
| V10 | 2025-12-12 | 圖片高度補償方案 |
| V11 | 2025-12-12 | 純比例同步（最簡版） |
| V12 | 2025-12-12 | 智能補償同步 |
| V13 | 2025-12-12 | 純比例同步（重構） |
| V14 | 2025-12-12 | 使用 MdEditor 原生同步 |
| V15 | 2025-12-12 | 排除 Summary 的比例同步 |
| V16 | 2025-12-12 | ✅ 區段映射同步 + 單向同步 + 閾值控制（已實作） |
| V17 | 規劃中 | 多錨點映射同步（標題級別精確對齊） |

---

## 🚀 V17 規劃：多錨點映射同步

### 📋 問題回顧

V16 的限制：
- ✅ 正確處理 Summary 區塊的高度差異
- ❌ Summary 後的區段仍使用「純比例同步」
- ❌ 程式碼區塊、標題等元素的高度差異未處理
- ❌ 文檔越長，累積誤差越大

### 🎯 V17 目標

**使用「標題」作為多個錨點，建立編輯器 ↔ 預覽區的精確映射**

```
V16 只有 1 個錨點（Summary）：
┌─────────────────────────────────────────────────────────┐
│  [Summary 前] → [Summary] → [Summary 後：純比例同步]     │
│                    ↑                                    │
│                唯一錨點                                  │
└─────────────────────────────────────────────────────────┘

V17 多錨點映射：
┌─────────────────────────────────────────────────────────┐
│  [Summary] → [## 標題1] → [### 標題2] → [## 標題3] → ...│
│      ↑           ↑            ↑            ↑            │
│   錨點0       錨點1        錨點2        錨點3           │
│                                                         │
│  每個錨點之間使用「區段內比例」同步                       │
└─────────────────────────────────────────────────────────┘
```

### 🧠 核心思路

1. **解析所有標題**：找出編輯器中所有 `#`、`##`、`###` 標題的行號
2. **匹配預覽區標題**：找出預覽區對應的 `<h1>`、`<h2>`、`<h3>` 元素位置
3. **建立錨點映射表**：`[{ editorPx, previewPx, text }, ...]`
4. **區段內插值**：滾動時找到前後兩個錨點，在區段內做比例計算

### 📊 資料結構設計

```typescript
interface Anchor {
  type: 'summary' | 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
  text: string;           // 標題文字（用於匹配）
  editorLine: number;     // 編輯器行號
  editorPx: number;       // 編輯器位置（px）
  previewPx: number;      // 預覽區位置（px）
}

interface AnchorMap {
  anchors: Anchor[];      // 所有錨點，按 editorPx 排序
  editorMax: number;      // 編輯器最大滾動值
  previewMax: number;     // 預覽區最大滾動值
}
```

### 🔧 同步算法

```javascript
/**
 * V17 多錨點映射同步算法
 */
function calculatePreviewTarget(editorScrollTop, anchorMap) {
  const { anchors, editorMax, previewMax } = anchorMap;
  
  // 沒有錨點：退化為純比例
  if (anchors.length === 0) {
    return (editorScrollTop / editorMax) * previewMax;
  }
  
  // 找到當前位置的前後錨點
  let prevAnchor = null;
  let nextAnchor = null;
  
  for (let i = 0; i < anchors.length; i++) {
    if (anchors[i].editorPx <= editorScrollTop) {
      prevAnchor = anchors[i];
    } else {
      nextAnchor = anchors[i];
      break;
    }
  }
  
  // 情況 1：在第一個錨點之前
  if (!prevAnchor && nextAnchor) {
    const ratio = editorScrollTop / nextAnchor.editorPx;
    return ratio * nextAnchor.previewPx;
  }
  
  // 情況 2：在最後一個錨點之後
  if (prevAnchor && !nextAnchor) {
    const editorAfter = editorScrollTop - prevAnchor.editorPx;
    const editorRemaining = editorMax - prevAnchor.editorPx;
    const previewRemaining = previewMax - prevAnchor.previewPx;
    
    if (editorRemaining <= 0) return prevAnchor.previewPx;
    
    const ratio = editorAfter / editorRemaining;
    return prevAnchor.previewPx + ratio * previewRemaining;
  }
  
  // 情況 3：在兩個錨點之間（最常見）
  if (prevAnchor && nextAnchor) {
    const editorRange = nextAnchor.editorPx - prevAnchor.editorPx;
    const previewRange = nextAnchor.previewPx - prevAnchor.previewPx;
    
    if (editorRange <= 0) return prevAnchor.previewPx;
    
    const progress = (editorScrollTop - prevAnchor.editorPx) / editorRange;
    return prevAnchor.previewPx + progress * previewRange;
  }
  
  // Fallback
  return (editorScrollTop / editorMax) * previewMax;
}
```

### 📐 錨點解析實作

```javascript
/**
 * 解析編輯器中的所有錨點（標題）
 */
function parseEditorAnchors(content, editorEl) {
  const lines = content.split('\n');
  const totalLines = lines.length;
  const lineHeight = editorEl.scrollHeight / totalLines;
  
  const anchors = [];
  
  lines.forEach((line, idx) => {
    // 檢測標題 (# ~ ######)
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const text = headingMatch[2].trim();
      
      anchors.push({
        type: `h${level}`,
        text: text,
        editorLine: idx,
        editorPx: idx * lineHeight,
        previewPx: null  // 稍後填入
      });
    }
  });
  
  return anchors;
}

/**
 * 從預覽區 DOM 匹配錨點位置
 */
function matchPreviewAnchors(anchors, previewEl) {
  const headingEls = previewEl.querySelectorAll('h1, h2, h3, h4, h5, h6');
  const headingMap = new Map();
  
  // 建立預覽區標題 text → offsetTop 映射
  headingEls.forEach(el => {
    const text = el.textContent.trim();
    // 處理可能的重複標題：使用第一個匹配
    if (!headingMap.has(text)) {
      headingMap.set(text, el.offsetTop);
    }
  });
  
  // 匹配編輯器錨點到預覽區位置
  anchors.forEach(anchor => {
    if (headingMap.has(anchor.text)) {
      anchor.previewPx = headingMap.get(anchor.text);
    } else {
      // 找不到匹配，嘗試部分匹配
      for (const [text, offsetTop] of headingMap) {
        if (text.includes(anchor.text) || anchor.text.includes(text)) {
          anchor.previewPx = offsetTop;
          break;
        }
      }
    }
  });
  
  // 過濾掉沒有匹配到的錨點
  return anchors.filter(a => a.previewPx !== null);
}
```

### 🔄 整合 Summary 區塊

```javascript
/**
 * 完整的錨點映射建立流程
 */
function buildAnchorMap(content, editorEl, previewEl) {
  const anchors = [];
  
  // 1. 解析 Summary 區塊（如果有）
  const summaryAnchor = parseSummaryAnchor(content, editorEl, previewEl);
  if (summaryAnchor) {
    anchors.push(summaryAnchor);
  }
  
  // 2. 解析所有標題錨點
  const headingAnchors = parseEditorAnchors(content, editorEl);
  const matchedAnchors = matchPreviewAnchors(headingAnchors, previewEl);
  anchors.push(...matchedAnchors);
  
  // 3. 按 editorPx 排序
  anchors.sort((a, b) => a.editorPx - b.editorPx);
  
  // 4. 去除 Summary 內部的標題（避免重複）
  const filteredAnchors = filterAnchorsInsideSummary(anchors, summaryAnchor);
  
  return {
    anchors: filteredAnchors,
    editorMax: editorEl.scrollHeight - editorEl.clientHeight,
    previewMax: previewEl.scrollHeight - previewEl.clientHeight
  };
}
```

### 📊 視覺化示例

```
假設文檔結構：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

編輯器                          預覽區
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Line 0:   :::summary             [0px]    ┌─────────────────┐
Line 1-20: ...                            │ Summary Block   │
Line 21:  :::                             │ (400px 高)      │
                                          └─────────────────┘
                                 [400px]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Line 22:  ## 如何確認 Hardware   [528px]  <h2>如何確認 Hardware [420px]
Line 23-40: 內容 + 程式碼                  內容 + 程式碼區塊
                                          (預覽區更高)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Line 41:  ### 如何確認 AVL       [984px]  <h3>如何確認 AVL    [850px]
Line 42-60: 內容 + 程式碼                  內容 + 程式碼區塊
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Line 61:  ### 利用 make_dev      [1464px] <h3>利用 make_dev  [1320px]
...

錨點映射表：
┌─────────────────────────────────────────────────────────┐
│ Anchor 0: Summary      | editor: 0px    | preview: 0px  │
│ Anchor 1: ## 如何確認  | editor: 528px  | preview: 420px│
│ Anchor 2: ### 如何確認 | editor: 984px  | preview: 850px│
│ Anchor 3: ### 利用     | editor: 1464px | preview: 1320px│
│ ...                                                     │
└─────────────────────────────────────────────────────────┘

當編輯器滾動到 750px 時（在 Anchor 1 和 Anchor 2 之間）：
- prevAnchor = Anchor 1 (editor: 528px, preview: 420px)
- nextAnchor = Anchor 2 (editor: 984px, preview: 850px)
- editorRange = 984 - 528 = 456px
- previewRange = 850 - 420 = 430px
- progress = (750 - 528) / 456 = 0.487
- targetPreview = 420 + 0.487 × 430 = 629px

這樣每個區段都有精確的映射！
```

### ⚡ 效能優化

```javascript
// 1. 緩存錨點映射（內容變化時才重建）
let cachedAnchorMap = null;
let cachedContent = null;

function getAnchorMap() {
  const content = formData?.content || '';
  
  if (content !== cachedContent) {
    cachedAnchorMap = buildAnchorMap(content, editorEl, previewEl);
    cachedContent = content;
    console.log(`📍 V17: 建立 ${cachedAnchorMap.anchors.length} 個錨點`);
  }
  
  return cachedAnchorMap;
}

// 2. 使用二分搜尋找錨點（大量錨點時優化）
function findAnchorRange(anchors, editorScrollTop) {
  let left = 0;
  let right = anchors.length - 1;
  let prevIdx = -1;
  
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    if (anchors[mid].editorPx <= editorScrollTop) {
      prevIdx = mid;
      left = mid + 1;
    } else {
      right = mid - 1;
    }
  }
  
  return {
    prev: prevIdx >= 0 ? anchors[prevIdx] : null,
    next: prevIdx + 1 < anchors.length ? anchors[prevIdx + 1] : null
  };
}
```

### 🧪 測試計劃

| 測試場景 | 預期結果 |
|---------|---------|
| 有 Summary + 多標題 | 所有標題對齊正確 |
| 無 Summary + 多標題 | 標題作為錨點，對齊準確 |
| 標題之間有大量程式碼 | 區段內比例同步，誤差最小化 |
| 快速滾動跨多個標題 | 平滑過渡，無跳躍 |
| 編輯內容後立即滾動 | 錨點映射自動更新 |
| 重複標題文字 | 使用第一個匹配 |

### ✅ V17 實作檢查清單

- [ ] 實作 `parseEditorAnchors()` - 解析編輯器標題
- [ ] 實作 `matchPreviewAnchors()` - 匹配預覽區標題
- [ ] 實作 `buildAnchorMap()` - 建立完整映射表
- [ ] 實作 `calculatePreviewTarget()` V17 版本
- [ ] 整合 Summary 區塊處理
- [ ] 加入錨點映射緩存
- [ ] 加入二分搜尋優化（可選）
- [ ] 測試：多標題文檔
- [ ] 測試：程式碼密集文檔
- [ ] 測試：無標題文檔（退化為純比例）
- [ ] 測試：確認無回拉現象

### 🎯 預期效果

| 版本 | 對齊精度 | 處理範圍 |
|------|---------|---------|
| V15 | ⭐⭐ | 只處理 Summary |
| V16 | ⭐⭐⭐ | Summary + 區段比例 |
| **V17** | ⭐⭐⭐⭐⭐ | **所有標題作為錨點** |

V17 應該能夠解決截圖中看到的對齊問題，因為每個 `###` 標題都會成為精確的對齊錨點。

---

## 🔬 回拉問題深入分析

### 什麼是「回拉」？

用戶向下滾動時，頁面突然向上跳動（或反方向移動），造成不順暢的體驗。

### 回拉發生的根本原因

#### 情境 1：雙向監聽的循環觸發

```
用戶滾動左邊 Editor
    ↓
觸發 onEditorScroll()
    ↓
程式設定 previewEl.scrollTop = X
    ↓
觸發 onPreviewScroll()  ← 問題！這是程式觸發的，不是用戶
    ↓
程式設定 editorEl.scrollTop = Y  ← Y 可能和原本位置不同
    ↓
觸發 onEditorScroll()  ← 又觸發！
    ↓
無限循環或位置抖動
```

**解決方案**：使用 `scrollSource` 標記區分「用戶滾動」和「程式滾動」

#### 情境 2：標題對齊的「跳躍」問題

```
假設標題對齊邏輯：
- 找到當前可見的標題
- 讓預覽區滾動到對應標題

問題：
1. 用戶滾動到 Line 50（在 ## Heading A 和 ## Heading B 之間）
2. 程式判斷「最近的標題是 ## Heading A」
3. 預覽區滾動到 Heading A 的位置
4. 但用戶繼續向下滾動，還是在 A-B 之間
5. 程式還是認為「最近的標題是 ## Heading A」
6. 預覽區位置不變...

然後：
7. 用戶滾動跨過了 ## Heading B
8. 程式突然判斷「最近的標題變成 ## Heading B」
9. 預覽區「跳躍」到 Heading B 的位置
10. 這個跳躍就像是「回拉」或「閃跳」
```

**問題本質**：標題對齊是「離散」的，但用戶滾動是「連續」的

#### 情境 3：行對齊的計算誤差

```
行對齊邏輯：
- 計算編輯器當前行號
- 找到預覽區對應的行位置
- 滾動到該位置

問題：
1. 編輯器 lineHeight 不是精確的 24px（可能是 23.5px 或 24.2px）
2. 預覽區每行高度不一致（標題、圖片、段落都不同）
3. 累積誤差導致位置越來越偏

例如：
- 編輯器計算：Line 100 = 2400px
- 實際預覽區 Line 100 對應位置 = 2800px
- 但簡單的行對齊算出來可能是 2600px
- 誤差 200px 導致內容不對齊
```

**問題本質**：行高假設不準確，累積誤差

#### 情境 4：同步延遲造成的抖動

```
用戶快速滾動：
T=0ms: 用戶開始滾動，editorScrollTop = 100
T=5ms: 用戶繼續滾動，editorScrollTop = 150
T=10ms: 之前的同步邏輯執行，設定 previewScrollTop（基於 100 計算）
T=15ms: 用戶繼續滾動，editorScrollTop = 200
T=20ms: 觸發 onPreviewScroll（因為 T=10ms 的設定）
T=25ms: 反向同步，editorScrollTop 被設定為舊值
→ 用戶感覺被「拉回去」
```

**問題本質**：非同步執行 + 快速滾動 = 狀態不一致

---

## 🛠️ 回拉問題解決方案

### 方案 A：scrollSource 標記（已實作）

```javascript
let scrollSource = null;
let resetTimer = null;

function onEditorScroll() {
  if (scrollSource === 'preview') return; // 忽略程式觸發的
  
  scrollSource = 'editor';
  clearTimeout(resetTimer);
  
  // 執行同步...
  previewEl.scrollTop = targetPosition;
  
  resetTimer = setTimeout(() => {
    scrollSource = null;
  }, 50);
}
```

**優點**：簡單有效，避免循環觸發
**缺點**：50ms 內的連續滾動可能被忽略

### 方案 B：只追蹤滾動方向

```javascript
let lastEditorScrollTop = 0;
let lastPreviewScrollTop = 0;

function onEditorScroll() {
  const currentScrollTop = editorEl.scrollTop;
  const scrollDirection = currentScrollTop > lastEditorScrollTop ? 'down' : 'up';
  
  // 計算目標位置
  const targetPosition = calculateTarget(currentScrollTop);
  
  // 檢查：目標位置的方向是否和用戶滾動方向一致？
  const targetDirection = targetPosition > lastPreviewScrollTop ? 'down' : 'up';
  
  if (scrollDirection !== targetDirection) {
    // 方向不一致！這會造成回拉感
    // 選擇 1：不同步（保持預覽區不動）
    // 選擇 2：只移動一小步，不要跳太遠
    return;
  }
  
  previewEl.scrollTop = targetPosition;
  lastEditorScrollTop = currentScrollTop;
  lastPreviewScrollTop = targetPosition;
}
```

**優點**：確保同步方向和用戶意圖一致
**缺點**：可能造成短暫的不對齊

### 方案 C：平滑過渡而非瞬間跳轉

```javascript
function smoothScrollTo(element, targetPosition, duration = 100) {
  const startPosition = element.scrollTop;
  const distance = targetPosition - startPosition;
  const startTime = performance.now();
  
  function animate(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // 使用 easeOut 緩動函數
    const easeProgress = 1 - Math.pow(1 - progress, 3);
    
    element.scrollTop = startPosition + distance * easeProgress;
    
    if (progress < 1) {
      requestAnimationFrame(animate);
    }
  }
  
  requestAnimationFrame(animate);
}
```

**優點**：視覺上更平滑，減少跳躍感
**缺點**：增加複雜度，可能和快速滾動衝突

### 方案 D：閾值控制，小幅變化不同步

```javascript
const SYNC_THRESHOLD = 30; // 像素

function onEditorScroll() {
  const targetPosition = calculateTarget(editorEl.scrollTop);
  const currentDiff = Math.abs(previewEl.scrollTop - targetPosition);
  
  // 只有當差異超過閾值才同步
  if (currentDiff > SYNC_THRESHOLD) {
    previewEl.scrollTop = targetPosition;
  }
}
```

**優點**：減少不必要的微調，滾動更穩定
**缺點**：可能造成最多 30px 的對齊誤差

### 方案 E：單向同步（推薦）

```javascript
// 只做「編輯器 → 預覽區」的同步
// 不做「預覽區 → 編輯器」的反向同步

function onEditorScroll() {
  const targetPosition = calculateTarget(editorEl.scrollTop);
  previewEl.scrollTop = targetPosition;
}

// 預覽區滾動時，不做任何事
// 用戶想手動查看預覽區的其他位置是允許的
// 下次編輯器滾動時會重新同步
```

**優點**：
- 完全避免循環觸發
- 邏輯最簡單
- 用戶可以自由查看預覽區

**缺點**：
- 預覽區滾動不會影響編輯器
- 但這其實是可接受的，因為主要編輯行為在左邊

---

## 📋 V16 最終方案：區段比例 + 單向同步 + 閾值控制

### 設計原則

1. **單向同步**：只做 Editor → Preview，不做反向
2. **區段比例**：Summary 前/中/後 分段計算
3. **閾值控制**：差異 < 20px 不同步，避免微調抖動
4. **scrollSource 保護**：防止程式觸發的滾動事件

### 完整邏輯流程圖

```
┌─────────────────────────────────────────────────────────┐
│                  用戶滾動左邊編輯器                       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              觸發 onEditorScroll()                       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│     檢查 scrollSource === 'preview' ?                    │
│     （是否為程式觸發的反向滾動）                          │
├─────────────────────────────────────────────────────────┤
│  是 → 直接返回，不處理                                   │
│  否 → 繼續執行                                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              設定 scrollSource = 'editor'                │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              解析內容結構（緩存）                         │
│  - 找出 Summary 區塊位置                                 │
│  - 計算編輯器 lineHeight                                 │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              判斷當前滾動位置在哪個區段                    │
├─────────────────────────────────────────────────────────┤
│  區段 0：Summary 前                                      │
│  區段 1：Summary 中                                      │
│  區段 2：Summary 後                                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              根據區段計算預覽區目標位置                    │
├─────────────────────────────────────────────────────────┤
│  區段 0：                                               │
│    ratio = editorScrollTop / editorSummaryStart         │
│    target = ratio × previewSummaryStart                 │
│                                                         │
│  區段 1：                                               │
│    progress = (scrollTop - summaryStart) / summaryHeight│
│    target = previewSummaryStart + progress × previewH   │
│                                                         │
│  區段 2：                                               │
│    editorAfter = scrollTop - editorSummaryEnd           │
│    ratio = editorAfter / editorRemainingContent         │
│    target = previewSummaryEnd + ratio × previewRemaining│
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│     檢查差異：|previewScrollTop - target| > 20px ?      │
├─────────────────────────────────────────────────────────┤
│  是 → 執行同步：previewEl.scrollTop = target            │
│  否 → 不同步（避免微調抖動）                             │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              50ms 後重置 scrollSource = null             │
└─────────────────────────────────────────────────────────┘
```

### 預覽區滾動處理（可選）

```
┌─────────────────────────────────────────────────────────┐
│                  用戶滾動右邊預覽區                       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│     選項 A：完全不處理（推薦）                            │
│     - 用戶可自由查看預覽區                               │
│     - 下次編輯器滾動時會重新同步                          │
├─────────────────────────────────────────────────────────┤
│     選項 B：反向同步                                     │
│     - 需要 scrollSource 保護                            │
│     - 計算方式和上面相反                                 │
│     - 可能造成複雜度增加                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 V16 實作規格

### 配置參數

```javascript
const SCROLL_SYNC_CONFIG = {
  // 同步延遲（組件載入後多久開始綁定）
  bindDelayMs: 500,
  
  // scrollSource 重置延遲
  sourceResetMs: 50,
  
  // 同步閾值（差異小於此值不同步）
  syncThresholdPx: 20,
  
  // 是否啟用反向同步（Preview → Editor）
  enableReverseSync: false,
  
  // 編輯器預估行高
  estimatedLineHeight: 24,
};
```

### 核心函數簽名

```javascript
/**
 * 解析編輯器內容結構
 * @param {string} content - Markdown 內容
 * @param {HTMLElement} editorEl - 編輯器 textarea
 * @returns {EditorStructure}
 */
function parseEditorStructure(content, editorEl) { ... }

/**
 * 解析預覽區 DOM 結構
 * @param {HTMLElement} previewEl - 預覽區容器
 * @returns {PreviewStructure}
 */
function parsePreviewStructure(previewEl) { ... }

/**
 * 計算預覽區目標滾動位置
 * @param {number} editorScrollTop - 編輯器當前滾動位置
 * @param {EditorStructure} editorStruct - 編輯器結構
 * @param {PreviewStructure} previewStruct - 預覽區結構
 * @param {HTMLElement} editorEl - 編輯器元素
 * @param {HTMLElement} previewEl - 預覽區元素
 * @returns {number} 預覽區目標 scrollTop
 */
function calculatePreviewTarget(editorScrollTop, editorStruct, previewStruct, editorEl, previewEl) { ... }
```

### 資料結構定義

```typescript
interface EditorStructure {
  summary: {
    exists: boolean;
    startLine: number;
    endLine: number;
    startPx: number;
    endPx: number;
    heightPx: number;
  } | null;
  totalLines: number;
  lineHeight: number;
}

interface PreviewStructure {
  summary: {
    exists: boolean;
    startPx: number;
    endPx: number;
    heightPx: number;
  } | null;
  totalHeight: number;
}
```

---

## 🧪 方案 E 場景測試分析

### 測試場景與預期結果

#### 場景 (1)：滑鼠大幅度滾動往同一方向

```
用戶操作：在編輯器快速向下滾動（或向上）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

時序分析：
T=0ms:   editorScrollTop = 100  → 計算 target = 150  → previewScrollTop = 150
T=16ms:  editorScrollTop = 300  → 計算 target = 450  → previewScrollTop = 450
T=32ms:  editorScrollTop = 600  → 計算 target = 900  → previewScrollTop = 900
T=48ms:  editorScrollTop = 1000 → 計算 target = 1500 → previewScrollTop = 1500
...

結果：✅ 正常運作
- 每次都是根據編輯器「當前位置」計算，無狀態衝突
- 沒有反向監聽，不會有循環觸發
- 預覽區穩定跟隨編輯器移動

潛在考量：
- 快速滾動時會頻繁觸發計算
- 解決：使用 requestAnimationFrame 自然節流（瀏覽器每 16ms 最多執行一次）
```

#### 場景 (2)：滑鼠往上滾又突然往下滾動

```
用戶操作：先向上滾，突然改變方向向下滾
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

時序分析：
T=0ms:   editorScrollTop = 500 → target = 750  → previewScrollTop = 750   ↑ 向上
T=16ms:  editorScrollTop = 400 → target = 600  → previewScrollTop = 600   ↑ 向上
T=32ms:  editorScrollTop = 300 → target = 450  → previewScrollTop = 450   ↑ 向上
T=48ms:  editorScrollTop = 320 → target = 480  → previewScrollTop = 480   ↓ 改向下！
T=64ms:  editorScrollTop = 400 → target = 600  → previewScrollTop = 600   ↓ 向下
T=80ms:  editorScrollTop = 500 → target = 750  → previewScrollTop = 750   ↓ 向下

結果：✅ 正常運作，無回拉
- 方向改變時，預覽區立即跟隨新方向
- 因為是「狀態式」計算（只看當前位置），不存在方向衝突
- 不會有「程式把編輯器拉回去」的情況（因為沒有反向同步）

為什麼雙向同步會有問題？
- 雙向同步：用戶改變方向 → 編輯器設定預覽區 → 預覽區反向設定編輯器 → 衝突
- 單向同步：用戶改變方向 → 編輯器設定預覽區 → 結束（無反向）
```

#### 場景 (3)：滑鼠同一方向慢慢滾動

```
用戶操作：緩慢、穩定地向下滾動
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

時序分析（無閾值控制）：
T=0ms:    editorScrollTop = 100 → target = 150 → previewScrollTop = 150
T=100ms:  editorScrollTop = 105 → target = 158 → previewScrollTop = 158
T=200ms:  editorScrollTop = 110 → target = 165 → previewScrollTop = 165
T=300ms:  editorScrollTop = 115 → target = 173 → previewScrollTop = 173
...

結果：✅ 完美平滑同步

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

時序分析（有 20px 閾值控制）：
T=0ms:    editorScrollTop = 100 → target = 150 → diff = 0   → 同步！ previewScrollTop = 150
T=100ms:  editorScrollTop = 105 → target = 158 → diff = 8   → 不同步（< 20px）
T=200ms:  editorScrollTop = 110 → target = 165 → diff = 15  → 不同步（< 20px）
T=300ms:  editorScrollTop = 115 → target = 173 → diff = 23  → 同步！ previewScrollTop = 173
T=400ms:  editorScrollTop = 120 → target = 180 → diff = 7   → 不同步（< 20px）
...

結果：⚠️ 可能出現「階梯式」跟隨
- 預覽區不是每次都同步，而是累積到閾值才跳一次
- 視覺上可能感覺不夠平滑

解決方案：
1. 降低閾值到 5-10px
2. 或完全移除閾值（慢速滾動本身不會有效能問題）
3. 或根據滾動速度動態調整閾值
```

### 三種場景總結

| 場景 | 方案 E 表現 | 是否有回拉 | 備註 |
|------|------------|-----------|------|
| (1) 大幅度同方向 | ✅ 正常 | ❌ 無 | 使用 rAF 節流即可 |
| (2) 方向突然改變 | ✅ 正常 | ❌ 無 | 單向同步的核心優勢 |
| (3) 慢速同方向 | ✅ 正常 | ❌ 無 | 建議降低或移除閾值 |

### 優化建議

```javascript
// 動態閾值：根據滾動速度調整
let lastScrollTop = 0;
let lastScrollTime = 0;

function onEditorScroll() {
  const now = performance.now();
  const currentScrollTop = editorEl.scrollTop;
  
  // 計算滾動速度（px/ms）
  const timeDelta = now - lastScrollTime;
  const scrollDelta = Math.abs(currentScrollTop - lastScrollTop);
  const speed = timeDelta > 0 ? scrollDelta / timeDelta : 0;
  
  // 動態閾值：快速滾動用高閾值，慢速滾動用低閾值
  const dynamicThreshold = speed > 2 ? 20 : (speed > 0.5 ? 10 : 0);
  
  const targetPosition = calculatePreviewTarget(...);
  const diff = Math.abs(previewEl.scrollTop - targetPosition);
  
  if (diff > dynamicThreshold) {
    previewEl.scrollTop = targetPosition;
  }
  
  lastScrollTop = currentScrollTop;
  lastScrollTime = now;
}
```

### 結論

**方案 E（單向同步）能夠正確處理所有三種滾動場景**：

1. ✅ 不會產生回拉（沒有反向監聽 = 沒有循環觸發）
2. ✅ 方向改變時立即響應（狀態式計算，無歷史包袱）
3. ✅ 慢速滾動平滑（建議移除或降低閾值）

**推薦配置**：
```javascript
const SCROLL_SYNC_CONFIG = {
  enableReverseSync: false,     // 單向同步
  syncThresholdPx: 5,           // 低閾值確保平滑（原本 20 改為 5）
  useRAF: true,                 // 使用 requestAnimationFrame
};
```

---

## ✅ 實作檢查清單

- [ ] 移除舊版 V15 滾動同步代碼
- [ ] 實作 `parseEditorStructure()` 函數
- [ ] 實作 `parsePreviewStructure()` 函數
- [ ] 實作 `calculatePreviewTarget()` 函數
- [ ] 實作 `onEditorScroll()` 事件處理
- [ ] 加入 scrollSource 保護機制
- [ ] 加入閾值控制
- [ ] 加入結構緩存機制
- [ ] 測試：Summary 前滾動
- [ ] 測試：Summary 中滾動
- [ ] 測試：Summary 後滾動
- [ ] 測試：無 Summary 的文檔
- [ ] 測試：快速滾動
- [ ] 測試：確認無回拉現象
