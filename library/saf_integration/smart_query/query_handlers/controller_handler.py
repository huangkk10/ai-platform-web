"""
ControllerHandler - 按控制器查詢專案
====================================

處理 query_projects_by_controller 意圖。

功能改進（方案 C：智能去重）：
- 當結果超過閾值時，按「客戶 + NAND 類型」聚合
- 每組只顯示一筆代表性記錄
- 加上數量標記「(共 N 筆)」
- 提供摘要統計

作者：AI Platform Team
創建日期：2025-12-05
更新日期：2025-12-15 - 新增智能去重功能
"""

import logging
from typing import Dict, Any, List
from collections import defaultdict

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)

# 配置
AGGREGATION_THRESHOLD = 30  # 超過此數量啟用聚合模式


class ControllerHandler(BaseHandler):
    """
    控制器查詢處理器
    
    處理按控制器型號查詢專案的請求。
    支援智能去重：當結果過多時自動聚合顯示。
    """
    
    handler_name = "controller_handler"
    supported_intent = "query_projects_by_controller"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行按控制器查詢專案
        
        Args:
            parameters: {"controller": "SM2264"}
            
        Returns:
            QueryResult: 包含使用該控制器的所有專案
        """
        self._log_query(parameters)
        
        # 驗證參數
        error = self.validate_parameters(parameters, required=['controller'])
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        controller = parameters.get('controller')
        
        try:
            # 使用正確的 API 方法獲取所有專案
            projects_list = self.api_client.get_all_projects()
            
            if not projects_list:
                return QueryResult.error(
                    "無法獲取專案列表",
                    self.handler_name,
                    parameters
                )
            
            # 過濾指定控制器的專案
            filtered_projects = self._filter_projects(
                projects_list, 
                'controller', 
                controller
            )
            
            if not filtered_projects:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"找不到使用控制器 '{controller}' 的專案"
                )
            
            total_count = len(filtered_projects)
            
            # 根據數量決定是否啟用聚合模式
            if total_count > AGGREGATION_THRESHOLD:
                # 啟用智能去重聚合
                message = self._format_aggregated_response(
                    controller, filtered_projects, total_count
                )
                # 聚合後的資料用於 data 欄位
                aggregated_data = self._aggregate_projects(filtered_projects)
                result_data = aggregated_data
            else:
                # 原始列表模式
                formatted_projects = [
                    self._format_project_data(p) for p in filtered_projects
                ]
                message = self._format_simple_response(
                    controller, formatted_projects, total_count
                )
                result_data = formatted_projects
            
            result = QueryResult.success(
                data=result_data,
                count=total_count,
                query_type=self.handler_name,
                parameters=parameters,
                message=message,
                metadata={
                    'controller': controller,
                    'total_projects': total_count,
                    'aggregated': total_count > AGGREGATION_THRESHOLD
                }
            )
            
            self._log_result(result)
            return result
            
        except Exception as e:
            return self._handle_api_error(e, parameters)
    
    def _aggregate_projects(self, projects: List[Dict]) -> List[Dict]:
        """
        按「客戶 + NAND 類型」聚合專案
        
        Args:
            projects: 原始專案列表
            
        Returns:
            List[Dict]: 聚合後的專案列表（每組一筆代表）
        """
        # 使用 (customer, nand) 作為聚合 key
        groups = defaultdict(list)
        
        for p in projects:
            customer = p.get('customer', 'Unknown')
            nand = p.get('nand', 'Unknown')
            key = (customer, nand)
            groups[key].append(p)
        
        # 從每組取第一筆作為代表，並標記數量
        aggregated = []
        for (customer, nand), group_projects in groups.items():
            representative = group_projects[0].copy()
            representative['_group_count'] = len(group_projects)
            representative['_group_key'] = f"{customer}|{nand}"
            aggregated.append(representative)
        
        # 按客戶名稱排序
        aggregated.sort(key=lambda x: (x.get('customer', ''), x.get('nand', '')))
        
        return aggregated
    
    def _format_aggregated_response(self, controller: str, 
                                     projects: List[Dict],
                                     total_count: int) -> str:
        """
        格式化聚合模式的回應（智能去重）
        
        Args:
            controller: 控制器名稱
            projects: 原始專案列表
            total_count: 總專案數
            
        Returns:
            str: Markdown 格式的回應
        """
        # 按「客戶 + NAND」聚合
        groups = defaultdict(list)
        for p in projects:
            customer = p.get('customer', 'Unknown')
            nand = p.get('nand', 'Unknown')
            key = (customer, nand)
            groups[key].append(p)
        
        # 統計客戶數和 NAND 類型數
        unique_customers = set(p.get('customer', '') for p in projects)
        unique_nands = set(p.get('nand', '') for p in projects)
        
        lines = [
            f"## 🔌 使用 {controller} 控制器的專案",
            "",
            f"**總計：{total_count} 個專案** | **{len(unique_customers)} 個客戶** | **{len(unique_nands)} 種 NAND 類型**",
            "",
            "---",
            "",
            "### 📊 按客戶與 NAND 類型分組",
            "",
            "| 客戶 | NAND 類型 | 專案數量 | 負責人 |",
            "|------|----------|---------|--------|"
        ]
        
        # 按客戶名稱排序
        sorted_groups = sorted(groups.items(), key=lambda x: (x[0][0], x[0][1]))
        
        for (customer, nand), group_projects in sorted_groups:
            count = len(group_projects)
            
            # 收集負責人（去重）
            pls = set()
            for p in group_projects:
                pl = p.get('pl', '')
                if pl:
                    # pl 可能是逗號分隔的多人
                    for person in pl.split(','):
                        person = person.strip()
                        if person:
                            pls.add(person)
            
            pl_str = ', '.join(sorted(pls)[:3])  # 最多顯示 3 人
            if len(pls) > 3:
                pl_str += f' (+{len(pls)-3}人)'
            
            # 數量標記
            count_badge = f"**{count}**" if count > 1 else "1"
            
            lines.append(f"| {customer} | {nand} | {count_badge} | {pl_str} |")
        
        lines.append("")
        
        # 添加客戶統計摘要
        lines.extend(self._format_customer_summary(projects, unique_customers))
        
        # 添加 NAND 統計摘要
        lines.extend(self._format_nand_summary(projects, unique_nands))
        
        # 提示訊息
        lines.extend([
            "",
            "---",
            "",
            "💡 **提示**：如需查看特定客戶的詳細專案列表，可詢問：",
            f"- 「{controller} + Transcend 的專案」",
            f"- 「{list(unique_customers)[0] if unique_customers else 'XX'} 使用 {controller} 的專案有哪些」"
        ])
        
        return "\n".join(lines)
    
    def _format_customer_summary(self, projects: List[Dict], 
                                  unique_customers: set) -> List[str]:
        """
        格式化客戶統計摘要
        
        Args:
            projects: 專案列表
            unique_customers: 唯一客戶集合
            
        Returns:
            List[str]: Markdown 行列表
        """
        # 統計每個客戶的專案數
        customer_counts = defaultdict(int)
        for p in projects:
            customer = p.get('customer', 'Unknown')
            customer_counts[customer] += 1
        
        # 按數量排序（前 10 名）
        sorted_customers = sorted(
            customer_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        total = sum(customer_counts.values())
        
        lines = [
            "### 👥 客戶分布（Top 10）",
            "",
            "| 排名 | 客戶 | 專案數 | 佔比 |",
            "|------|------|--------|------|"
        ]
        
        for i, (customer, count) in enumerate(sorted_customers, 1):
            percentage = count / total * 100 if total > 0 else 0
            lines.append(f"| {i} | {customer} | {count} | {percentage:.1f}% |")
        
        if len(customer_counts) > 10:
            lines.append(f"| ... | 其他 {len(customer_counts) - 10} 個客戶 | ... | ... |")
        
        lines.append("")
        
        return lines
    
    def _format_nand_summary(self, projects: List[Dict],
                              unique_nands: set) -> List[str]:
        """
        格式化 NAND 類型統計摘要
        
        Args:
            projects: 專案列表
            unique_nands: 唯一 NAND 類型集合
            
        Returns:
            List[str]: Markdown 行列表
        """
        # 統計每種 NAND 的專案數
        nand_counts = defaultdict(int)
        for p in projects:
            nand = p.get('nand', 'Unknown')
            nand_counts[nand] += 1
        
        # 按數量排序
        sorted_nands = sorted(
            nand_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        total = sum(nand_counts.values())
        
        lines = [
            "### 💾 NAND 類型分布",
            "",
            "| NAND 類型 | 專案數 | 佔比 |",
            "|----------|--------|------|"
        ]
        
        for nand, count in sorted_nands:
            percentage = count / total * 100 if total > 0 else 0
            lines.append(f"| {nand} | {count} | {percentage:.1f}% |")
        
        lines.append("")
        
        return lines
    
    def _format_simple_response(self, controller: str,
                                 projects: List[Dict],
                                 total_count: int) -> str:
        """
        格式化簡單列表模式的回應（專案數量較少時）
        
        Args:
            controller: 控制器名稱
            projects: 格式化後的專案列表
            total_count: 總專案數
            
        Returns:
            str: Markdown 格式的回應
        """
        lines = [
            f"使用 {controller} 控制器的專案共有 {total_count} 個：",
            "",
            "| 專案名稱 | 客戶 | 控制器 | NAND 類型 | 負責人 |",
            "|---------|------|--------|----------|--------|"
        ]
        
        for p in projects:
            name = p.get('project_name', p.get('projectName', '-'))
            customer = p.get('customer', '-')
            ctrl = p.get('controller', controller)
            nand = p.get('nand', '-')
            pl = p.get('pl', '-')
            
            lines.append(f"| {name} | {customer} | {ctrl} | {nand} | {pl} |")
        
        return "\n".join(lines)
