#!/bin/bash
# 診斷 v1.1.1 vs v1.2.1 返回內容差異的快速腳本

echo "=========================================="
echo "🔍 診斷 v1.1.1 vs v1.2.1 內容差異"
echo "=========================================="
echo ""

echo "📊 步驟 1：確認當前 Baseline 版本"
echo "----------------------------------------"
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT version_code, version_name, is_baseline 
FROM dify_config_version 
WHERE is_baseline = true;
" | grep -E "version_code|dify-two-tier"

echo ""
echo "📊 步驟 2：查看最近 20 條搜尋日誌"
echo "----------------------------------------"
echo "關鍵字：Stage、content_type、段落、全文"
echo ""
docker logs ai-django --tail 200 | grep -E "(使用 Baseline 版本|段落搜尋|全文搜尋|Stage [12]|content_type|IOL)" | tail -20

echo ""
echo "📊 步驟 3：統計不同 content_type 的出現次數"
echo "----------------------------------------"
docker logs ai-django --tail 500 | grep "content_type" | grep -oE "'(section|document)'" | sort | uniq -c

echo ""
echo "=========================================="
echo "💡 診斷提示"
echo "=========================================="
echo ""
echo "1. 如果看到 content_type='document' → 返回全文內容"
echo "2. 如果看到 content_type='section' → 返回段落內容"
echo "3. 如果看到 '執行 Stage 2' → 觸發了全文搜尋"
echo ""
echo "請你在 Dify 工作室中："
echo "  1. 切換到 v1.2.1，搜尋 'iol 密碼'"
echo "  2. 執行此腳本，記錄結果"
echo "  3. 切換到 v1.1.1，搜尋 'iol 密碼'"
echo "  4. 再次執行此腳本，比較差異"
echo ""
