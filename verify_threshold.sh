#!/bin/bash
# 
# 快速驗證 Threshold 設定
# ========================
# 
# 使用方式：
#   ./verify_threshold.sh
#

echo "============================================================"
echo "🔍 驗證向量搜尋 Threshold 設定"
echo "============================================================"
echo ""

# 檢查設定檔
echo "📁 檢查設定檔..."
FILE="library/common/knowledge_base/base_search_service.py"

if [ -f "$FILE" ]; then
    echo "✅ 找到設定檔: $FILE"
    echo ""
    
    echo "📊 當前 Threshold 設定："
    echo ""
    
    # 段落搜尋 threshold
    echo "  🎯 段落搜尋 (第一層)："
    grep -n "threshold=0\." "$FILE" | grep -A 1 "section_service.search_sections"
    echo ""
    
    # 文檔搜尋 threshold
    echo "  📄 文檔搜尋 (第二層)："
    grep -n "threshold=0\." "$FILE" | grep -B 2 "search_with_vectors_generic"
    echo ""
else
    echo "❌ 找不到設定檔: $FILE"
    exit 1
fi

echo "============================================================"
echo "💡 預期設定："
echo "   - 段落搜尋：threshold=0.7"
echo "   - 文檔搜尋：threshold=0.6"
echo "============================================================"
echo ""

# 詢問是否執行測試
read -p "是否執行測試腳本？(y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧪 執行測試..."
    docker exec ai-django python test_threshold_adjustment.py
fi
