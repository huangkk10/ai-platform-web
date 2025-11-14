import { useState, useEffect } from 'react';
import axios from 'axios';
import { message } from 'antd';

/**
 * Hook for managing search threshold settings
 * 用於管理搜尋閾值設定的 Hook
 */
const useSearchThresholdSettings = () => {
  const [settings, setSettings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);
  const [error, setError] = useState(null);
  const [testResults, setTestResults] = useState(null);

  /**
   * Fetch all search threshold settings
   * 獲取所有搜尋閾值設定
   */
  const fetchSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/search-threshold-settings/');
      setSettings(response.data);
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || '獲取設定失敗';
      setError(errorMessage);
      message.error(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Fetch specific assistant's threshold settings
   * 獲取特定 assistant 的閾值設定
   */
  const fetchSetting = async (assistantType) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/search-threshold-settings/${assistantType}/`);
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || '獲取設定失敗';
      setError(errorMessage);
      message.error(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Update specific assistant's threshold settings
   * 更新特定 assistant 的閾值設定
   */
  const updateSetting = async (assistantType, data) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.patch(
        `/api/search-threshold-settings/${assistantType}/`,
        data
      );
      message.success('設定已成功保存');
      
      // Update local settings state
      setSettings(prev => 
        prev.map(setting => 
          setting.assistant_type === assistantType ? response.data : setting
        )
      );
      
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || '保存設定失敗';
      setError(errorMessage);
      
      // Display validation errors if available
      if (err.response?.data) {
        const errors = err.response.data;
        if (typeof errors === 'object') {
          Object.entries(errors).forEach(([field, messages]) => {
            if (Array.isArray(messages)) {
              messages.forEach(msg => message.error(`${field}: ${msg}`));
            } else {
              message.error(`${field}: ${messages}`);
            }
          });
        } else {
          message.error(errorMessage);
        }
      } else {
        message.error(errorMessage);
      }
      
      throw err;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Test search configuration without saving
   * 測試搜尋配置（不保存到資料庫）
   * 
   * @param {string} assistantType - Assistant 類型
   * @param {object} testConfig - 測試配置
   * @param {string} testQuery - 測試查詢字串
   * @returns {Promise} - 測試結果（包含 Stage 1 和 Stage 2 搜尋結果）
   */
  const testSearch = async (assistantType, testConfig, testQuery) => {
    setTestLoading(true);
    setError(null);
    setTestResults(null);
    
    try {
      const response = await axios.post(
        `/api/search-threshold-settings/${assistantType}/test_search/`,
        {
          test_config: testConfig,
          test_query: testQuery
        }
      );
      
      setTestResults(response.data);
      message.success('測試搜尋完成');
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 
                           err.response?.data?.error || 
                           err.message || 
                           '測試搜尋失敗';
      setError(errorMessage);
      message.error(errorMessage);
      
      // Display detailed error if available
      if (err.response?.data?.details) {
        console.error('Test search error details:', err.response.data.details);
      }
      
      throw err;
    } finally {
      setTestLoading(false);
    }
  };

  /**
   * Reset specific assistant's threshold settings to defaults
   * 重置特定 assistant 的閾值設定為預設值
   */
  const resetToDefaults = async (assistantType) => {
    setLoading(true);
    setError(null);
    
    try {
      // Default configuration
      const defaultConfig = {
        use_unified_weights: true,
        stage1_title_weight: 30,
        stage1_content_weight: 70,
        stage1_threshold: 0.65,
        stage2_title_weight: 30,
        stage2_content_weight: 70,
        stage2_threshold: 0.55
      };
      
      const response = await axios.patch(
        `/api/search-threshold-settings/${assistantType}/`,
        defaultConfig
      );
      
      message.success('設定已重置為預設值');
      
      // Update local settings state
      setSettings(prev => 
        prev.map(setting => 
          setting.assistant_type === assistantType ? response.data : setting
        )
      );
      
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || '重置設定失敗';
      setError(errorMessage);
      message.error(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Clear test results
   * 清除測試結果
   */
  const clearTestResults = () => {
    setTestResults(null);
  };

  // Auto-fetch settings on mount
  useEffect(() => {
    fetchSettings();
  }, []);

  return {
    // State
    settings,
    loading,
    testLoading,
    error,
    testResults,
    
    // Actions
    fetchSettings,
    fetchSetting,
    updateSetting,
    testSearch,
    resetToDefaults,
    clearTestResults
  };
};

export default useSearchThresholdSettings;
