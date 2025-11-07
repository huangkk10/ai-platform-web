/**
 * Analytics Configuration - 分析系統配置
 * 
 * 此配置檔案統一管理所有 Assistant 的分析端點和顯示設定
 * 當需要新增新的 Assistant 時，只需在此檔案中添加配置即可
 */

export const ANALYTICS_ASSISTANTS = {
  rvt: {
    id: 'rvt',
    name: 'RVT Assistant',
    displayName: 'RVT Assistant',
    shortName: 'RVT',
    description: 'RVT 相關測試指導和協助',
    icon: 'RobotOutlined',
    color: '#1890ff',
    tagColor: 'blue',
    
    // API 端點配置
    endpoints: {
      overview: '/api/rvt-analytics/overview/',
      questions: '/api/rvt-analytics/questions/',
      satisfaction: '/api/rvt-analytics/satisfaction/',
      trends: '/api/rvt-analytics/trends/',
      feedback: '/api/rvt-analytics/feedback/',
      'question-history': '/api/rvt-analytics/question-history/'
    },
    
    // 問題分類配置（用於圖表顏色對應）
    questionCategories: {
      'rvt_execution': { label: 'RVT 執行', color: '#1890ff' },
      'known_issue': { label: '已知問題', color: '#f5222d' },
      'troubleshooting': { label: '故障排除', color: '#faad14' },
      'configuration': { label: '配置問題', color: '#52c41a' },
      'specification': { label: '規範查詢', color: '#722ed1' },
      'general_inquiry': { label: '一般查詢', color: '#13c2c2' }
    },
    
    // 預設查詢參數
    defaultParams: {
      days: 30,
      mode: 'smart'
    }
  },
  
  protocol: {
    id: 'protocol',
    name: 'Protocol Assistant',
    displayName: 'Protocol Assistant',
    shortName: 'Protocol',
    description: 'Protocol 測試相關指導和協助',
    icon: 'ExperimentOutlined',
    color: '#52c41a',
    tagColor: 'green',
    
    // API 端點配置
    endpoints: {
      overview: '/api/protocol-analytics/overview/',
      questions: '/api/protocol-analytics/questions/',
      satisfaction: '/api/protocol-analytics/satisfaction/',
      trends: '/api/protocol-analytics/trends/',
      feedback: '/api/protocol-analytics/feedback/', // 暫未實作
      'question-history': '/api/protocol-analytics/question-history/' // 暫未實作
    },
    
    // 問題分類配置
    questionCategories: {
      'protocol_execution': { label: 'Protocol 執行', color: '#1890ff' },
      'known_issue': { label: '已知問題', color: '#f5222d' },
      'configuration': { label: '配置問題', color: '#52c41a' },
      'specification': { label: '規範查詢', color: '#722ed1' },
      'troubleshooting': { label: '故障排除', color: '#faad14' },
      'test_result': { label: '測試結果', color: '#fa8c16' },
      'environment': { label: '環境問題', color: '#13c2c2' },
      'general_inquiry': { label: '一般查詢', color: '#eb2f96' }
    },
    
    // 預設查詢參數
    defaultParams: {
      days: 30,
      mode: 'smart'
    }
  }
};

/**
 * 獲取 Assistant 配置
 * @param {string} assistantId - Assistant ID (rvt, protocol, etc.)
 * @returns {Object} Assistant 配置對象
 */
export const getAssistantConfig = (assistantId) => {
  return ANALYTICS_ASSISTANTS[assistantId] || ANALYTICS_ASSISTANTS.rvt;
};

/**
 * 獲取所有可用的 Assistant 列表
 * @returns {Array} Assistant 配置陣列
 */
export const getAvailableAssistants = () => {
  return Object.values(ANALYTICS_ASSISTANTS);
};

/**
 * 獲取 API 端點 URL
 * @param {string} assistantId - Assistant ID
 * @param {string} endpointType - 端點類型 (overview, questions, satisfaction, trends)
 * @returns {string} 完整的 API URL
 */
export const getApiEndpoint = (assistantId, endpointType) => {
  const config = getAssistantConfig(assistantId);
  return config.endpoints[endpointType];
};

/**
 * 獲取問題分類顏色
 * @param {string} assistantId - Assistant ID
 * @param {string} category - 問題分類名稱
 * @returns {string} 顏色代碼
 */
export const getCategoryColor = (assistantId, category) => {
  const config = getAssistantConfig(assistantId);
  return config.questionCategories[category]?.color || '#d9d9d9';
};

/**
 * 獲取問題分類標籤
 * @param {string} assistantId - Assistant ID
 * @param {string} category - 問題分類名稱
 * @returns {string} 分類標籤
 */
export const getCategoryLabel = (assistantId, category) => {
  const config = getAssistantConfig(assistantId);
  return config.questionCategories[category]?.label || category;
};

/**
 * 檢查 Assistant 是否可用
 * @param {string} assistantId - Assistant ID
 * @returns {boolean} 是否可用
 */
export const isAssistantAvailable = (assistantId) => {
  return assistantId in ANALYTICS_ASSISTANTS;
};

export default ANALYTICS_ASSISTANTS;
