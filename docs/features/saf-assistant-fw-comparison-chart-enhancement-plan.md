# SAF Assistant FW 版本比較圖表增強計畫

## 📋 文件資訊

| 項目 | 內容 |
|------|------|
| **文件名稱** | SAF Assistant FW 版本比較圖表視覺化增強計畫 |
| **建立日期** | 2025-12-15 |
| **作者** | AI Platform Team |
| **狀態** | ✅ 已完成（全部圖表功能） |
| **關聯文件** | `saf-assistant-fw-comparison-enhancement-plan.md` |
| **相關模組** | `library/saf_integration/smart_query/`<br>`frontend/src/components/chat/charts/` |

---

## 🎯 目標概述

在現有 FW 版本比較功能基礎上，增加圖表視覺化呈現，提升用戶對比較結果的理解效率。

### 📊 實作完成狀態

| 區塊 | 圖表類型 | 顯示條件 | 狀態 |
|------|---------|---------|------|
| **按測試類別比較** | 雷達圖 | 永遠顯示（2 版本比較） | ✅ 已完成 |
| **測試結果比較** | 分組長條圖 | ≥3 版本時顯示 | ✅ 已完成 |
| **整體指標比較** | 折線圖 | ≥3 版本時顯示 | ✅ 已完成 |

### 📊 目前呈現方式（純表格）

根據附件截圖，目前 FW 版本比較結果包含三個主要區塊：

| 區塊 | 目前呈現 | 資料特性 |
|------|---------|---------|
| **測試結果比較** | 表格（Pass/Fail/通過率） | 2 個版本對比 |
| **整體指標比較** | 表格（完成率/執行率/失敗率/樣本使用） | 2 個版本對比 |
| **按測試類別比較** | 表格（9 個測試類別的 Pass/Fail） | 多維度對比 |

---

## 📈 圖表增強規劃

### 一、按測試類別比較 → 新增雷達圖 ✅ **已完成**

#### 1.1 需求分析

| 項目 | 說明 |
|------|------|
| **目的** | 讓用戶一眼看出兩個版本在各測試類別的強弱分佈 |
| **資料來源** | 9 個測試類別（Functionality, MANDi, NVMe_Validation_Tool, Performance, Power Cycling, Protocol, Reliability, Security） |
| **顯示時機** | **永遠顯示**（固定 2 個版本比較） |
| **適用性** | ⭐⭐⭐⭐⭐ 非常適合 |

#### 1.2 為什麼雷達圖適合？

```
✅ 優點：
├── 多維度對比：9 個類別一目了然
├── 面積直觀：整體覆蓋程度一眼可見
├── 差異突顯：兩條線的重疊/分離區域清晰
└── 視覺記憶：形狀更容易記住

❌ 不適合的情況：
├── 類別數量 < 3（太少，雷達圖無意義）
└── 類別數量 > 12（太多，圖形過於複雜）

當前情況：9 個類別 → 非常適合
```

#### 1.3 雷達圖設計規格

```javascript
// 圖表類型：radar
{
  "type": "radar",
  "title": "測試類別分佈對比",
  "data": {
    "labels": [
      "Functionality", "MANDi", "NVMe_Validation_Tool",
      "Performance", "Power Cycling", "Protocol",
      "Reliability", "Security"
    ],
    "datasets": [
      {
        "name": "GM10YCCM_Opal",
        "data": [0, 8, 2, 12, 9, 1, 5, 3],  // Pass 數量
        "color": "#1890ff",
        "backgroundColor": "rgba(24, 144, 255, 0.2)"
      },
      {
        "name": "GM10YCBM_Opal",
        "data": [4, 3, 2, 12, 9, 1, 5, 3],
        "color": "#52c41a",
        "backgroundColor": "rgba(82, 196, 26, 0.2)"
      }
    ]
  },
  "options": {
    "showLegend": true,
    "showScale": true,
    "height": 400
  }
}
```

#### 1.4 視覺預覽

```
              Functionality
                   /\
                  /  \
                 /    \
       Security /      \ MANDi
               /   ⬡⬡   \
              /  ⬡    ⬡  \
    Reliability ─────────── NVMe_Validation
              \  ⬡    ⬡  /
               \   ⬡⬡   /
       Protocol \      / Power Cycling
                 \    /
                  \  /
                   \/
               Performance
               
    ──── GM10YCCM_Opal (藍色)
    ──── GM10YCBM_Opal (綠色)
```

---

### 二、測試結果比較 → 條件式顯示長條圖/折線圖

#### 2.1 需求分析

| 項目 | 說明 |
|------|------|
| **目的** | 展示 Pass/Fail 數量的版本對比 |
| **資料來源** | Pass、Fail、通過率 |
| **顯示條件** | **資料筆數 ≥ 3 時顯示** |
| **當前情況** | 2 個版本 → **不顯示圖表** |

#### 2.2 為什麼需要 ≥ 3 筆條件？

```
2 筆資料：
├── 長條圖：只有 2 個長條，視覺資訊少
├── 折線圖：只有 1 條線段，無法呈現趨勢
└── 建議：維持表格即可

3 筆以上資料：
├── 長條圖：可以看出變化差異
├── 折線圖：可以呈現趨勢（上升/下降/波動）
└── 建議：加入圖表提升可讀性
```

#### 2.3 圖表類型選擇

| 資料筆數 | 推薦圖表 | 原因 |
|---------|---------|------|
| 2 筆 | **不顯示圖表** | 表格已足夠 |
| 3-5 筆 | **分組長條圖** | 易於逐版本對比 |
| 6+ 筆 | **折線圖** | 呈現整體趨勢 |

#### 2.4 分組長條圖設計規格（3-5 筆）

```javascript
// 圖表類型：grouped-bar
{
  "type": "bar",
  "title": "FW 版本測試結果趨勢",
  "data": {
    "labels": ["FW_v1", "FW_v2", "FW_v3"],  // 版本名稱
    "datasets": [
      {
        "name": "Pass",
        "data": [38, 39, 40],
        "color": "#52c41a"  // 綠色
      },
      {
        "name": "Fail",
        "data": [2, 1, 0],
        "color": "#ff4d4f"  // 紅色
      }
    ]
  },
  "options": {
    "showLegend": true,
    "showGrid": true,
    "height": 300,
    "barMode": "grouped"  // 分組模式
  }
}
```

#### 2.5 折線圖設計規格（6+ 筆）

```javascript
// 圖表類型：line
{
  "type": "line",
  "title": "FW 版本測試結果趨勢",
  "data": {
    "labels": ["v1", "v2", "v3", "v4", "v5", "v6"],
    "datasets": [
      {
        "name": "Pass",
        "data": [35, 36, 38, 39, 40, 40],
        "color": "#52c41a"
      },
      {
        "name": "Fail",
        "data": [5, 4, 2, 1, 0, 0],
        "color": "#ff4d4f"
      },
      {
        "name": "通過率 (%)",
        "data": [87.5, 90.0, 95.0, 97.5, 100, 100],
        "color": "#1890ff",
        "yAxisID": "percentage"  // 使用第二 Y 軸
      }
    ]
  },
  "options": {
    "showLegend": true,
    "showGrid": true,
    "showDots": true,
    "height": 350
  }
}
```

---

### 三、整體指標比較 → 條件式顯示圖表

#### 3.1 需求分析

| 項目 | 說明 |
|------|------|
| **目的** | 展示完成率、執行率、失敗率等指標的變化 |
| **資料來源** | 完成率、執行率、失敗率、樣本使用 |
| **顯示條件** | **資料筆數 ≥ 3 時顯示** |
| **當前情況** | 2 個版本 → **不顯示圖表** |

#### 3.2 適合的圖表類型分析

| 圖表類型 | 優點 | 缺點 | 推薦度 |
|---------|------|------|--------|
| **多系列折線圖** | 可同時追蹤多個指標趨勢 | 指標單位不同需雙 Y 軸 | ⭐⭐⭐⭐ |
| **分組長條圖** | 版本間對比直觀 | 指標多時顯得擁擠 | ⭐⭐⭐ |
| **面積圖 (Area)** | 累積趨勢明顯 | 指標不適合累積 | ⭐⭐ |
| **雷達圖** | 多維度整體觀 | 更適合分類而非時序 | ⭐⭐ |

#### 3.3 推薦方案：多系列折線圖

**理由**：
1. 整體指標都是百分比（同單位），適合同一 Y 軸
2. 折線圖能清楚呈現版本演進趨勢
3. 可以看出各指標是同步上升還是此消彼長

#### 3.4 多系列折線圖設計規格

```javascript
// 圖表類型：line (多系列)
{
  "type": "line",
  "title": "FW 版本整體指標趨勢",
  "data": {
    "labels": ["FW_v1", "FW_v2", "FW_v3", "FW_v4"],
    "datasets": [
      {
        "name": "完成率",
        "data": [85, 91, 95, 100],
        "color": "#1890ff"  // 藍色
      },
      {
        "name": "執行率",
        "data": [90, 96, 98, 100],
        "color": "#52c41a"  // 綠色
      },
      {
        "name": "失敗率",
        "data": [5, 3, 1, 0],
        "color": "#ff4d4f"  // 紅色
      }
    ]
  },
  "options": {
    "showLegend": true,
    "showGrid": true,
    "showDots": true,
    "height": 350,
    "yAxis": {
      "min": 0,
      "max": 100,
      "suffix": "%"
    }
  }
}
```

#### 3.5 替代方案：分組長條圖

如果不想用折線圖，分組長條圖也是可接受的選擇：

```javascript
{
  "type": "bar",
  "title": "FW 版本整體指標對比",
  "data": {
    "labels": ["完成率", "執行率", "失敗率"],
    "datasets": [
      { "name": "FW_v1", "data": [85, 90, 5], "color": "#1890ff" },
      { "name": "FW_v2", "data": [91, 96, 3], "color": "#52c41a" },
      { "name": "FW_v3", "data": [95, 98, 1], "color": "#faad14" },
      { "name": "FW_v4", "data": [100, 100, 0], "color": "#722ed1" }
    ]
  },
  "options": {
    "barMode": "grouped",
    "showLegend": true,
    "height": 300
  }
}
```

---

## 📊 圖表顯示邏輯總結

| 區塊 | 資料筆數 | 圖表類型 | 顯示位置 |
|------|---------|---------|---------|
| **按測試類別比較** | 任意（永遠顯示） | 🕸️ 雷達圖 | 表格上方或下方 |
| **測試結果比較** | < 3 | ❌ 不顯示圖表 | - |
| **測試結果比較** | 3-5 | 📊 分組長條圖 | 表格下方 |
| **測試結果比較** | ≥ 6 | 📈 折線圖 | 表格下方 |
| **整體指標比較** | < 3 | ❌ 不顯示圖表 | - |
| **整體指標比較** | ≥ 3 | 📈 多系列折線圖 | 表格下方 |

---

## 🔧 技術實作方案

### Phase 6.1：新增雷達圖組件（前端）

#### 6.1.1 需修改/新增的檔案

```
frontend/src/components/chat/charts/
├── RadarChart.jsx           # 🆕 新增：雷達圖組件
├── ChartRenderer.jsx        # 📝 修改：支援 radar 類型
├── ChartStyles.css          # 📝 修改：雷達圖樣式
└── index.js                 # 📝 修改：導出 RadarChart
```

#### 6.1.2 RadarChart.jsx 組件設計

```jsx
/**
 * RadarChart - 雷達圖組件
 * 
 * 用於多維度數據對比（如測試類別分佈）
 * 基於 Recharts RadarChart
 */

import React from 'react';
import {
  Radar, RadarChart as RechartsRadarChart, 
  PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Legend, ResponsiveContainer, Tooltip
} from 'recharts';

const RadarChart = ({ data, options = {} }) => {
  const { 
    labels, 
    datasets 
  } = data;
  
  const { 
    showLegend = true, 
    height = 400,
    showScale = true 
  } = options;

  // 轉換資料格式
  const chartData = labels.map((label, index) => {
    const point = { category: label };
    datasets.forEach(ds => {
      point[ds.name] = ds.data[index];
    });
    return point;
  });

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsRadarChart data={chartData}>
        <PolarGrid />
        <PolarAngleAxis dataKey="category" />
        {showScale && <PolarRadiusAxis angle={30} domain={[0, 'auto']} />}
        
        {datasets.map((ds, index) => (
          <Radar
            key={ds.name}
            name={ds.name}
            dataKey={ds.name}
            stroke={ds.color}
            fill={ds.backgroundColor || ds.color}
            fillOpacity={0.3}
          />
        ))}
        
        <Tooltip />
        {showLegend && <Legend />}
      </RechartsRadarChart>
    </ResponsiveContainer>
  );
};

export default RadarChart;
```

#### 6.1.3 ChartRenderer.jsx 修改

```jsx
// 新增 import
import RadarChart from './RadarChart';

// 修改 renderChart 函數
const renderChart = (config) => {
  const { type, data, options = {} } = config;
  
  switch (type) {
    case 'line':
      return <TrendLineChart data={data} options={options} />;
    case 'bar':
      return <ComparisonBarChart data={data} options={options} />;
    case 'pie':
      return <DistributionPieChart data={data} options={options} />;
    case 'radar':  // 🆕 新增
      return <RadarChart data={data} options={options} />;
    default:
      return <Empty description="不支援的圖表類型" />;
  }
};

// 修改 validateConfig
const validTypes = ['line', 'bar', 'pie', 'radar'];  // 加入 radar
```

---

### Phase 6.2：後端 ChartFormatter 擴展

#### 6.2.1 需修改的檔案

```
library/common/chart_formatter.py  # 📝 修改：新增雷達圖方法
```

#### 6.2.2 新增 radar_chart 方法

```python
@classmethod
def radar_chart(
    cls,
    title: str,
    labels: List[str],
    datasets: List[Dict[str, Any]],
    description: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> str:
    """
    生成雷達圖標記
    
    Args:
        title: 圖表標題
        labels: 維度標籤列表（如測試類別名稱）
        datasets: 資料集列表，每個資料集包含：
            - name: 資料系列名稱（如版本名）
            - data: 數據列表（與 labels 對應）
            - color: 線條顏色（可選）
            - backgroundColor: 填充顏色（可選）
        description: 圖表描述（可選）
        options: 額外選項（可選）
        
    Returns:
        str: :::chart 格式的 Markdown 標記
        
    Example:
        ChartFormatter.radar_chart(
            title="測試類別分佈對比",
            labels=["Functionality", "MANDi", "Performance", "Security"],
            datasets=[
                {"name": "FW_v1", "data": [4, 8, 12, 3]},
                {"name": "FW_v2", "data": [5, 6, 12, 4]}
            ]
        )
    """
    # 自動分配顏色和背景色
    for i, ds in enumerate(datasets):
        if 'color' not in ds:
            ds['color'] = cls.SERIES_COLORS[i % len(cls.SERIES_COLORS)]
        if 'backgroundColor' not in ds:
            # 將顏色轉為半透明背景
            color = ds['color']
            ds['backgroundColor'] = f"{color}33"  # 20% 透明度
    
    config = {
        'type': 'radar',
        'title': title,
        'data': {
            'labels': labels,
            'datasets': datasets
        }
    }
    
    if description:
        config['description'] = description
        
    if options:
        config['options'] = options
    else:
        config['options'] = {
            'showLegend': True,
            'showScale': True,
            'height': 400
        }
        
    return cls._format_chart_marker(config)
```

#### 6.2.3 新增便利方法

```python
@classmethod
def fw_category_comparison_radar(
    cls,
    title: str,
    categories: List[str],
    fw_versions: List[Dict[str, Any]]
) -> str:
    """
    生成 FW 版本測試類別雷達圖
    
    專為 SAF FW 比較設計的便利方法
    
    Args:
        title: 圖表標題
        categories: 測試類別列表
        fw_versions: FW 版本資料列表，每個版本包含：
            - name: 版本名稱
            - pass_counts: 各類別 Pass 數量列表
            
    Returns:
        str: :::chart 格式的 Markdown 標記
    """
    datasets = []
    for i, fw in enumerate(fw_versions):
        datasets.append({
            'name': fw['name'],
            'data': fw['pass_counts'],
            'color': cls.SERIES_COLORS[i % len(cls.SERIES_COLORS)]
        })
    
    return cls.radar_chart(
        title=title,
        labels=categories,
        datasets=datasets,
        description=f"比較 {len(fw_versions)} 個 FW 版本在 {len(categories)} 個測試類別的表現"
    )
```

---

### Phase 6.3：整合到 FW 比較 Handler

#### 6.3.1 需修改的檔案

```
library/saf_integration/smart_query/query_handlers/
└── compare_fw_versions_handler.py  # 📝 修改：加入圖表輸出
```

#### 6.3.2 修改 _format_comparison_response 方法

```python
def _format_comparison_response(self, data: Dict) -> str:
    """格式化比較回應，包含圖表"""
    
    response_parts = []
    
    # 1. 標題和基本資訊
    response_parts.append(self._format_header(data))
    
    # 2. 測試結果比較（表格）
    response_parts.append(self._format_test_results_table(data))
    
    # 3. 測試結果圖表（條件式顯示）
    version_count = len(data.get('versions', []))
    if version_count >= 3:
        response_parts.append(self._format_test_results_chart(data, version_count))
    
    # 4. 整體指標比較（表格）
    response_parts.append(self._format_overall_metrics_table(data))
    
    # 5. 整體指標圖表（條件式顯示）
    if version_count >= 3:
        response_parts.append(self._format_overall_metrics_chart(data))
    
    # 6. 按測試類別比較（表格）
    response_parts.append(self._format_category_comparison_table(data))
    
    # 7. 測試類別雷達圖（永遠顯示）
    response_parts.append(self._format_category_radar_chart(data))
    
    return '\n\n'.join(response_parts)


def _format_category_radar_chart(self, data: Dict) -> str:
    """生成測試類別雷達圖"""
    from library.common.chart_formatter import ChartFormatter
    
    categories = list(data['category_comparison'].keys())
    fw_versions = []
    
    for version_name, version_data in data['versions'].items():
        pass_counts = [
            data['category_comparison'][cat].get(version_name, {}).get('pass', 0)
            for cat in categories
        ]
        fw_versions.append({
            'name': version_name,
            'pass_counts': pass_counts
        })
    
    return ChartFormatter.fw_category_comparison_radar(
        title="📊 測試類別分佈對比",
        categories=categories,
        fw_versions=fw_versions
    )


def _format_test_results_chart(self, data: Dict, version_count: int) -> str:
    """生成測試結果圖表"""
    from library.common.chart_formatter import ChartFormatter
    
    versions = list(data['versions'].keys())
    pass_data = [data['versions'][v].get('pass', 0) for v in versions]
    fail_data = [data['versions'][v].get('fail', 0) for v in versions]
    
    if version_count >= 6:
        # 使用折線圖
        return ChartFormatter.line_chart(
            title="📈 測試結果趨勢",
            labels=versions,
            datasets=[
                {"name": "Pass", "data": pass_data, "color": "#52c41a"},
                {"name": "Fail", "data": fail_data, "color": "#ff4d4f"}
            ]
        )
    else:
        # 使用長條圖
        return ChartFormatter.bar_chart(
            title="📊 測試結果對比",
            labels=versions,
            datasets=[
                {"name": "Pass", "data": pass_data, "color": "#52c41a"},
                {"name": "Fail", "data": fail_data, "color": "#ff4d4f"}
            ]
        )


def _format_overall_metrics_chart(self, data: Dict) -> str:
    """生成整體指標圖表"""
    from library.common.chart_formatter import ChartFormatter
    
    versions = list(data['versions'].keys())
    
    completion_rates = [
        data['versions'][v].get('completion_rate', 0) for v in versions
    ]
    execution_rates = [
        data['versions'][v].get('execution_rate', 0) for v in versions
    ]
    failure_rates = [
        data['versions'][v].get('failure_rate', 0) for v in versions
    ]
    
    return ChartFormatter.line_chart(
        title="📈 整體指標趨勢",
        labels=versions,
        datasets=[
            {"name": "完成率", "data": completion_rates, "color": "#1890ff"},
            {"name": "執行率", "data": execution_rates, "color": "#52c41a"},
            {"name": "失敗率", "data": failure_rates, "color": "#ff4d4f"}
        ],
        options={
            "showLegend": True,
            "showGrid": True,
            "showDots": True,
            "height": 350
        }
    )
```

---

## 📅 實施時程

### Phase 6：圖表視覺化增強

| 子項目 | 任務 | 工時 | 優先級 |
|--------|------|------|--------|
| 6.1.1 | 建立 RadarChart.jsx 組件 | 3h | ⭐⭐⭐ |
| 6.1.2 | 修改 ChartRenderer 支援 radar | 1h | ⭐⭐⭐ |
| 6.1.3 | 雷達圖樣式調整 | 1h | ⭐⭐⭐ |
| 6.2.1 | ChartFormatter 新增 radar_chart | 2h | ⭐⭐⭐ |
| 6.2.2 | 新增便利方法 fw_category_comparison_radar | 1h | ⭐⭐⭐ |
| 6.3.1 | 修改 compare_fw_versions_handler | 3h | ⭐⭐⭐ |
| 6.3.2 | 整合測試與調整 | 2h | ⭐⭐⭐ |
| **小計** | | **13h** | |

### 時程建議

```
Week 1：前端雷達圖組件開發（5h）
├── Day 1-2：RadarChart.jsx 開發
└── Day 3：ChartRenderer 整合與測試

Week 2：後端整合（5h）
├── Day 1：ChartFormatter 擴展
└── Day 2-3：Handler 整合

Week 3：測試與優化（3h）
├── Day 1：端對端測試
└── Day 2：UI 調整與優化
```

---

## ✅ 驗收標準

### 雷達圖驗收
- [ ] 兩個 FW 版本比較時，自動顯示測試類別雷達圖
- [ ] 雷達圖正確顯示 9 個測試類別
- [ ] 兩個版本用不同顏色區分，圖例清晰
- [ ] 滑鼠 hover 顯示具體數值
- [ ] 響應式設計，手機端也能正常顯示

### 條件式圖表驗收
- [ ] 2 個版本比較時，測試結果和整體指標**不顯示圖表**
- [ ] 3-5 個版本比較時，測試結果顯示**分組長條圖**
- [ ] 6+ 個版本比較時，測試結果顯示**折線圖**
- [ ] 3+ 個版本比較時，整體指標顯示**多系列折線圖**

### 整體驗收
- [ ] 圖表與表格並存，互相補充
- [ ] 圖表載入時有 loading 狀態
- [ ] 圖表渲染失敗時有 fallback 顯示
- [ ] 效能：圖表渲染 < 500ms

---

## 📚 相關資源

### 技術參考
- [Recharts RadarChart](https://recharts.org/en-US/api/RadarChart)
- [Ant Design Charts](https://charts.ant.design/)

### 相關文件
- [SAF FW 比較增強計畫](./saf-assistant-fw-comparison-enhancement-plan.md)
- [ChartFormatter 使用指南](../../library/common/chart_formatter.py)
- [前端圖表組件](../../frontend/src/components/chat/charts/)

---

## 📝 更新記錄

| 日期 | 版本 | 更新內容 | 作者 |
|------|------|----------|------|
| 2025-12-15 | v1.0 | 初版建立 | AI Platform Team |
| 2025-12-15 | v1.1 | 完成 Phase 6.1-6.3 雷達圖實作 | AI Platform Team |

---

## ✅ 已完成項目

### Phase 6.1：前端雷達圖組件
- [x] 建立 `RadarChart.jsx` 組件
- [x] 修改 `ChartRenderer.jsx` 支援 radar 類型
- [x] 更新 `charts/index.js` 導出

### Phase 6.2：後端 ChartFormatter
- [x] 新增 `radar_chart()` 方法
- [x] 新增 `fw_category_comparison_radar()` 便利方法
- [x] 新增便利函數導出

### Phase 6.3：Handler 整合
- [x] 修改 `compare_fw_versions_handler.py` 
- [x] 在測試類別比較表格後自動生成雷達圖

---

**📌 下一步行動**：確認計畫內容後，開始執行 Phase 6.1 前端雷達圖組件開發。
