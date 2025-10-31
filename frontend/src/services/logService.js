/**
 * 日誌查看器 API 服務
 * 
 * 提供與後端日誌 API 的通訊功能：
 * - 列出日誌檔案
 * - 查看日誌內容
 * - 下載日誌檔案
 * - 搜尋日誌
 * - 獲取統計資訊
 */

import axios from 'axios';

// 配置 API 基礎路徑
const API_BASE_URL = '/api';

const logService = {
  /**
   * 列出所有日誌檔案
   * 
   * @returns {Promise<Object>} 日誌檔案列表
   */
  async listLogFiles() {
    try {
      const response = await axios.get(`${API_BASE_URL}/system/logs/list/`);
      return response.data;
    } catch (error) {
      console.error('列出日誌檔案失敗:', error);
      throw error;
    }
  },

  /**
   * 查看日誌檔案內容
   * 
   * @param {string} filename - 日誌檔案名稱
   * @param {Object} params - 查詢參數
   * @param {number} params.lines - 顯示行數（預設 100）
   * @param {boolean} params.tail - 從尾部讀取（預設 true）
   * @param {string} params.level - 過濾日誌等級（INFO, WARNING, ERROR, CRITICAL）
   * @param {string} params.search - 搜尋關鍵字
   * @param {string} params.startDate - 開始日期（YYYY-MM-DD）
   * @param {string} params.endDate - 結束日期（YYYY-MM-DD）
   * @returns {Promise<Object>} 日誌內容
   */
  async viewLogFile(filename, params = {}) {
    try {
      const response = await axios.get(`${API_BASE_URL}/system/logs/view/`, {
        params: {
          file: filename,
          lines: params.lines || 100,
          tail: params.tail !== false,
          level: params.level,
          search: params.search,
          start_date: params.startDate,
          end_date: params.endDate
        }
      });
      return response.data;
    } catch (error) {
      console.error('查看日誌失敗:', error);
      throw error;
    }
  },

  /**
   * 下載日誌檔案
   * 
   * @param {string} filename - 日誌檔案名稱
   * @param {string} format - 檔案格式（txt 或 json，預設 txt）
   * @returns {Promise<void>}
   */
  async downloadLogFile(filename, format = 'txt') {
    try {
      const response = await axios.get(`${API_BASE_URL}/system/logs/download/`, {
        params: { file: filename, format },
        responseType: 'blob'
      });

      // 觸發瀏覽器下載
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const downloadFilename = format === 'json' ? `${filename}.json` : filename;
      link.setAttribute('download', downloadFilename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      console.log(`日誌檔案 ${filename} 下載成功`);
    } catch (error) {
      console.error('下載日誌失敗:', error);
      throw error;
    }
  },

  /**
   * 搜尋日誌內容
   * 
   * @param {string} filename - 日誌檔案名稱
   * @param {string} searchQuery - 搜尋關鍵字
   * @param {Object} options - 搜尋選項
   * @param {boolean} options.caseSensitive - 是否區分大小寫（預設 false）
   * @param {boolean} options.regex - 是否使用正則表達式（預設 false）
   * @param {number} options.contextLines - 上下文行數（預設 3）
   * @param {number} options.maxResults - 最大結果數（預設 50）
   * @returns {Promise<Object>} 搜尋結果
   */
  async searchLogFile(filename, searchQuery, options = {}) {
    try {
      const response = await axios.post(`${API_BASE_URL}/system/logs/search/`, {
        file: filename,
        search: searchQuery,
        case_sensitive: options.caseSensitive || false,
        regex: options.regex || false,
        context_lines: options.contextLines || 3,
        max_results: options.maxResults || 50
      });
      return response.data;
    } catch (error) {
      console.error('搜尋日誌失敗:', error);
      throw error;
    }
  },

  /**
   * 獲取日誌統計資訊
   * 
   * @param {string} filename - 日誌檔案名稱
   * @param {number} days - 統計最近 N 天（預設 7）
   * @returns {Promise<Object>} 統計資訊
   */
  async getLogStats(filename, days = 7) {
    try {
      const response = await axios.get(`${API_BASE_URL}/system/logs/stats/`, {
        params: { file: filename, days }
      });
      return response.data;
    } catch (error) {
      console.error('獲取日誌統計失敗:', error);
      throw error;
    }
  }
};

export default logService;
