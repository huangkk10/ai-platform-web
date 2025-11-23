"""
自訂分頁類別
"""
from rest_framework.pagination import PageNumberPagination


class DynamicPageSizePagination(PageNumberPagination):
    """
    支援動態 page_size 的分頁類別
    
    使用方式：
    - 預設每頁 20 筆
    - 可透過 ?page_size=100 自訂每頁筆數
    - 最大每頁 1000 筆
    """
    page_size = 20
    page_size_query_param = 'page_size'  # 允許客戶端透過此參數自訂每頁筆數
    max_page_size = 1000  # 最大每頁筆數限制
