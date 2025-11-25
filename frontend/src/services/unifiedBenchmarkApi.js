/**
 * 統一 Benchmark 測試案例 API Service
 * 整合 Protocol 和 VSA 測試案例管理
 */

import axios from 'axios';

// 確保所有請求都帶上認證憑證
const api = axios.create({
  withCredentials: true,
});

/**
 * 統一 Benchmark API 服務
 */
export const unifiedBenchmarkApi = {
  /**
   * 獲取測試案例列表
   * @param {Object} params - 查詢參數
   * @param {string} params.test_type - 測試類型: protocol, vsa, hybrid
   * @param {string} params.difficulty_level - 難度: easy, medium, hard
   * @param {boolean} params.is_active - 是否啟用
   * @param {string} params.category - 類別
   * @param {string} params.test_class_name - 測試類別名稱
   * @param {string} params.search - 搜尋關鍵字
   * @returns {Promise}
   */
  getTestCases: (params = {}) => {
    return api.get('/api/unified-benchmark/test-cases/', { params });
  },

  /**
   * 獲取單個測試案例詳情
   * @param {number} id - 測試案例 ID
   * @returns {Promise}
   */
  getTestCase: (id) => {
    return api.get(`/api/unified-benchmark/test-cases/${id}/`);
  },

  /**
   * 創建測試案例
   * @param {Object} data - 測試案例資料
   * @returns {Promise}
   */
  createTestCase: (data) => {
    return api.post('/api/unified-benchmark/test-cases/', data);
  },

  /**
   * 更新測試案例
   * @param {number} id - 測試案例 ID
   * @param {Object} data - 更新的資料
   * @returns {Promise}
   */
  updateTestCase: (id, data) => {
    return api.put(`/api/unified-benchmark/test-cases/${id}/`, data);
  },

  /**
   * 部分更新測試案例
   * @param {number} id - 測試案例 ID
   * @param {Object} data - 更新的資料
   * @returns {Promise}
   */
  patchTestCase: (id, data) => {
    return api.patch(`/api/unified-benchmark/test-cases/${id}/`, data);
  },

  /**
   * 刪除測試案例
   * @param {number} id - 測試案例 ID
   * @returns {Promise}
   */
  deleteTestCase: (id) => {
    return api.delete(`/api/unified-benchmark/test-cases/${id}/`);
  },

  /**
   * 切換測試案例的啟用狀態
   * @param {number} id - 測試案例 ID
   * @returns {Promise}
   */
  toggleActive: (id) => {
    return api.patch(`/api/unified-benchmark/test-cases/${id}/toggle_active/`);
  },

  /**
   * 獲取統計資料
   * @param {string} testType - 測試類型 (可選): protocol, vsa
   * @returns {Promise}
   */
  getStatistics: (testType = null) => {
    const params = testType ? { test_type: testType } : {};
    return api.get('/api/unified-benchmark/test-cases/statistics/', { params });
  },

  /**
   * 獲取所有類別列表
   * @param {string} testType - 測試類型 (可選)
   * @returns {Promise}
   */
  getCategories: (testType = null) => {
    const params = testType ? { test_type: testType } : {};
    return api.get('/api/unified-benchmark/test-cases/categories/', { params });
  },

  /**
   * 獲取所有測試類別列表
   * @param {string} testType - 測試類型 (可選)
   * @returns {Promise}
   */
  getTestClasses: (testType = null) => {
    const params = testType ? { test_type: testType } : {};
    return api.get('/api/unified-benchmark/test-cases/test_classes/', { params });
  },

  /**
   * 批量匯入測試案例
   * @param {string} testType - 測試類型: protocol, vsa
   * @param {Array} testCases - 測試案例陣列
   * @param {boolean} overwriteExisting - 是否覆蓋現有案例
   * @returns {Promise}
   */
  bulkImport: (testType, testCases, overwriteExisting = false) => {
    return api.post('/api/unified-benchmark/test-cases/bulk_import/', {
      test_type: testType,
      test_cases: testCases,
      overwrite_existing: overwriteExisting,
    });
  },

  /**
   * 批量匯出測試案例
   * @param {string} testType - 測試類型 (可選): protocol, vsa
   * @returns {Promise}
   */
  bulkExport: (testType = null) => {
    const params = testType ? { test_type: testType } : {};
    return api.get('/api/unified-benchmark/test-cases/bulk_export/', { params });
  },
};

export default unifiedBenchmarkApi;
