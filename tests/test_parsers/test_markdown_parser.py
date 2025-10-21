"""
測試 Markdown 解析器

驗證 MarkdownStructureParser 的功能。
"""

import sys
import os

# 添加項目路徑
sys.path.insert(0, '/home/kevin/PythonCode/ai-platform-web/backend')
sys.path.insert(0, '/home/kevin/PythonCode/ai-platform-web')

from library.common.knowledge_base.markdown_parser import MarkdownStructureParser


def test_simple_markdown():
    """測試簡單 Markdown"""
    parser = MarkdownStructureParser()
    
    markdown = """
# 第一章

這是第一章的內容。

## 1.1 小節

這是小節的內容。

### 1.1.1 子節

這是子節的內容。

## 1.2 第二小節

這是第二小節的內容。
"""
    
    sections = parser.parse(markdown, "測試文檔")
    
    print("\n" + "="*60)
    print("測試簡單 Markdown 解析")
    print("="*60)
    print(f"\n總段落數: {len(sections)}\n")
    
    for i, section in enumerate(sections, 1):
        print(f"{i}. 段落 ID: {section.section_id}")
        print(f"   標題層級: {section.level}")
        print(f"   標題: {section.title}")
        print(f"   路徑: {section.path}")
        print(f"   父段落: {section.parent_id or '無'}")
        print(f"   子段落: {section.children_ids or '無'}")
        print(f"   內容長度: {section.word_count} 字元")
        print(f"   內容預覽: {section.content[:60]}...")
        print()


def test_protocol_guide_format():
    """測試 Protocol Guide 格式"""
    parser = MarkdownStructureParser()
    
    # 模擬 Protocol Guide 的 Markdown 格式
    markdown = """
# ULINK Protocol 測試基礎指南

本文檔說明 ULINK Protocol 的基本測試方法。

## 測試環境準備

需要準備以下環境：
- 測試設備
- ULINK 線材
- 測試軟體

## 連接步驟

### 1. 硬體連接

將 ULINK 連接到設備：
```bash
connect_ulink --port=USB0
```

### 2. 軟體設置

執行以下命令：
```python
import ulink
ulink.init()
```

## 常見問題

### Q1: 連接失敗怎麼辦？

檢查以下項目：
- 線材是否插好
- 驅動是否安裝

### Q2: 速度很慢？

優化建議：
- 減少數據量
- 更新韌體

## 總結

完成上述步驟即可開始測試。
"""
    
    sections = parser.parse(markdown, "ULINK Protocol 測試指南")
    
    print("\n" + "="*60)
    print("測試 Protocol Guide 格式解析")
    print("="*60)
    print(f"\n總段落數: {len(sections)}\n")
    
    for i, section in enumerate(sections, 1):
        print(f"{i}. [{section.section_id}] {'#' * section.level} {section.title}")
        print(f"   路徑: {section.path}")
        print(f"   父段落: {section.parent_id or '根'}")
        print(f"   子段落數: {len(section.children_ids)}")
        print(f"   包含代碼: {'✅' if section.has_code else '❌'}")
        print(f"   包含圖片: {'✅' if section.has_images else '❌'}")
        print(f"   內容長度: {section.word_count} 字元")
        print()


def test_no_headings():
    """測試無標題情況"""
    parser = MarkdownStructureParser()
    
    markdown = """這是一段沒有標題的 Markdown 文本。
    
只有純文本內容，沒有任何標題結構。"""
    
    sections = parser.parse(markdown, "無標題文檔")
    
    print("\n" + "="*60)
    print("測試無標題情況")
    print("="*60)
    print(f"\n總段落數: {len(sections)}\n")
    
    if sections:
        section = sections[0]
        print(f"段落 ID: {section.section_id}")
        print(f"標題: {section.title}")
        print(f"內容長度: {section.word_count} 字元")


if __name__ == "__main__":
    print("\n🧪 開始測試 Markdown 解析器...\n")
    
    try:
        test_simple_markdown()
        test_protocol_guide_format()
        test_no_headings()
        
        print("\n" + "="*60)
        print("✅ 所有測試完成！")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}\n")
        import traceback
        traceback.print_exc()
