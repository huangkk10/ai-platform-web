#!/bin/bash
# 測試圖片 API 是否正常

echo "🔍 測試圖片 API..."
echo ""

for id in 32 35 36 37 38 39 40; do
    echo -n "ID $id: "
    http_code=$(curl -s -o /dev/null -w "%{http_code}" http://10.10.172.127/api/content-images/$id/)
    if [ "$http_code" = "200" ]; then
        echo "✅ $http_code"
    else
        echo "❌ $http_code"
    fi
done

echo ""
echo "📊 測試圖片資料內容："
curl -s http://10.10.172.127/api/content-images/36/ | python3 -m json.tool | head -20
