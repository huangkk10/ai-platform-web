#!/bin/bash
# 測試 Protocol Guide 編輯頁面的圖片顯示功能

echo "=========================================="
echo "🧪 Protocol Guide 圖片顯示功能測試"
echo "=========================================="
echo ""

echo "📝 測試步驟："
echo ""
echo "1️⃣ 打開瀏覽器訪問："
echo "   http://10.10.172.127/knowledge/protocol-guide/markdown-edit/10"
echo ""
echo "2️⃣ 在左側編輯器中輸入："
echo "   # 測試圖片顯示"
echo "   "
echo "   這是一個測試文檔，包含圖片："
echo "   "
echo "   [IMG:32]"
echo "   "
echo "   [IMG:35]"
echo ""
echo "3️⃣ 檢查右側預覽窗是否顯示："
echo "   ✅ 實際的圖片縮圖（不是文字佔位符）"
echo "   ✅ 圖片名稱（如 1.1.jpg, 2.jpg）"
echo "   ✅ 圖片可點擊放大"
echo "   ✅ 載入動畫（如果圖片正在載入）"
echo ""
echo "4️⃣ 對比 markdown-test 頁面效果："
echo "   http://10.10.172.127/dev/markdown-test"
echo "   （應該完全一致）"
echo ""
echo "=========================================="
echo "📊 已知的測試圖片 ID："
echo "=========================================="
echo ""

# 顯示測試圖片資訊
docker exec ai-django python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ContentImage
from django.contrib.contenttypes.models import ContentType
from api.models import ProtocolGuide

protocol_content_type = ContentType.objects.get_for_model(ProtocolGuide)
images = ContentImage.objects.filter(content_type=protocol_content_type).order_by('id')[:5]

if images:
    for img in images:
        print(f'  🖼️  ID: {img.id:3d} | {img.filename:20s} | {img.width}×{img.height}')
else:
    print('  ❌ 沒有找到 Protocol Guide 相關圖片')
" 2>/dev/null

echo ""
echo "=========================================="
echo "✅ 修改內容總結："
echo "=========================================="
echo ""
echo "1. ✅ 添加了 ReactMarkdown 和相關工具的 import"
echo "2. ✅ 創建了 renderMarkdownWithImages 函數"
echo "3. ✅ 修改了 MdEditor 的 renderHTML 屬性"
echo "4. ✅ 添加了圖片顯示的 CSS 樣式"
echo "5. ✅ 前端容器已重啟並編譯成功"
echo ""
echo "🎯 預期效果："
echo "   在 Protocol Guide 編輯頁面的右側預覽窗中"
echo "   輸入 [IMG:32] 會顯示實際的圖片縮圖"
echo "   就像在 markdown-test 頁面中一樣！"
echo ""
echo "=========================================="
