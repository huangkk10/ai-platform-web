"""
SAF 資料轉換器

將 SAF API 回應轉換為 Dify 外部知識庫格式

Dify 格式要求:
{
    "records": [
        {
            "content": str,        # 文檔內容
            "score": float,        # 相關性分數 (0-1)
            "title": str,          # 文檔標題
            "metadata": dict       # 額外元數據
        }
    ]
}
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SAFDataTransformer:
    """SAF 資料轉換器"""
    
    def __init__(self):
        """初始化轉換器"""
        pass
    
    # ==================== Projects 轉換 ====================
    
    def transform_projects(
        self,
        projects: List[Dict[str, Any]],
        query: str = "",
        score_threshold: float = 0.0
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        轉換 SAF 專案列表為 Dify 格式
        
        Args:
            projects: SAF 專案列表
            query: 搜尋關鍵字（用於計算相關性）
            score_threshold: 分數閾值
            
        Returns:
            Dify 格式的記錄列表
        """
        records = []
        query_lower = query.lower() if query else ""
        
        for project in projects:
            try:
                record = self._transform_project(project, query_lower)
                
                # 過濾低分數記錄
                if record["score"] >= score_threshold:
                    records.append(record)
                    
            except Exception as e:
                logger.warning(f"轉換專案失敗: {e}, 專案: {project.get('projectName', 'N/A')}")
                continue
        
        # 按分數排序
        records.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"轉換 {len(records)} 個專案記錄 (總計: {len(projects)}, 閾值: {score_threshold})")
        
        return {"records": records}
    
    def _transform_project(
        self,
        project: Dict[str, Any],
        query_lower: str = ""
    ) -> Dict[str, Any]:
        """
        轉換單個專案為 Dify 記錄格式
        
        Args:
            project: SAF 專案數據
            query_lower: 小寫的搜尋關鍵字
            
        Returns:
            Dify 記錄格式
        """
        project_name = project.get("projectName", "Unknown")
        customer = project.get("customer", "Unknown")
        project_id = project.get("id", 0)
        
        # 構建內容
        content = self._build_project_content(project)
        
        # 計算相關性分數
        score = self._calculate_project_score(project, query_lower)
        
        # 構建標題
        title = f"{project_name} - {customer}"
        
        # 構建元數據
        metadata = {
            "source": "saf_projects",
            "project_id": project_id,
            "project_name": project_name,
            "customer": customer,
            "created_at": project.get("createdAt", ""),
            "storage_type": project.get("storageType", ""),
            "project_status": project.get("projectStatus", ""),
        }
        
        return {
            "content": content,
            "score": score,
            "title": title,
            "metadata": metadata
        }
    
    def _build_project_content(self, project: Dict[str, Any]) -> str:
        """
        構建專案的內容描述
        
        Args:
            project: SAF 專案數據
            
        Returns:
            格式化的專案描述
        """
        lines = []
        
        # 基本資訊
        lines.append(f"專案名稱: {project.get('projectName', 'N/A')}")
        lines.append(f"客戶: {project.get('customer', 'N/A')}")
        
        # 專案詳情
        if project.get("storageType"):
            lines.append(f"儲存類型: {project.get('storageType')}")
        
        if project.get("projectStatus"):
            lines.append(f"專案狀態: {project.get('projectStatus')}")
        
        if project.get("capacity"):
            lines.append(f"容量: {project.get('capacity')}")
        
        if project.get("interface"):
            lines.append(f"介面: {project.get('interface')}")
        
        if project.get("formFactor"):
            lines.append(f"規格: {project.get('formFactor')}")
        
        # 日期資訊
        if project.get("createdAt"):
            lines.append(f"建立日期: {project.get('createdAt')}")
        
        # 專案 ID
        lines.append(f"專案 ID: {project.get('id', 'N/A')}")
        
        return "\n".join(lines)
    
    def _calculate_project_score(
        self,
        project: Dict[str, Any],
        query_lower: str
    ) -> float:
        """
        計算專案的相關性分數
        
        Args:
            project: SAF 專案數據
            query_lower: 小寫的搜尋關鍵字
            
        Returns:
            相關性分數 (0.0-1.0)
        """
        if not query_lower:
            return 0.7  # 無查詢時返回默認分數
        
        score = 0.0
        
        # 專案名稱匹配 (權重最高)
        project_name = project.get("projectName", "").lower()
        if query_lower in project_name:
            score += 0.5
            if project_name == query_lower:
                score += 0.3  # 完全匹配額外加分
        
        # 客戶名稱匹配
        customer = project.get("customer", "").lower()
        if query_lower in customer:
            score += 0.3
            if customer == query_lower:
                score += 0.1
        
        # 儲存類型匹配
        storage_type = project.get("storageType", "").lower()
        if query_lower in storage_type:
            score += 0.2
        
        # 介面匹配
        interface = project.get("interface", "").lower()
        if query_lower in interface:
            score += 0.15
        
        # 確保分數在有效範圍內
        return min(1.0, max(0.0, score))
    
    # ==================== Summary 轉換 ====================
    
    def transform_summary(
        self,
        summary_data: Dict[str, Any],
        project_name: str = "",
        score_threshold: float = 0.0
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        轉換 SAF Summary 為 Dify 格式
        
        Args:
            summary_data: SAF Summary 數據
            project_name: 專案名稱
            score_threshold: 分數閾值
            
        Returns:
            Dify 格式的記錄列表
        """
        records = []
        
        try:
            # 總覽記錄
            overview_record = self._transform_summary_overview(summary_data, project_name)
            if overview_record["score"] >= score_threshold:
                records.append(overview_record)
            
            # 測試項目記錄
            test_items = summary_data.get("testItems", [])
            for item in test_items:
                record = self._transform_test_item(item, project_name)
                if record["score"] >= score_threshold:
                    records.append(record)
            
        except Exception as e:
            logger.error(f"轉換 Summary 失敗: {e}")
        
        logger.info(f"轉換 {len(records)} 個 Summary 記錄")
        
        return {"records": records}
    
    def _transform_summary_overview(
        self,
        summary_data: Dict[str, Any],
        project_name: str
    ) -> Dict[str, Any]:
        """
        轉換 Summary 總覽為 Dify 記錄
        
        Args:
            summary_data: SAF Summary 數據
            project_name: 專案名稱
            
        Returns:
            Dify 記錄格式
        """
        # 構建內容
        content_lines = [
            f"專案: {project_name}",
            f"測試總覽 Summary",
            "",
        ]
        
        # 添加統計資訊
        if "totalTests" in summary_data:
            content_lines.append(f"總測試數: {summary_data['totalTests']}")
        if "passedTests" in summary_data:
            content_lines.append(f"通過測試: {summary_data['passedTests']}")
        if "failedTests" in summary_data:
            content_lines.append(f"失敗測試: {summary_data['failedTests']}")
        if "passRate" in summary_data:
            content_lines.append(f"通過率: {summary_data['passRate']}%")
        
        return {
            "content": "\n".join(content_lines),
            "score": 0.9,  # Summary 總覽高分數
            "title": f"{project_name} - 測試總覽",
            "metadata": {
                "source": "saf_summary",
                "project_name": project_name,
                "record_type": "overview",
                "total_tests": summary_data.get("totalTests", 0),
                "pass_rate": summary_data.get("passRate", 0),
            }
        }
    
    def _transform_test_item(
        self,
        item: Dict[str, Any],
        project_name: str
    ) -> Dict[str, Any]:
        """
        轉換單個測試項目為 Dify 記錄
        
        Args:
            item: 測試項目數據
            project_name: 專案名稱
            
        Returns:
            Dify 記錄格式
        """
        test_name = item.get("testName", "Unknown Test")
        status = item.get("status", "unknown")
        
        # 構建內容
        content_lines = [
            f"專案: {project_name}",
            f"測試項目: {test_name}",
            f"狀態: {status}",
        ]
        
        if item.get("description"):
            content_lines.append(f"描述: {item['description']}")
        
        if item.get("errorMessage"):
            content_lines.append(f"錯誤訊息: {item['errorMessage']}")
        
        if item.get("executionTime"):
            content_lines.append(f"執行時間: {item['executionTime']}")
        
        # 根據狀態決定分數
        score = 0.8 if status == "passed" else 0.85  # 失敗測試更重要
        
        return {
            "content": "\n".join(content_lines),
            "score": score,
            "title": f"{project_name} - {test_name}",
            "metadata": {
                "source": "saf_summary",
                "project_name": project_name,
                "record_type": "test_item",
                "test_name": test_name,
                "status": status,
            }
        }
    
    # ==================== Project Names 轉換 ====================
    
    def transform_project_names(
        self,
        projects: List[Dict[str, Any]],
        query: str = "",
        score_threshold: float = 0.0
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        轉換專案名稱列表為 Dify 格式（輕量級）
        
        Args:
            projects: SAF 專案列表
            query: 搜尋關鍵字
            score_threshold: 分數閾值
            
        Returns:
            Dify 格式的記錄列表
        """
        records = []
        query_lower = query.lower() if query else ""
        
        for project in projects:
            try:
                project_name = project.get("projectName", "")
                customer = project.get("customer", "")
                
                if not project_name:
                    continue
                
                # 計算分數
                score = self._calculate_name_score(project_name, customer, query_lower)
                
                if score >= score_threshold:
                    record = {
                        "content": f"專案: {project_name}\n客戶: {customer}",
                        "score": score,
                        "title": project_name,
                        "metadata": {
                            "source": "saf_project_names",
                            "project_name": project_name,
                            "customer": customer,
                        }
                    }
                    records.append(record)
                    
            except Exception as e:
                logger.warning(f"轉換專案名稱失敗: {e}")
                continue
        
        # 按分數排序
        records.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"轉換 {len(records)} 個專案名稱記錄")
        
        return {"records": records}
    
    def _calculate_name_score(
        self,
        project_name: str,
        customer: str,
        query_lower: str
    ) -> float:
        """
        計算專案名稱的相關性分數
        
        Args:
            project_name: 專案名稱
            customer: 客戶名稱
            query_lower: 小寫的搜尋關鍵字
            
        Returns:
            相關性分數 (0.0-1.0)
        """
        if not query_lower:
            return 0.7
        
        score = 0.0
        name_lower = project_name.lower()
        customer_lower = customer.lower()
        
        # 專案名稱匹配
        if query_lower in name_lower:
            score += 0.6
            if name_lower == query_lower:
                score += 0.3
        
        # 客戶名稱匹配
        if query_lower in customer_lower:
            score += 0.3
        
        return min(1.0, score)


# 全局轉換器實例
_transformer_instance: Optional[SAFDataTransformer] = None


def get_data_transformer() -> SAFDataTransformer:
    """
    獲取全局資料轉換器實例（單例模式）
    
    Returns:
        SAFDataTransformer 實例
    """
    global _transformer_instance
    if _transformer_instance is None:
        _transformer_instance = SAFDataTransformer()
    return _transformer_instance
