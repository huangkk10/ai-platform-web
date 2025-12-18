"""
ChartFormatter - 圖表格式化工具

用於在 AI Assistant 回應中生成圖表 Markdown 標記
前端會解析這些標記並渲染對應的圖表

支援圖表類型：
- line: 折線圖（趨勢分析）
- bar: 柱狀圖（版本比較）
- pie: 圓餅圖（佔比分佈）

使用方式：
    from library.common.chart_formatter import ChartFormatter
    
    # 生成折線圖
    chart_md = ChartFormatter.line_chart(
        title="FW 版本趨勢",
        labels=["FW1", "FW2", "FW3"],
        datasets=[
            {"name": "Read IOPS", "data": [100, 120, 115], "color": "#1890ff"},
            {"name": "Write IOPS", "data": [90, 95, 100], "color": "#52c41a"}
        ]
    )

@author AI Platform Team
@version 1.0.0
"""

import json
from typing import List, Dict, Any, Optional


class ChartFormatter:
    """
    圖表格式化工具類
    
    提供靜態方法生成 :::chart 標記
    """
    
    # 預設配色方案（與前端 CHART_COLORS 對應）
    COLORS = {
        'primary': '#1890ff',    # Ant Design 主色
        'success': '#52c41a',    # 綠色 - 成功
        'warning': '#faad14',    # 橙色 - 警告
        'error': '#ff4d4f',      # 紅色 - 錯誤
        'purple': '#722ed1',     # 紫色
        'cyan': '#13c2c2',       # 青色
        'magenta': '#eb2f96',    # 洋紅
        'lime': '#a0d911',       # 青檸
        'gold': '#faad14',       # 金色
        'blue': '#1890ff',       # 藍色
    }
    
    # 漸變系列顏色
    SERIES_COLORS = [
        '#1890ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1',
        '#13c2c2', '#eb2f96', '#a0d911', '#2f54eb', '#fa8c16'
    ]
    
    @classmethod
    def _format_chart_marker(cls, config: Dict[str, Any]) -> str:
        """
        格式化圖表配置為 Markdown 標記
        
        Args:
            config: 圖表配置字典
            
        Returns:
            str: :::chart 格式的 Markdown 標記
        """
        json_str = json.dumps(config, ensure_ascii=False, indent=2)
        return f":::chart\n{json_str}\n:::"
    
    @classmethod
    def line_chart(
        cls,
        title: str,
        labels: List[str],
        datasets: List[Dict[str, Any]],
        description: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成折線圖標記
        
        Args:
            title: 圖表標題
            labels: X 軸標籤列表（如 FW 版本名稱）
            datasets: 資料集列表，每個資料集包含：
                - name: 資料系列名稱
                - data: 數據列表
                - color: 顏色（可選）
            description: 圖表描述（可選）
            options: 額外選項（可選）
            
        Returns:
            str: :::chart 格式的 Markdown 標記
            
        Example:
            ChartFormatter.line_chart(
                title="FW 版本 Read IOPS 趨勢",
                labels=["FW_001", "FW_002", "FW_003"],
                datasets=[
                    {"name": "Read IOPS", "data": [15000, 15500, 15200]}
                ]
            )
        """
        # 自動分配顏色
        for i, ds in enumerate(datasets):
            if 'color' not in ds:
                ds['color'] = cls.SERIES_COLORS[i % len(cls.SERIES_COLORS)]
        
        config = {
            'type': 'line',
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
            
        return cls._format_chart_marker(config)
    
    @classmethod
    def bar_chart(
        cls,
        title: str,
        labels: List[str],
        datasets: List[Dict[str, Any]],
        description: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成柱狀圖標記
        
        Args:
            title: 圖表標題
            labels: X 軸標籤列表
            datasets: 資料集列表，每個資料集包含：
                - name: 資料系列名稱
                - data: 數據列表
                - color: 顏色（可選）
            description: 圖表描述（可選）
            options: 額外選項（可選）
            
        Returns:
            str: :::chart 格式的 Markdown 標記
        """
        # 自動分配顏色
        for i, ds in enumerate(datasets):
            if 'color' not in ds:
                ds['color'] = cls.SERIES_COLORS[i % len(cls.SERIES_COLORS)]
        
        config = {
            'type': 'bar',
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
            
        return cls._format_chart_marker(config)
    
    @classmethod
    def pie_chart(
        cls,
        title: str,
        items: List[Dict[str, Any]],
        description: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成圓餅圖標記
        
        Args:
            title: 圖表標題
            items: 項目列表，每個項目包含：
                - name: 項目名稱
                - value: 數值
                - color: 顏色（可選）
            description: 圖表描述（可選）
            options: 額外選項（可選）
            
        Returns:
            str: :::chart 格式的 Markdown 標記
            
        Example:
            ChartFormatter.pie_chart(
                title="測試類型分佈",
                items=[
                    {"name": "Read", "value": 60},
                    {"name": "Write", "value": 40}
                ]
            )
        """
        # 自動分配顏色
        for i, item in enumerate(items):
            if 'color' not in item:
                item['color'] = cls.SERIES_COLORS[i % len(cls.SERIES_COLORS)]
        
        config = {
            'type': 'pie',
            'title': title,
            'data': {
                'items': items
            }
        }
        
        if description:
            config['description'] = description
            
        if options:
            config['options'] = options
            
        return cls._format_chart_marker(config)
    
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
                # 將顏色轉為半透明背景（20% 透明度）
                color = ds['color']
                ds['backgroundColor'] = f"{color}33"
        
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
            
        Example:
            ChartFormatter.fw_category_comparison_radar(
                title="測試類別分佈對比",
                categories=["Functionality", "MANDi", "Performance"],
                fw_versions=[
                    {"name": "FW_v1", "pass_counts": [4, 8, 12]},
                    {"name": "FW_v2", "pass_counts": [5, 6, 12]}
                ]
            )
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
    
    @classmethod
    def fw_trend_chart(
        cls,
        title: str,
        fw_versions: List[str],
        metrics: Dict[str, List[float]],
        metric_colors: Optional[Dict[str, str]] = None
    ) -> str:
        """
        生成 FW 趨勢分析專用圖表
        
        專為 SAF API 查詢結果設計的便利方法
        
        Args:
            title: 圖表標題（如 "Springsteen AA 最近 3 個 FW 版本趨勢"）
            fw_versions: FW 版本列表（按時間順序）
            metrics: 指標字典，key 為指標名稱，value 為對應數值列表
                例如: {"Read IOPS": [15000, 15500, 15200], "Write IOPS": [10000, 10500, 10200]}
            metric_colors: 指標顏色映射（可選）
                例如: {"Read IOPS": "#1890ff", "Write IOPS": "#52c41a"}
        
        Returns:
            str: :::chart 格式的 Markdown 標記
            
        Example:
            ChartFormatter.fw_trend_chart(
                title="Springsteen AA 最近 3 個 FW 版本趨勢",
                fw_versions=["FW_001", "FW_002", "FW_003"],
                metrics={
                    "Seq Read IOPS": [15000, 15500, 15200],
                    "Seq Write IOPS": [10000, 10500, 10200],
                    "Rand Read IOPS": [5000, 5200, 5100],
                    "Rand Write IOPS": [4000, 4100, 4050]
                }
            )
        """
        datasets = []
        default_colors = {
            'Seq Read': '#1890ff',      # 藍色
            'Seq Write': '#52c41a',     # 綠色
            'Rand Read': '#722ed1',     # 紫色
            'Rand Write': '#faad14',    # 橙色
            'Read IOPS': '#1890ff',
            'Write IOPS': '#52c41a',
            'Read Throughput': '#13c2c2',  # 青色
            'Write Throughput': '#eb2f96'  # 洋紅
        }
        
        for i, (metric_name, values) in enumerate(metrics.items()):
            color = None
            
            # 嘗試從自訂顏色中取得
            if metric_colors and metric_name in metric_colors:
                color = metric_colors[metric_name]
            
            # 嘗試從預設顏色中取得
            if not color:
                for key, default_color in default_colors.items():
                    if key in metric_name:
                        color = default_color
                        break
            
            # 使用系列顏色
            if not color:
                color = cls.SERIES_COLORS[i % len(cls.SERIES_COLORS)]
            
            datasets.append({
                'name': metric_name,
                'data': values,
                'color': color
            })
        
        return cls.line_chart(
            title=title,
            labels=fw_versions,
            datasets=datasets,
            description=f"顯示 {len(fw_versions)} 個 FW 版本的 {len(metrics)} 項指標變化趨勢",
            options={
                'showGrid': True,
                'showLegend': True,
                'showDots': True,
                'height': 350
            }
        )
    
    @classmethod
    def fw_comparison_bar_chart(
        cls,
        title: str,
        fw_versions: List[str],
        metrics: Dict[str, List[float]]
    ) -> str:
        """
        生成 FW 版本比較柱狀圖
        
        Args:
            title: 圖表標題
            fw_versions: FW 版本列表
            metrics: 指標字典
            
        Returns:
            str: :::chart 格式的 Markdown 標記
        """
        datasets = []
        for i, (metric_name, values) in enumerate(metrics.items()):
            datasets.append({
                'name': metric_name,
                'data': values,
                'color': cls.SERIES_COLORS[i % len(cls.SERIES_COLORS)]
            })
        
        return cls.bar_chart(
            title=title,
            labels=fw_versions,
            datasets=datasets,
            description=f"{len(fw_versions)} 個 FW 版本性能對比",
            options={
                'showGrid': True,
                'showLegend': True,
                'height': 350
            }
        )

    @classmethod
    def fw_test_results_bar(
        cls,
        title: str,
        fw_versions: List[str],
        pass_counts: List[int],
        fail_counts: List[int]
    ) -> str:
        """
        生成 FW 版本測試結果分組長條圖
        
        專為 SAF FW 比較設計，顯示各版本的 Pass/Fail 數量
        條件：僅在 fw_versions >= 3 時顯示
        
        Args:
            title: 圖表標題
            fw_versions: FW 版本名稱列表（按時間順序）
            pass_counts: 各版本 Pass 數量列表
            fail_counts: 各版本 Fail 數量列表
            
        Returns:
            str: :::chart 格式的 Markdown 標記
            
        Example:
            ChartFormatter.fw_test_results_bar(
                title="FW 版本測試結果趨勢",
                fw_versions=["FW_v1", "FW_v2", "FW_v3"],
                pass_counts=[38, 39, 40],
                fail_counts=[2, 1, 0]
            )
        """
        datasets = [
            {
                'name': 'Pass',
                'data': pass_counts,
                'color': cls.COLORS['success']  # 綠色
            },
            {
                'name': 'Fail',
                'data': fail_counts,
                'color': cls.COLORS['error']  # 紅色
            }
        ]
        
        return cls.bar_chart(
            title=title,
            labels=fw_versions,
            datasets=datasets,
            description=f"比較 {len(fw_versions)} 個 FW 版本的測試結果分佈",
            options={
                'showGrid': True,
                'showLegend': True,
                'height': 300,
                'barMode': 'grouped'  # 分組模式
            }
        )

    @classmethod
    def version_comparison_chart(
        cls,
        title: str,
        fw_versions: List[str],
        pass_counts: List[int],
        fail_counts: List[int],
        pass_rates: List[float],
        description: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成 FW 版本比較組合圖表（堆疊柱狀圖 + 折線圖）
        
        專為 SAF Assistant 多 FW 版本比較設計：
        - 堆疊柱狀圖：顯示各版本的 Pass/Fail 數量
        - 折線圖：顯示通過率趨勢
        
        這是一個組合圖表，前端使用 VersionComparisonChart 組件渲染
        
        Args:
            title: 圖表標題
            fw_versions: FW 版本名稱列表（按時間順序）
            pass_counts: 各版本 Pass 數量列表
            fail_counts: 各版本 Fail 數量列表
            pass_rates: 各版本通過率列表（百分比數值，如 89.4）
            description: 圖表描述（可選）
            options: 額外選項（可選）
            
        Returns:
            str: :::chart 格式的 Markdown 標記，type 為 'version-comparison'
            
        Example:
            ChartFormatter.version_comparison_chart(
                title="Springsteen FW 版本測試結果對比",
                fw_versions=["G210X74A", "G210Y1NA", "G210Y33A", "G210Y37B"],
                pass_counts=[17, 59, 68, 50],
                fail_counts=[14, 5, 4, 15],
                pass_rates=[44.7, 89.4, 93.2, 67.6]
            )
        """
        config = {
            'type': 'version-comparison',
            'title': title,
            'data': {
                'labels': fw_versions,
                'pass': pass_counts,
                'fail': fail_counts,
                'passRate': pass_rates
            }
        }
        
        if description:
            config['description'] = description
        else:
            config['description'] = f"比較 {len(fw_versions)} 個 FW 版本的測試結果與通過率趨勢"
        
        # 預設選項
        default_options = {
            'height': 350,
            'showGrid': True,
            'showLegend': True,
            'animate': True,
            'showLineLabels': True
        }
        
        if options:
            default_options.update(options)
        
        config['options'] = default_options
        
        return cls._format_chart_marker(config)

    @classmethod
    def fw_overall_metrics_line(
        cls,
        title: str,
        fw_versions: List[str],
        metrics_data: Dict[str, List[float]]
    ) -> str:
        """
        生成 FW 版本整體指標多系列折線圖
        
        專為 SAF FW 比較設計，顯示完成率、執行率、失敗率等指標趨勢
        條件：僅在 fw_versions >= 3 時顯示
        
        Args:
            title: 圖表標題
            fw_versions: FW 版本名稱列表（按時間順序）
            metrics_data: 指標數據字典，key 為指標名稱，value 為數值列表
                支援的指標：
                - "完成率": 完成率百分比列表
                - "執行率": 執行率百分比列表
                - "失敗率": 失敗率百分比列表
                
        Returns:
            str: :::chart 格式的 Markdown 標記
            
        Example:
            ChartFormatter.fw_overall_metrics_line(
                title="FW 版本整體指標趨勢",
                fw_versions=["FW_v1", "FW_v2", "FW_v3", "FW_v4"],
                metrics_data={
                    "完成率": [85.0, 91.0, 95.0, 100.0],
                    "執行率": [90.0, 96.0, 98.0, 100.0],
                    "失敗率": [5.0, 3.0, 1.0, 0.0]
                }
            )
        """
        # 預設指標顏色
        metric_colors = {
            '完成率': cls.COLORS['primary'],  # 藍色
            '執行率': cls.COLORS['success'],   # 綠色
            '失敗率': cls.COLORS['error'],     # 紅色
            '通過率': cls.COLORS['cyan'],      # 青色
            'completion_rate': cls.COLORS['primary'],
            'execution_rate': cls.COLORS['success'],
            'fail_rate': cls.COLORS['error'],
            'pass_rate': cls.COLORS['cyan']
        }
        
        datasets = []
        for i, (metric_name, values) in enumerate(metrics_data.items()):
            color = metric_colors.get(metric_name, cls.SERIES_COLORS[i % len(cls.SERIES_COLORS)])
            datasets.append({
                'name': metric_name,
                'data': values,
                'color': color
            })
        
        return cls.line_chart(
            title=title,
            labels=fw_versions,
            datasets=datasets,
            description=f"顯示 {len(fw_versions)} 個 FW 版本的整體指標變化趨勢",
            options={
                'showGrid': True,
                'showLegend': True,
                'showDots': True,
                'height': 350,
                'yAxis': {
                    'min': 0,
                    'max': 100,
                    'suffix': '%'
                }
            }
        )

    @classmethod
    def heatmap(
        cls,
        title: str,
        x_labels: List[str],
        y_labels: List[str],
        data: List[List[float]],
        description: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成熱力圖標記
        
        Args:
            title: 圖表標題
            x_labels: X 軸標籤列表（如 FW 版本名稱）
            y_labels: Y 軸標籤列表（如測試類別名稱）
            data: 二維數據陣列 [y][x]，數值範圍影響顏色深淺
            description: 圖表描述（可選）
            options: 額外選項（可選）
                - colorScale: 顏色方案 ('green-red', 'blue', 'red', 'green')
                - showValues: 是否在格子中顯示數值
                - valueType: 數值類型 ('number', 'percent', 'status')
            
        Returns:
            str: :::chart 格式的 Markdown 標記
            
        Example:
            ChartFormatter.heatmap(
                title="測試類別通過率熱力圖",
                x_labels=["FW_v1", "FW_v2", "FW_v3"],
                y_labels=["Functionality", "MANDi", "Performance"],
                data=[
                    [100, 100, 95],   # Functionality 在各版本的通過率
                    [100, 100, 100],  # MANDi 在各版本的通過率
                    [80, 85, 90]      # Performance 在各版本的通過率
                ]
            )
        """
        config = {
            'type': 'heatmap',
            'title': title,
            'data': {
                'xLabels': x_labels,
                'yLabels': y_labels,
                'values': data
            }
        }
        
        if description:
            config['description'] = description
            
        if options:
            config['options'] = options
        else:
            config['options'] = {
                'colorScale': 'green-red',  # 綠色=好，紅色=差
                'showValues': True,
                'valueType': 'number',
                'height': max(300, len(y_labels) * 40 + 100)  # 動態高度
            }
            
        return cls._format_chart_marker(config)
    
    @classmethod
    def category_pass_rate_heatmap(
        cls,
        title: str,
        categories: List[str],
        fw_versions: List[str],
        pass_rates: List[List[float]],
        description: Optional[str] = None
    ) -> str:
        """
        生成測試類別通過率熱力圖
        
        專為 SAF FW 多版本比較設計的便利方法
        
        Args:
            title: 圖表標題
            categories: 測試類別列表（Y 軸）
            fw_versions: FW 版本列表（X 軸）
            pass_rates: 二維通過率數據 [category_index][version_index]
                        數值範圍 0-100（百分比）
            description: 圖表描述（可選）
                
        Returns:
            str: :::chart 格式的 Markdown 標記
            
        Example:
            ChartFormatter.category_pass_rate_heatmap(
                title="測試類別通過率分佈",
                categories=["Functionality", "MANDi", "Performance"],
                fw_versions=["GM10YCCM", "GM10YCBM", "PH10YC3H"],
                pass_rates=[
                    [100.0, 100.0, 95.0],   # Functionality
                    [100.0, 100.0, 100.0],  # MANDi
                    [80.0, 85.0, 90.0]      # Performance
                ]
            )
        """
        return cls.heatmap(
            title=title,
            x_labels=fw_versions,
            y_labels=categories,
            data=pass_rates,
            description=description or f"顯示 {len(categories)} 個測試類別在 {len(fw_versions)} 個 FW 版本的通過率分佈",
            options={
                'colorScale': 'green-red',  # 綠色=高通過率，紅色=低通過率
                'showValues': True,
                'valueType': 'percent',
                'height': max(350, len(categories) * 35 + 120)
            }
        )
    
    @classmethod
    def category_fail_heatmap(
        cls,
        title: str,
        categories: List[str],
        fw_versions: List[str],
        fail_counts: List[List[int]],
        description: Optional[str] = None
    ) -> str:
        """
        生成測試類別 Fail 數量熱力圖
        
        專為 SAF FW 多版本比較設計的便利方法
        顏色邏輯：0 = 綠色（無 Fail），數值越大越紅
        
        Args:
            title: 圖表標題
            categories: 測試類別列表（Y 軸）
            fw_versions: FW 版本列表（X 軸）
            fail_counts: 二維 Fail 數量數據 [category_index][version_index]
            description: 圖表描述（可選）
                
        Returns:
            str: :::chart 格式的 Markdown 標記
            
        Example:
            ChartFormatter.category_fail_heatmap(
                title="測試類別 Fail 分佈",
                categories=["Functionality", "MANDi", "NVMe_Validation"],
                fw_versions=["GM10YCCM", "GM10YCBM", "PH10YC3H"],
                fail_counts=[
                    [0, 0, 1],  # Functionality
                    [0, 0, 0],  # MANDi
                    [0, 0, 1]   # NVMe_Validation
                ]
            )
        """
        return cls.heatmap(
            title=title,
            x_labels=fw_versions,
            y_labels=categories,
            data=fail_counts,
            description=description or f"顯示 {len(categories)} 個測試類別在 {len(fw_versions)} 個 FW 版本的 Fail 分佈",
            options={
                'colorScale': 'red',  # 0=綠色，>0 越大越紅
                'showValues': True,
                'valueType': 'number',
                'height': max(350, len(categories) * 35 + 120)
            }
        )


# 便利函數
def format_trend_chart(title: str, fw_versions: List[str], metrics: Dict[str, List[float]]) -> str:
    """便利函數：生成 FW 趨勢圖"""
    return ChartFormatter.fw_trend_chart(title, fw_versions, metrics)


def format_comparison_chart(title: str, fw_versions: List[str], metrics: Dict[str, List[float]]) -> str:
    """便利函數：生成比較柱狀圖"""
    return ChartFormatter.fw_comparison_bar_chart(title, fw_versions, metrics)


def format_radar_chart(title: str, labels: List[str], datasets: List[Dict[str, Any]]) -> str:
    """便利函數：生成雷達圖"""
    return ChartFormatter.radar_chart(title, labels, datasets)


def format_category_comparison_radar(
    title: str, 
    categories: List[str], 
    fw_versions: List[Dict[str, Any]]
) -> str:
    """便利函數：生成 FW 版本測試類別雷達圖"""
    return ChartFormatter.fw_category_comparison_radar(title, categories, fw_versions)


def format_test_results_bar(
    title: str,
    fw_versions: List[str],
    pass_counts: List[int],
    fail_counts: List[int]
) -> str:
    """便利函數：生成測試結果分組長條圖"""
    return ChartFormatter.fw_test_results_bar(title, fw_versions, pass_counts, fail_counts)


def format_version_comparison_chart(
    title: str,
    fw_versions: List[str],
    pass_counts: List[int],
    fail_counts: List[int],
    pass_rates: List[float],
    description: Optional[str] = None
) -> str:
    """
    便利函數：生成版本比較組合圖表（堆疊柱狀圖 + 折線圖）
    
    Args:
        title: 圖表標題
        fw_versions: FW 版本名稱列表
        pass_counts: 各版本 Pass 數量列表
        fail_counts: 各版本 Fail 數量列表
        pass_rates: 各版本通過率列表（百分比）
        description: 圖表描述（可選）
        
    Returns:
        str: :::chart 格式的 Markdown 標記
    """
    return ChartFormatter.version_comparison_chart(
        title, fw_versions, pass_counts, fail_counts, pass_rates, description
    )


def format_overall_metrics_line(
    title: str,
    fw_versions: List[str],
    metrics_data: Dict[str, List[float]]
) -> str:
    """便利函數：生成整體指標折線圖"""
    return ChartFormatter.fw_overall_metrics_line(title, fw_versions, metrics_data)


def format_category_pass_rate_heatmap(
    title: str,
    categories: List[str],
    fw_versions: List[str],
    pass_rates: List[List[float]]
) -> str:
    """便利函數：生成測試類別通過率熱力圖"""
    return ChartFormatter.category_pass_rate_heatmap(title, categories, fw_versions, pass_rates)


def format_category_fail_heatmap(
    title: str,
    categories: List[str],
    fw_versions: List[str],
    fail_counts: List[List[int]]
) -> str:
    """便利函數：生成測試類別 Fail 數量熱力圖"""
    return ChartFormatter.category_fail_heatmap(title, categories, fw_versions, fail_counts)
