"""
SAF 意圖分析器
=============

使用 Dify Chat API 分析用戶查詢的意圖，輸出結構化的意圖識別結果。

功能：
1. 分析用戶問題的意圖
2. 提取相關參數（客戶名稱、控制器型號、專案名稱等）
3. 返回信心度評分
4. 提供降級的關鍵字匹配方案

作者：AI Platform Team
創建日期：2025-12-05
"""

import json
import logging
import re
import requests
from typing import Optional, Dict, Any

from .intent_types import (
    IntentType, 
    IntentResult, 
    KNOWN_CUSTOMERS, 
    KNOWN_CONTROLLERS,
    INTENT_KEYWORDS
)

logger = logging.getLogger(__name__)


# ============================================================
# 意圖分析 Prompt（完全在程式碼中管理，可版本控制）
# ============================================================
INTENT_ANALYSIS_PROMPT = """
你是一個意圖分析器，專門分析用戶關於 SAF 專案管理系統的問題。

【重要規則】
1. 你必須**只輸出 JSON 格式**，不要輸出任何其他文字、解釋或標記
2. 仔細理解用戶問題的**語義意圖**，不要只看關鍵字
3. 即使語句結構不同，只要意思相同就應該識別為相同意圖

## 可用的意圖類型

### 1. query_projects_by_customer - 按客戶查詢專案
用戶想知道某個客戶有哪些專案時使用。
- 常見問法：
  - 「XX 有哪些專案」「列出 XX 的專案」「XX 的專案有哪些」
  - 「XX 的專案列表」「顯示 XX 的專案」「查詢 XX 的專案」
  - 「XX 目前有什麼專案」「XX 正在進行的專案」
- 參數：customer (客戶名稱)

### 2. query_projects_by_controller - 按控制器查詢專案
用戶想知道某個控制器型號被哪些專案使用時使用。
- 常見問法：
  - 「SM2264 用在哪些專案」「哪些專案用 SM2264」
  - 「SM2264 被哪些專案使用」「哪些專案使用 SM2264」
  - 「那些專案使用 SM2264」「什麼專案用 SM2264 控制器」
  - 「SM2264 的專案」「用 SM2264 的專案有哪些」
  - 「列出使用 SM2264 的專案」「查詢 SM2264 相關專案」
- 參數：controller (控制器型號，如 SM2264、SM2269XT)

### 3. query_project_detail - 查詢專案詳細資訊
用戶想了解某個特定專案的詳細資訊時使用。
- 常見問法：
  - 「XX 專案的詳細資訊」「告訴我 XX 專案」
  - 「XX 專案是什麼」「查詢 XX 專案」「XX 專案的資訊」
  - 「介紹一下 XX 專案」「XX 專案的狀況」
- 參數：project_name (專案名稱)

### 4. query_project_summary - 查詢專案測試摘要
用戶想了解某個專案的測試結果或測試狀況時使用。
- 常見問法：
  - 「XX 的測試結果」「XX 測試狀況」「XX 的測試摘要」
  - 「XX 專案測試得怎麼樣」「XX 的 QA 結果」
  - 「XX 測試通過了嗎」「XX 的驗證結果」
- 參數：project_name (專案名稱)

### 5. count_projects - 統計專案數量
用戶想知道專案數量時使用。
- 常見問法：
  - 「有多少專案」「幾個專案」「專案數量」「總共多少專案」
  - 「XX 有多少專案」「XX 有幾個專案」「XX 專案數」
  - 「統計專案數量」「專案總數」
- 參數：customer (可選，若指定特定客戶)

### 6. list_all_customers - 列出所有客戶
用戶想知道系統中有哪些客戶時使用。
- 常見問法：
  - 「有哪些客戶」「客戶列表」「列出所有客戶」
  - 「系統裡有什麼客戶」「支援哪些客戶」「客戶有誰」
- 參數：無

### 7. list_all_controllers - 列出所有控制器
用戶想知道系統中有哪些控制器型號時使用。
- 常見問法：
  - 「有哪些控制器」「控制器列表」「列出所有控制器」
  - 「支援哪些控制器型號」「可以查詢哪些控制器」
- 參數：無

### 8. unknown - 無法識別的意圖
當問題與 SAF 專案管理系統無關時使用。

## 已知資訊

客戶名稱：WD, WDC, Western Digital, Samsung, Micron, Transcend, ADATA, UMIS, Biwin, Kioxia, SK Hynix
控制器型號：SM2263, SM2264, SM2267, SM2269, SM2264XT, SM2269XT, SM2508

## 輸出格式

{"intent": "意圖ID", "parameters": {}, "confidence": 0.0-1.0}

## 範例（注意各種不同的問法都應該正確識別）

輸入：WD 有哪些專案？
輸出：{"intent": "query_projects_by_customer", "parameters": {"customer": "WD"}, "confidence": 0.95}

輸入：列出 Samsung 的專案
輸出：{"intent": "query_projects_by_customer", "parameters": {"customer": "Samsung"}, "confidence": 0.93}

輸入：SM2264 控制器用在哪些專案？
輸出：{"intent": "query_projects_by_controller", "parameters": {"controller": "SM2264"}, "confidence": 0.95}

輸入：哪些專案使用 SM2269XT
輸出：{"intent": "query_projects_by_controller", "parameters": {"controller": "SM2269XT"}, "confidence": 0.93}

輸入：那些專案使用 SM2508
輸出：{"intent": "query_projects_by_controller", "parameters": {"controller": "SM2508"}, "confidence": 0.92}

輸入：SM2267 的專案有哪些
輸出：{"intent": "query_projects_by_controller", "parameters": {"controller": "SM2267"}, "confidence": 0.90}

輸入：用 SM2264 的專案
輸出：{"intent": "query_projects_by_controller", "parameters": {"controller": "SM2264"}, "confidence": 0.88}

輸入：總共有多少專案？
輸出：{"intent": "count_projects", "parameters": {}, "confidence": 0.95}

輸入：Samsung 有幾個專案？
輸出：{"intent": "count_projects", "parameters": {"customer": "Samsung"}, "confidence": 0.93}

輸入：WD 專案數量
輸出：{"intent": "count_projects", "parameters": {"customer": "WD"}, "confidence": 0.90}

輸入：DEMETER 專案的詳細資訊
輸出：{"intent": "query_project_detail", "parameters": {"project_name": "DEMETER"}, "confidence": 0.92}

輸入：查詢 APOLLO 專案
輸出：{"intent": "query_project_detail", "parameters": {"project_name": "APOLLO"}, "confidence": 0.88}

輸入：TITAN 的測試結果
輸出：{"intent": "query_project_summary", "parameters": {"project_name": "TITAN"}, "confidence": 0.90}

輸入：有哪些客戶
輸出：{"intent": "list_all_customers", "parameters": {}, "confidence": 0.95}

輸入：控制器列表
輸出：{"intent": "list_all_controllers", "parameters": {}, "confidence": 0.95}

輸入：今天天氣如何？
輸出：{"intent": "unknown", "parameters": {}, "confidence": 0.10}

輸入：幫我寫程式
輸出：{"intent": "unknown", "parameters": {}, "confidence": 0.10}

---

現在分析以下問題：
"""


class SAFIntentAnalyzer:
    """
    SAF 意圖分析器
    
    使用 Dify 的 SAF_Intent_Analyzer App 進行意圖分析。
    Prompt 完全由程式碼控制，方便版本管理。
    """
    
    def __init__(self, api_key: str = None, timeout: int = None):
        """
        初始化意圖分析器
        
        Args:
            api_key: Dify API Key（可選，使用配置管理器的預設值）
            timeout: 請求超時時間（可選）
        """
        # 延遲導入避免循環依賴
        from library.config.dify_config_manager import get_saf_intent_analyzer_config
        
        config = get_saf_intent_analyzer_config()
        
        self.api_key = api_key or config.api_key
        self.api_url = config.api_url
        self.timeout = timeout or config.timeout
        
        logger.info(f"SAFIntentAnalyzer 初始化完成: api_url={self.api_url}")
    
    def analyze(self, query: str, user_id: str = "saf-smart-query") -> IntentResult:
        """
        分析用戶問題的意圖
        
        Args:
            query: 用戶的問題（如「WD 有哪些專案？」）
            user_id: 用戶識別碼
            
        Returns:
            IntentResult: 包含 intent, parameters, confidence
        """
        if not query or not query.strip():
            return IntentResult.create_error("查詢內容不能為空")
        
        try:
            # 組合完整的 prompt
            full_query = f"{INTENT_ANALYSIS_PROMPT}\n{query}"
            
            # 調用 Dify Chat API
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "inputs": {},
                    "query": full_query,
                    "response_mode": "blocking",
                    "conversation_id": "",  # 每次都是新對話
                    "user": user_id
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"Dify API 錯誤: {response.status_code} - {response.text[:200]}")
                return self._fallback_analysis(query)
            
            data = response.json()
            answer = data.get('answer', '')
            
            logger.info(f"意圖分析原始回應: {answer[:200]}...")
            
            return self._parse_intent_response(answer, query)
            
        except requests.Timeout:
            logger.error("Dify API 請求超時")
            return self._fallback_analysis(query)
        except requests.ConnectionError as e:
            logger.error(f"Dify API 連線錯誤: {str(e)}")
            return self._fallback_analysis(query)
        except Exception as e:
            logger.error(f"意圖分析錯誤: {str(e)}")
            return self._fallback_analysis(query)
    
    def _parse_intent_response(self, answer: str, original_query: str) -> IntentResult:
        """
        解析 LLM 返回的 JSON
        
        Args:
            answer: LLM 回應
            original_query: 原始查詢
            
        Returns:
            IntentResult: 解析後的意圖結果
        """
        try:
            # 清理可能的 markdown 標記
            clean_answer = self._clean_json_response(answer)
            
            # 解析 JSON
            intent_data = json.loads(clean_answer)
            
            # 創建 IntentResult
            intent_type = IntentType.from_string(intent_data.get('intent', 'unknown'))
            
            return IntentResult(
                intent=intent_type,
                parameters=intent_data.get('parameters', {}),
                confidence=float(intent_data.get('confidence', 0.5)),
                raw_response=answer
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失敗: {e}, 嘗試提取: {answer[:100]}...")
            return self._extract_json_from_text(answer, original_query)
    
    def _clean_json_response(self, answer: str) -> str:
        """
        清理 JSON 回應中的 markdown 標記
        
        Args:
            answer: 原始回應
            
        Returns:
            str: 清理後的 JSON 字串
        """
        clean_answer = answer.strip()
        
        # 移除 markdown 代碼塊標記
        if clean_answer.startswith("```json"):
            clean_answer = clean_answer[7:]
        if clean_answer.startswith("```"):
            clean_answer = clean_answer[3:]
        if clean_answer.endswith("```"):
            clean_answer = clean_answer[:-3]
        
        return clean_answer.strip()
    
    def _extract_json_from_text(self, text: str, original_query: str) -> IntentResult:
        """
        從文字中提取 JSON（處理 LLM 可能添加的額外文字）
        
        Args:
            text: 包含 JSON 的文字
            original_query: 原始查詢
            
        Returns:
            IntentResult: 提取的意圖結果
        """
        # 嘗試找到包含 "intent" 的 JSON 部分
        json_pattern = r'\{[^{}]*"intent"[^{}]*\}'
        matches = re.findall(json_pattern, text)
        
        for match in matches:
            try:
                intent_data = json.loads(match)
                if 'intent' in intent_data:
                    intent_type = IntentType.from_string(intent_data.get('intent', 'unknown'))
                    return IntentResult(
                        intent=intent_type,
                        parameters=intent_data.get('parameters', {}),
                        confidence=float(intent_data.get('confidence', 0.5)),
                        raw_response=text
                    )
            except (json.JSONDecodeError, ValueError):
                continue
        
        # 完全無法解析，使用降級方案
        logger.warning("無法從回應中提取 JSON，使用降級方案")
        return self._fallback_analysis(original_query)
    
    def _fallback_analysis(self, query: str) -> IntentResult:
        """
        降級處理：使用簡單的關鍵字匹配
        當 LLM 調用失敗時的備用方案
        
        Args:
            query: 用戶查詢
            
        Returns:
            IntentResult: 基於關鍵字匹配的意圖結果
        """
        query_lower = query.lower()
        
        # 1. 檢查客戶關鍵字
        detected_customer = self._detect_customer(query)
        if detected_customer:
            # 檢查是數量查詢還是列表查詢
            if self._has_count_keywords(query):
                return IntentResult(
                    intent=IntentType.COUNT_PROJECTS,
                    parameters={'customer': detected_customer},
                    confidence=0.6,
                    raw_response=f"Fallback: detected customer={detected_customer}, count query"
                )
            elif self._has_project_keywords(query):
                return IntentResult(
                    intent=IntentType.QUERY_PROJECTS_BY_CUSTOMER,
                    parameters={'customer': detected_customer},
                    confidence=0.6,
                    raw_response=f"Fallback: detected customer={detected_customer}"
                )
        
        # 2. 檢查控制器關鍵字
        detected_controller = self._detect_controller(query)
        if detected_controller:
            return IntentResult(
                intent=IntentType.QUERY_PROJECTS_BY_CONTROLLER,
                parameters={'controller': detected_controller},
                confidence=0.6,
                raw_response=f"Fallback: detected controller={detected_controller}"
            )
        
        # 3. 通用數量查詢（無特定客戶）
        if self._has_count_keywords(query):
            return IntentResult(
                intent=IntentType.COUNT_PROJECTS,
                parameters={},
                confidence=0.6,
                raw_response="Fallback: count query without customer"
            )
        
        # 4. 客戶列表查詢
        if '客戶' in query and ('有哪些' in query or '列表' in query or '全部' in query):
            return IntentResult(
                intent=IntentType.LIST_ALL_CUSTOMERS,
                parameters={},
                confidence=0.6,
                raw_response="Fallback: list customers query"
            )
        
        # 5. 控制器列表查詢
        if '控制器' in query and ('有哪些' in query or '列表' in query or '全部' in query):
            return IntentResult(
                intent=IntentType.LIST_ALL_CONTROLLERS,
                parameters={},
                confidence=0.6,
                raw_response="Fallback: list controllers query"
            )
        
        # 6. 檢查是否是專案詳情或摘要查詢
        project_name = self._detect_project_name(query)
        if project_name:
            if '測試' in query or '結果' in query or '摘要' in query:
                return IntentResult(
                    intent=IntentType.QUERY_PROJECT_SUMMARY,
                    parameters={'project_name': project_name},
                    confidence=0.5,
                    raw_response=f"Fallback: project summary query for {project_name}"
                )
            else:
                return IntentResult(
                    intent=IntentType.QUERY_PROJECT_DETAIL,
                    parameters={'project_name': project_name},
                    confidence=0.5,
                    raw_response=f"Fallback: project detail query for {project_name}"
                )
        
        # 無法識別
        return IntentResult(
            intent=IntentType.UNKNOWN,
            parameters={},
            confidence=0.3,
            raw_response=f"Fallback: unknown intent for query: {query}"
        )
    
    def _detect_customer(self, query: str) -> Optional[str]:
        """
        檢測查詢中的客戶名稱
        
        Args:
            query: 用戶查詢
            
        Returns:
            Optional[str]: 檢測到的客戶名稱，或 None
        """
        query_upper = query.upper()
        
        # 按優先順序檢查（較長的名稱優先）
        sorted_customers = sorted(KNOWN_CUSTOMERS, key=len, reverse=True)
        
        for customer in sorted_customers:
            if customer.upper() in query_upper:
                # 標準化返回值
                customer_mapping = {
                    'WDC': 'WD',
                    'WESTERN DIGITAL': 'WD',
                }
                return customer_mapping.get(customer.upper(), customer)
        
        return None
    
    def _detect_controller(self, query: str) -> Optional[str]:
        """
        檢測查詢中的控制器型號
        
        Args:
            query: 用戶查詢
            
        Returns:
            Optional[str]: 檢測到的控制器型號，或 None
        """
        query_upper = query.upper()
        
        for controller in KNOWN_CONTROLLERS:
            if controller.upper() in query_upper:
                return controller.upper()
        
        # 嘗試匹配部分型號（如 2264）
        partial_pattern = r'(\d{4})'
        matches = re.findall(partial_pattern, query)
        for match in matches:
            full_model = f"SM{match}"
            if full_model in [c.upper() for c in KNOWN_CONTROLLERS]:
                return full_model
        
        return None
    
    def _detect_project_name(self, query: str) -> Optional[str]:
        """
        檢測查詢中的專案名稱（啟發式方法）
        
        Args:
            query: 用戶查詢
            
        Returns:
            Optional[str]: 檢測到的專案名稱，或 None
        """
        # 常見專案名稱模式
        # 1. 大寫字母開頭的單詞（不是已知客戶或控制器）
        words = re.findall(r'\b([A-Z][a-zA-Z0-9]+)\b', query)
        
        for word in words:
            word_upper = word.upper()
            # 排除已知客戶和控制器
            if word_upper not in [c.upper() for c in KNOWN_CUSTOMERS]:
                if word_upper not in [c.upper() for c in KNOWN_CONTROLLERS]:
                    if word not in ['GET', 'POST', 'API', 'SAF']:
                        return word
        
        return None
    
    def _has_count_keywords(self, query: str) -> bool:
        """檢查是否包含數量相關關鍵字"""
        count_keywords = ['多少', '幾個', '數量', 'count', '總共', '專案數']
        return any(kw in query.lower() for kw in count_keywords)
    
    def _has_project_keywords(self, query: str) -> bool:
        """檢查是否包含專案相關關鍵字"""
        project_keywords = ['專案', 'project', '有哪些', '列表', '列出']
        return any(kw in query.lower() for kw in project_keywords)


# ============================================================
# 便利函數
# ============================================================

def analyze_intent(query: str, user_id: str = "saf-smart-query") -> IntentResult:
    """
    分析用戶查詢意圖的便利函數
    
    Args:
        query: 用戶查詢
        user_id: 用戶 ID
        
    Returns:
        IntentResult: 意圖分析結果
    """
    analyzer = SAFIntentAnalyzer()
    return analyzer.analyze(query, user_id)


# ============================================================
# 測試用 main 函數
# ============================================================
if __name__ == "__main__":
    # 測試案例
    test_queries = [
        "WD 有哪些專案？",
        "Samsung 有幾個專案？",
        "SM2264 控制器用在哪些專案？",
        "有哪些客戶？",
        "DEMETER 專案的詳細資訊",
        "DEMETER 的測試結果如何？",
        "有哪些控制器？",
        "今天天氣如何？"
    ]
    
    analyzer = SAFIntentAnalyzer()
    
    print("=" * 60)
    print("SAF 意圖分析器測試")
    print("=" * 60)
    
    for query in test_queries:
        result = analyzer.analyze(query)
        print(f"\n問題: {query}")
        print(f"意圖: {result.intent.value}")
        print(f"參數: {result.parameters}")
        print(f"信心度: {result.confidence:.2f}")
        print(f"有效: {result.is_valid()}")
        print("-" * 40)
