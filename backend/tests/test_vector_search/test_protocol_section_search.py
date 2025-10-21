"""
Protocol Guide 分段向量搜尋測試
================================

測試目標：
1. 創建包含多個段落的 Protocol Guide 文檔
2. 驗證分段向量化是否正確執行
3. 測試語義搜尋是否只返回相關段落
"""

import os
import sys
import django

# 設置 Django 環境
# 在容器內，backend 目錄就是 /app
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ProtocolGuide
from django.db import connection
from api.services.embedding_service import get_embedding_service


# 測試文檔內容
TEST_MARKDOWN_CONTENT = """# USB Type-C 測試指南

本文檔涵蓋 USB Type-C 介面的完整測試流程和規範。

## 1. 硬體規格驗證

### 1.1 連接器物理檢查

USB Type-C 連接器必須符合以下規格：
- 24 針腳設計，支援正反插
- 尺寸：8.4mm × 2.6mm
- 插拔壽命：10,000 次
- 工作溫度：-20°C 到 85°C

檢查步驟：
1. 使用游標卡尺測量連接器尺寸
2. 目視檢查針腳是否對齊
3. 執行插拔測試 100 次
4. 檢查接觸電阻是否小於 30mΩ

### 1.2 電氣特性測試

電源傳輸（Power Delivery）測試：
- VBUS 電壓範圍：5V, 9V, 12V, 15V, 20V
- 最大電流：5A
- 功率：最高 100W（20V @ 5A）

測試設備：
- 電源供應器（支援 PD 協議）
- 示波器（頻寬 ≥ 500MHz）
- 電流錶（精度 ±1%）
- 負載箱（可程式）

## 2. 數據傳輸測試

### 2.1 USB 2.0 訊號完整性

USB 2.0 差分訊號測試：
- 差分阻抗：90Ω ± 15%
- 上升/下降時間：4ns ~ 20ns
- 眼圖開口：最小 200mV @ 480Mbps

測試方法：
```python
# 使用示波器捕捉眼圖
def test_usb2_eye_diagram():
    scope.set_bandwidth('500MHz')
    scope.set_timebase('10ns/div')
    scope.trigger_on_edge('D+', rising_edge=True)
    
    # 捕捉 1000 個封包
    for i in range(1000):
        scope.capture_waveform()
    
    # 分析眼圖開口
    eye_height = scope.measure_eye_height()
    assert eye_height >= 200e-3  # 200mV
```

### 2.2 USB 3.2 Gen 2 高速測試

SuperSpeed 訊號測試（10Gbps）：
- 差分阻抗：85Ω ± 10%
- 抖動（Jitter）：< 0.3 UI
- TX 均衡：De-emphasis -3.5dB
- RX 均衡：CTLE + DFE

測試條件：
1. 使用 BERT（誤碼率測試儀）
2. 測試模式：PRBS-31
3. 測試時間：至少 5 分鐘
4. 目標 BER：< 10^-12

## 3. 協議層測試

### 3.1 USB PD 協議驗證

Power Delivery 協議測試項目：
- Source Capabilities 廣播
- Power Role Swap（PRS）
- Data Role Swap（DRS）
- VCONN Swap
- Fast Role Swap（FRS）

測試工具：
- Ellisys USB PD Protocol Analyzer
- Total Phase Beagle USB 480 Power Protocol Analyzer

### 3.2 DisplayPort Alt Mode

DP Alt Mode 測試（4K @ 60Hz）：
- 支援 HBR2（5.4Gbps/lane）
- 4 lane 配置
- 色彩深度：8/10 位元
- 音訊支援：8 通道 192kHz

測試腳本範例：
```bash
#!/bin/bash
# DP Alt Mode 進入測試
echo "1. 發送 Discover Identity"
pd_tool send_vdm --cmd=DISCOVER_IDENTITY

echo "2. 發送 Discover SVIDs"
pd_tool send_vdm --cmd=DISCOVER_SVIDS

echo "3. 檢查 DisplayPort SVID (0xFF01)"
pd_tool check_svid --svid=0xFF01

echo "4. 進入 DP Alt Mode"
pd_tool enter_mode --svid=0xFF01 --mode=0x0001
```

## 4. 相容性測試

### 4.1 裝置互通性

測試矩陣：
- 不同廠牌的 USB-C 裝置
- 不同 USB 版本（2.0, 3.2, 4.0）
- 不同作業系統（Windows, macOS, Linux）
- 不同電源配置（5V, 9V, 15V, 20V）

測試案例：
1. MacBook Pro + USB-C Hub
2. Dell XPS + USB-C Dock
3. Samsung Galaxy + USB-C 充電器
4. iPad Pro + USB-C 顯示器

### 4.2 線材驗證

USB-C 線材分類：
- USB 2.0 Only（僅充電或低速數據）
- USB 3.2 Gen 1（5Gbps）
- USB 3.2 Gen 2（10Gbps）
- USB4 Gen 3（40Gbps）
- Thunderbolt 3/4（40Gbps）

線材標記檢查：
- 電子標記晶片（E-Marker）
- 支援的 USB 版本圖示
- 功率標示（60W / 100W）
- 認證標誌（USB-IF, Thunderbolt）

## 5. 安全性與可靠度測試

### 5.1 過電流保護測試

測試步驟：
1. 設定電流限制為 6A（超過規格的 5A）
2. 監控 VBUS 電壓和電流
3. 驗證裝置是否切斷電源
4. 檢查保護電路響應時間（< 10ms）

預期結果：
- 電流不應超過 5.5A
- VBUS 電壓應降至 0V
- 不應有冒煙或燒焦現象

### 5.2 ESD 靜電放電測試

測試標準：IEC 61000-4-2
- 接觸放電：±8kV
- 空氣放電：±15kV
- 測試點：所有可接觸的金屬部分

測試設備：
- ESD 模擬器
- 接地墊
- 濕度控制：45-55% RH

## 6. 溫度與環境測試

### 6.1 高溫運作測試

測試條件：
- 環境溫度：85°C
- 測試時間：72 小時
- 負載：最大功率（100W）
- 監控項目：VBUS 電壓穩定度、連接器溫度

### 6.2 低溫啟動測試

測試條件：
- 環境溫度：-20°C
- 冷浸時間：4 小時
- 測試項目：冷機啟動、功能驗證
- 升溫速率：自然升溫（無強制加熱）

## 7. 常見問題排除

### 7.1 充電異常

可能原因：
1. 線材不支援 PD 協議
2. E-Marker 晶片損壞
3. 電源供應器不支援對應電壓
4. 裝置端 CC 針腳接觸不良

排除步驟：
```
1. 更換已知良好的 USB-C 線材
2. 使用 PD Analyzer 檢查協商過程
3. 測量 CC1/CC2 電壓（應為 0.2V-3.3V）
4. 檢查 VBUS 是否有 5V 預充電
```

### 7.2 數據傳輸不穩定

可能原因：
- 訊號完整性問題（阻抗不匹配）
- EMI 干擾
- 線材過長（> 2m for USB 3.2）
- 連接器接觸不良

診斷工具：
- USB Protocol Analyzer
- 頻譜分析儀
- TDR（時域反射計）

## 8. 報告範本

### 8.1 測試報告結構

1. **測試概要**
   - 測試目的
   - 測試對象
   - 測試日期
   - 測試工程師

2. **測試結果摘要**
   - PASS/FAIL 項目統計
   - 關鍵問題列表
   - 建議改善項目

3. **詳細測試數據**
   - 硬體規格測試
   - 電氣特性測試
   - 協議層測試
   - 相容性測試

4. **附錄**
   - 測試設備清單
   - 測試環境照片
   - 波形截圖
   - 原始數據檔案

## 9. 參考文獻

- USB Type-C Specification 2.1
- USB Power Delivery Specification 3.1
- DisplayPort Alt Mode on USB Type-C 2.0
- USB4 Specification Version 2.0
- IEC 61000-4-2 (ESD Test)
- MIL-STD-810H (Environmental Testing)
"""


def create_test_document():
    """創建測試文檔"""
    print("\n" + "="*80)
    print("📝 創建 Protocol Guide 測試文檔")
    print("="*80)
    
    # 刪除舊的測試文檔（如果存在）
    ProtocolGuide.objects.filter(title__startswith="[測試] USB Type-C").delete()
    print("✅ 已清理舊測試數據")
    
    # 創建新文檔
    guide = ProtocolGuide.objects.create(
        title="[測試] USB Type-C 測試指南",
        content=TEST_MARKDOWN_CONTENT
    )
    
    print(f"✅ 測試文檔已創建 (ID: {guide.id})")
    print(f"   標題: {guide.title}")
    print(f"   內容長度: {len(guide.content)} 字元")
    
    # 手動觸發段落向量生成
    print("\n🔄 手動生成段落向量...")
    from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
    
    vectorization_service = SectionVectorizationService()
    result = vectorization_service.vectorize_document_sections(
        source_table='protocol_guide',
        source_id=guide.id,
        markdown_content=guide.content,
        document_title=guide.title
    )
    
    if result['success']:
        print(f"✅ 段落向量生成成功：{result['vectorized_count']}/{result['total_sections']} 個段落")
    else:
        print(f"❌ 段落向量生成失敗：{result.get('error', '未知錯誤')}")
    
    return guide


def check_section_vectors(guide_id):
    """檢查段落向量是否已生成"""
    print("\n" + "="*80)
    print("🔍 檢查段落向量生成狀態")
    print("="*80)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                section_id,
                heading_level,
                heading_text,
                LEFT(content, 100) as content_preview,
                word_count,
                vector_dims(embedding) as vector_dimension
            FROM document_section_embeddings
            WHERE source_table = 'protocol_guide'
              AND source_id = %s
            ORDER BY section_id;
        """, [guide_id])
        
        rows = cursor.fetchall()
        
        if not rows:
            print("❌ 未找到段落向量！")
            return False
        
        print(f"✅ 找到 {len(rows)} 個段落向量")
        print("\n段落列表：")
        print("-" * 120)
        print(f"{'段落 ID':<15} {'層級':<6} {'標題':<40} {'字數':<8} {'向量維度':<10}")
        print("-" * 120)
        
        for row in rows:
            section_id, level, heading, content_preview, word_count, dimension = row
            print(f"{section_id:<15} {level:<6} {heading[:38]:<40} {word_count:<8} {dimension:<10}")
        
        return True


def test_semantic_search(query, expected_section=None):
    """測試語義搜尋"""
    print("\n" + "="*80)
    print(f"🔎 測試語義搜尋: {query}")
    print("="*80)
    
    # 獲取 embedding service
    embedding_service = get_embedding_service('ultra_high')
    
    # 生成查詢向量
    query_embedding = embedding_service.generate_embedding(query)
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    # 執行向量搜尋
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                section_id,
                heading_text,
                section_path,
                LEFT(content, 200) as content_preview,
                1 - (embedding <=> %s::vector) as similarity
            FROM document_section_embeddings
            WHERE source_table = 'protocol_guide'
            ORDER BY embedding <=> %s::vector
            LIMIT 5;
        """, [embedding_str, embedding_str])
        
        results = cursor.fetchall()
        
        if not results:
            print("❌ 未找到任何結果！")
            return
        
        print(f"\n找到 {len(results)} 個相關段落：")
        print("-" * 140)
        print(f"{'相似度':<10} {'段落 ID':<15} {'標題':<40} {'內容預覽':<50}")
        print("-" * 140)
        
        for i, (section_id, heading, path, content, similarity) in enumerate(results, 1):
            similarity_pct = similarity * 100
            marker = "✅" if expected_section and section_id == expected_section else "  "
            print(f"{marker} {similarity_pct:>6.2f}%  {section_id:<15} {heading[:38]:<40} {content[:48]:<50}")
        
        # 驗證結果
        if expected_section:
            top_section = results[0][0]
            if top_section == expected_section:
                print(f"\n✅ 測試通過：最相關的段落是 {expected_section}")
            else:
                print(f"\n⚠️  預期段落 {expected_section}，但最相關的是 {top_section}")


def main():
    """主測試流程"""
    print("\n" + "="*80)
    print("🚀 Protocol Guide 分段向量搜尋測試")
    print("="*80)
    
    # 步驟 1：創建測試文檔
    guide = create_test_document()
    
    # 步驟 2：檢查段落向量（不需要等待，已經生成）
    success = check_section_vectors(guide.id)
    
    if not success:
        print("\n❌ 段落向量生成失敗，請檢查 ViewSet Manager 配置")
        return
    
    # 步驟 3：執行語義搜尋測試
    test_cases = [
        {
            'query': '如何測試 USB 眼圖？',
            'expected': 'section_2_1',  # USB 2.0 訊號完整性
            'description': '應該找到「USB 2.0 訊號完整性」段落'
        },
        {
            'query': 'DisplayPort 替代模式怎麼測試？',
            'expected': 'section_3_2',  # DisplayPort Alt Mode
            'description': '應該找到「DisplayPort Alt Mode」段落'
        },
        {
            'query': '過電流保護測試步驟',
            'expected': 'section_5_1',  # 過電流保護測試
            'description': '應該找到「過電流保護測試」段落'
        },
        {
            'query': '充電不穩定如何排查？',
            'expected': 'section_7_1',  # 充電異常
            'description': '應該找到「充電異常」段落'
        },
        {
            'query': '高溫環境測試條件',
            'expected': 'section_6_1',  # 高溫運作測試
            'description': '應該找到「高溫運作測試」段落'
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n測試案例 {i}/{len(test_cases)}: {test_case['description']}")
        test_semantic_search(
            query=test_case['query'],
            expected_section=test_case['expected']
        )
    
    print("\n" + "="*80)
    print("✅ 測試完成！")
    print("="*80)


if __name__ == '__main__':
    main()
