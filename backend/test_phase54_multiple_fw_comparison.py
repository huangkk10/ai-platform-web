#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 5.4 多版本趨勢比較功能測試
================================

測試 CompareMultipleFWHandler 的功能：
- 指定多個 FW 版本比較
- 自動選擇最近 N 個版本
- 趨勢計算和分析
- 圖表 JSON 資料輸出

作者：AI Platform Team
創建日期：2025-12-08
"""

import os
import sys
import json
import time

# 確保可以導入專案模組
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

import django
django.setup()

from library.saf_integration.smart_query.query_handlers.compare_multiple_fw_handler import (
    CompareMultipleFWHandler
)


def print_separator(title: str = ""):
    """打印分隔線"""
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)


def test_basic_functionality():
    """測試基本功能"""
    print_separator("測試 1: 基本功能測試")
    
    handler = CompareMultipleFWHandler()
    print(f"Handler 名稱: {handler.handler_name}")
    print(f"支援的意圖: {handler.supported_intent}")
    
    print("✅ Handler 初始化成功")


def test_auto_select_latest(project_name: str = "Springsteen", latest_count: int = 3):
    """測試自動選擇最近 N 個版本"""
    print_separator(f"測試 2: 自動選擇最近 {latest_count} 個版本 ({project_name})")
    
    handler = CompareMultipleFWHandler()
    
    start_time = time.time()
    result = handler.execute({
        'project_name': project_name,
        'latest_count': latest_count,
        'include_chart_data': True
    })
    elapsed = time.time() - start_time
    
    print(f"\n執行耗時: {elapsed:.2f} 秒")
    print(f"狀態: {result.status}")
    
    if result.is_success():
        data = result.data
        print(f"\n✅ 成功比較 {data.get('versions_count', 0)} 個版本")
        print(f"版本列表: {data.get('versions_compared', [])}")
        
        # 顯示趨勢
        trends = data.get('trends', {})
        print(f"\n📈 趨勢分析:")
        for metric in ['pass', 'fail', 'pass_rate', 'completion_rate']:
            if metric in trends:
                t = trends[metric]
                print(f"  - {metric}: {t.get('trend', 'N/A')} {t.get('icon', '')} (變化: {t.get('change', 0):+})")
        
        # 顯示 Markdown 訊息的前 50 行
        message = result.message
        if message:
            print(f"\n📝 回應內容（前 50 行）:")
            lines = message.split('\n')[:50]
            for line in lines:
                print(line)
        
        # 顯示圖表資料摘要
        chart_data = data.get('chart_data', {})
        if chart_data:
            print(f"\n📊 圖表資料:")
            print(f"  - 圖表類型: {chart_data.get('chart_type', 'N/A')}")
            print(f"  - 版本數量: {chart_data.get('version_count', 0)}")
            print(f"  - 版本列表: {chart_data.get('versions', [])}")
            metrics = chart_data.get('metrics', {})
            if metrics:
                print(f"  - Pass 數列: {metrics.get('pass', [])}")
                print(f"  - Fail 數列: {metrics.get('fail', [])}")
    else:
        print(f"❌ 錯誤: {result.error_message}")
    
    return result


def test_specified_versions(project_name: str = "Springsteen", 
                             fw_versions: list = None):
    """測試指定多個版本比較"""
    print_separator(f"測試 3: 指定版本比較 ({project_name})")
    
    if fw_versions is None:
        fw_versions = ["G200X6EC", "G200X5DC", "G200X4CB"]
    
    handler = CompareMultipleFWHandler()
    
    print(f"指定版本: {fw_versions}")
    
    start_time = time.time()
    result = handler.execute({
        'project_name': project_name,
        'fw_versions': fw_versions,
        'include_chart_data': True
    })
    elapsed = time.time() - start_time
    
    print(f"\n執行耗時: {elapsed:.2f} 秒")
    print(f"狀態: {result.status}")
    
    if result.is_success():
        data = result.data
        print(f"\n✅ 成功比較 {data.get('versions_count', 0)} 個版本")
        print(f"實際比較的版本: {data.get('versions_compared', [])}")
        
        # 趨勢
        trends = data.get('trends', {})
        if 'by_category' in trends:
            cat_trends = trends['by_category']
            print(f"\n📁 按類別趨勢:")
            for cat, cat_data in list(cat_trends.items())[:5]:  # 只顯示前 5 個
                pass_change = cat_data.get('pass_change', 0)
                fail_change = cat_data.get('fail_change', 0)
                attention = "⚠️" if cat_data.get('needs_attention') else ""
                print(f"  - {cat}: Pass {pass_change:+}, Fail {fail_change:+} {attention}")
    else:
        print(f"❌ 錯誤: {result.error_message}")
    
    return result


def test_chart_data_structure():
    """測試圖表資料結構"""
    print_separator("測試 4: 圖表資料結構驗證")
    
    handler = CompareMultipleFWHandler()
    
    result = handler.execute({
        'project_name': 'Springsteen',
        'latest_count': 3,
        'include_chart_data': True
    })
    
    if result.is_success():
        chart_data = result.data.get('chart_data', {})
        
        print("圖表資料結構驗證:")
        
        # 必要欄位
        required_fields = ['chart_type', 'project_name', 'versions', 'metrics', 'trends']
        for field in required_fields:
            if field in chart_data:
                print(f"  ✅ {field}: 存在")
            else:
                print(f"  ❌ {field}: 缺失")
        
        # metrics 結構
        metrics = chart_data.get('metrics', {})
        metric_fields = ['pass', 'fail', 'pass_rate', 'completion_rate']
        print("\n  metrics 子欄位:")
        for field in metric_fields:
            if field in metrics:
                print(f"    ✅ {field}: {metrics[field]}")
            else:
                print(f"    ❌ {field}: 缺失")
        
        # 輸出完整 JSON（格式化）
        print("\n📋 完整圖表資料 JSON:")
        print(json.dumps(chart_data, indent=2, ensure_ascii=False))
    else:
        print(f"❌ 無法獲取圖表資料: {result.error_message}")


def test_few_versions():
    """測試版本數量不足的情況"""
    print_separator("測試 5: 版本數量不足情況")
    
    handler = CompareMultipleFWHandler()
    
    # 只指定 1 個版本
    result = handler.execute({
        'project_name': 'Springsteen',
        'fw_versions': ['G200X6EC']
    })
    
    print(f"狀態: {result.status}")
    if result.is_error():
        print(f"✅ 正確返回錯誤: {result.error_message}")
    else:
        print(f"⚠️ 預期應該返回錯誤，但返回了: {result.status}")


def test_nonexistent_project():
    """測試不存在的專案"""
    print_separator("測試 6: 不存在的專案")
    
    handler = CompareMultipleFWHandler()
    
    result = handler.execute({
        'project_name': 'NonExistentProject',
        'latest_count': 3
    })
    
    print(f"狀態: {result.status}")
    if result.is_error():
        print(f"✅ 正確返回錯誤: {result.error_message}")
    else:
        print(f"⚠️ 預期應該返回錯誤")


def test_many_versions(latest_count: int = 5):
    """測試比較更多版本"""
    print_separator(f"測試 7: 比較 {latest_count} 個版本")
    
    handler = CompareMultipleFWHandler()
    
    start_time = time.time()
    result = handler.execute({
        'project_name': 'Springsteen',
        'latest_count': latest_count,
        'include_chart_data': True
    })
    elapsed = time.time() - start_time
    
    print(f"執行耗時: {elapsed:.2f} 秒")
    print(f"狀態: {result.status}")
    
    if result.is_success():
        data = result.data
        print(f"✅ 成功比較 {data.get('versions_count', 0)} 個版本")
        
        chart_data = data.get('chart_data', {})
        if chart_data:
            metrics = chart_data.get('metrics', {})
            print(f"\n各版本 Pass 數: {metrics.get('pass', [])}")
            print(f"各版本 Fail 數: {metrics.get('fail', [])}")
    else:
        print(f"❌ 錯誤: {result.error_message}")


def main():
    """主測試函數"""
    print("\n" + "=" * 70)
    print("  Phase 5.4 多版本趨勢比較功能測試")
    print("=" * 70)
    
    # 執行測試
    test_basic_functionality()
    
    # 主要測試
    result1 = test_auto_select_latest("Springsteen", 3)
    
    # 如果基本測試通過，繼續其他測試
    if result1.is_success():
        test_specified_versions()
        test_chart_data_structure()
        test_few_versions()
        test_nonexistent_project()
        test_many_versions(5)
    else:
        print("\n⚠️ 基本測試未通過，跳過其他測試")
    
    print_separator("測試完成")
    print("\n🎉 Phase 5.4 多版本趨勢比較功能測試完成！")


if __name__ == '__main__':
    main()
