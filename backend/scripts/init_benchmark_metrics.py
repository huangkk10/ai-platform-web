"""
初始化搜尋跑分系統的預設評分維度
Date: 2025-11-21
"""
import os
import sys
import django

# 設定 Django 環境
sys.path.append("/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

from api.models import BenchmarkMetric


def init_metrics():
    """初始化預設評分維度"""
    
    metrics = [
        {
            "metric_name": "精準度 (Precision)",
            "metric_key": "precision",
            "metric_type": "precision",
            "description": "回傳結果中正確答案的比例",
            "calculation_method": "TP / (TP + FP)",
            "weight": 0.35,
            "display_order": 1
        },
        {
            "metric_name": "召回率 (Recall)",
            "metric_key": "recall",
            "metric_type": "recall",
            "description": "正確答案被找回的比例",
            "calculation_method": "TP / (TP + FN)",
            "weight": 0.30,
            "display_order": 2
        },
        {
            "metric_name": "F1 分數 (F1-Score)",
            "metric_key": "f1_score",
            "metric_type": "quality",
            "description": "精準度和召回率的調和平均數",
            "calculation_method": "2 * (Precision * Recall) / (Precision + Recall)",
            "weight": 0.20,
            "display_order": 3
        },
        {
            "metric_name": "平均響應時間 (Avg Response Time)",
            "metric_key": "avg_response_time",
            "metric_type": "speed",
            "description": "搜尋查詢的平均處理時間 (ms)",
            "calculation_method": "sum(response_times) / count",
            "weight": 0.10,
            "display_order": 4
        },
        {
            "metric_name": "NDCG@5",
            "metric_key": "ndcg_at_5",
            "metric_type": "quality",
            "description": "考慮排序的搜尋品質指標",
            "calculation_method": "DCG / IDCG (前5個結果)",
            "weight": 0.05,
            "display_order": 5
        }
    ]
    
    print("🚀 開始初始化評分維度...")
    print(f"   總共 {len(metrics)} 個維度\n")
    
    for metric_data in metrics:
        metric, created = BenchmarkMetric.objects.update_or_create(
            metric_key=metric_data['metric_key'],
            defaults=metric_data
        )
        
        status = "✅ 創建" if created else "✅ 更新"
        print(f"{status}: {metric.metric_name} (權重: {metric.weight * 100}%)")
    
    print(f"\n✅ 預設評分維度初始化完成！")
    
    # 驗證
    total = BenchmarkMetric.objects.filter(is_active=True).count()
    total_weight = sum(m.weight for m in BenchmarkMetric.objects.filter(is_active=True))
    
    print(f"\n📊 驗證結果:")
    print(f"   啟用的維度數量: {total}")
    print(f"   總權重: {total_weight:.2f} (應為 1.00)")
    
    if abs(float(total_weight) - 1.0) < 0.01:
        print("   ✅ 權重總和正確")
    else:
        print(f"   ⚠️  警告：權重總和不為 1.00")


if __name__ == '__main__':
    init_metrics()
