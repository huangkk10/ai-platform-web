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


# 便利函數
def format_trend_chart(title: str, fw_versions: List[str], metrics: Dict[str, List[float]]) -> str:
    """便利函數：生成 FW 趨勢圖"""
    return ChartFormatter.fw_trend_chart(title, fw_versions, metrics)


def format_comparison_chart(title: str, fw_versions: List[str], metrics: Dict[str, List[float]]) -> str:
    """便利函數：生成比較柱狀圖"""
    return ChartFormatter.fw_comparison_bar_chart(title, fw_versions, metrics)
