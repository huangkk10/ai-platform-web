/**
 * Benchmark API Client
 * 
 * 封裝所有 Benchmark 系統的 API 調用
 * 包含：Test Cases、Test Runs、Test Results、Versions
 */

import axios from 'axios';

// 確保所有請求都帶上認證憑證
const api = axios.create({
  withCredentials: true,
});

// ==================== Test Cases API ====================

/**
 * 獲取測試案例列表
 * @param {Object} params - 查詢參數
 * @param {string} params.category - 類別篩選
 * @param {string} params.difficulty - 難度篩選
 * @param {string} params.question_type - 題型篩選
 * @param {string} params.knowledge_source - 知識源篩選
 * @param {boolean} params.is_active - 啟用狀態篩選
 */
export const getTestCases = (params = {}) => {
  return api.get('/api/benchmark/test-cases/', { params });
};

/**
 * 獲取單個測試案例
 * @param {number} id - 測試案例 ID
 */
export const getTestCase = (id) => {
  return api.get(`/api/benchmark/test-cases/${id}/`);
};

/**
 * 創建測試案例
 * @param {Object} data - 測試案例數據
 */
export const createTestCase = (data) => {
  return api.post('/api/benchmark/test-cases/', data);
};

/**
 * 更新測試案例
 * @param {number} id - 測試案例 ID
 * @param {Object} data - 更新數據
 */
export const updateTestCase = (id, data) => {
  return api.put(`/api/benchmark/test-cases/${id}/`, data);
};

/**
 * 部分更新測試案例
 * @param {number} id - 測試案例 ID
 * @param {Object} data - 更新數據
 */
export const patchTestCase = (id, data) => {
  return api.patch(`/api/benchmark/test-cases/${id}/`, data);
};

/**
 * 刪除測試案例
 * @param {number} id - 測試案例 ID
 */
export const deleteTestCase = (id) => {
  return api.delete(`/api/benchmark/test-cases/${id}/`);
};

/**
 * 獲取測試案例統計資訊
 */
export const getTestCaseStatistics = () => {
  return api.get('/api/benchmark/test-cases/statistics/');
};

/**
 * 批量啟用測試案例
 * @param {Array<number>} ids - 測試案例 ID 列表
 */
export const bulkActivateTestCases = (ids) => {
  return api.post('/api/benchmark/test-cases/bulk_activate/', { ids });
};

/**
 * 批量停用測試案例
 * @param {Array<number>} ids - 測試案例 ID 列表
 */
export const bulkDeactivateTestCases = (ids) => {
  return api.post('/api/benchmark/test-cases/bulk_deactivate/', { ids });
};

// ==================== Test Runs API ====================

/**
 * 獲取測試執行列表
 * @param {Object} params - 查詢參數
 * @param {number} params.version_id - 版本 ID 篩選
 * @param {string} params.status - 狀態篩選
 * @param {string} params.run_type - 執行類型篩選
 * @param {number} params.days - 時間範圍篩選（天數）
 */
export const getTestRuns = (params = {}) => {
  return api.get('/api/benchmark/test-runs/', { params });
};

/**
 * 獲取單個測試執行
 * @param {number} id - 測試執行 ID
 */
export const getTestRun = (id) => {
  return api.get(`/api/benchmark/test-runs/${id}/`);
};

/**
 * 創建測試執行
 * @param {Object} data - 測試執行數據
 */
export const createTestRun = (data) => {
  return api.post('/api/benchmark/test-runs/', data);
};

/**
 * 更新測試執行
 * @param {number} id - 測試執行 ID
 * @param {Object} data - 更新數據
 */
export const updateTestRun = (id, data) => {
  return api.put(`/api/benchmark/test-runs/${id}/`, data);
};

/**
 * 刪除測試執行
 * @param {number} id - 測試執行 ID
 */
export const deleteTestRun = (id) => {
  return api.delete(`/api/benchmark/test-runs/${id}/`);
};

/**
 * 獲取測試執行的所有結果
 * @param {number} id - 測試執行 ID
 * @param {Object} params - 查詢參數
 * @param {boolean} params.passed_only - 是否只顯示通過的結果
 */
export const getTestRunResults = (id, params = {}) => {
  return api.get(`/api/benchmark/test-runs/${id}/results/`, { params });
};

/**
 * 啟動新的測試執行
 * @param {Object} data - 測試配置
 * @param {number} data.version_id - 版本 ID
 * @param {string} data.run_name - 執行名稱
 * @param {string} data.run_type - 執行類型 (manual/scheduled/ci)
 * @param {string} data.category - 類別篩選（可選）
 * @param {string} data.difficulty - 難度篩選（可選）
 * @param {string} data.question_type - 題型篩選（可選）
 * @param {number} data.limit - 限制題數（可選）
 * @param {string} data.notes - 備註（可選）
 */
export const startTest = (data) => {
  return api.post('/api/benchmark/test-runs/start_test/', data);
};

/**
 * 停止執行中的測試
 * @param {number} id - 測試執行 ID
 */
export const stopTest = (id) => {
  return api.post(`/api/benchmark/test-runs/${id}/stop_test/`);
};

/**
 * 比較兩個測試執行的結果
 * @param {number} runId1 - 測試執行 ID 1
 * @param {number} runId2 - 測試執行 ID 2
 */
export const compareTestRuns = (runId1, runId2) => {
  return api.post('/api/benchmark/test-runs/compare/', {
    run_id_1: runId1,
    run_id_2: runId2,
  });
};

// ==================== Test Results API ====================

/**
 * 獲取測試結果列表
 * @param {Object} params - 查詢參數
 * @param {number} params.test_run_id - 測試執行 ID 篩選
 * @param {number} params.test_case_id - 測試案例 ID 篩選
 * @param {boolean} params.is_passed - 通過狀態篩選
 */
export const getTestResults = (params = {}) => {
  return api.get('/api/benchmark/test-results/', { params });
};

/**
 * 獲取單個測試結果
 * @param {number} id - 測試結果 ID
 */
export const getTestResult = (id) => {
  return api.get(`/api/benchmark/test-results/${id}/`);
};

/**
 * 獲取所有失敗的測試案例
 */
export const getFailedCases = () => {
  return api.get('/api/benchmark/test-results/failed_cases/');
};

// ==================== Versions API ====================

/**
 * 獲取演算法版本列表
 */
export const getVersions = () => {
  return api.get('/api/benchmark/versions/');
};

/**
 * 獲取單個演算法版本
 * @param {number} id - 版本 ID
 */
export const getVersion = (id) => {
  return api.get(`/api/benchmark/versions/${id}/`);
};

/**
 * 創建演算法版本
 * @param {Object} data - 版本數據
 * @param {string} data.version_name - 版本名稱
 * @param {string} data.version_code - 版本代碼
 * @param {string} data.description - 描述
 * @param {Object} data.config_snapshot - 配置快照
 */
export const createVersion = (data) => {
  return api.post('/api/benchmark/versions/', data);
};

/**
 * 更新演算法版本
 * @param {number} id - 版本 ID
 * @param {Object} data - 更新數據
 */
export const updateVersion = (id, data) => {
  return api.put(`/api/benchmark/versions/${id}/`, data);
};

/**
 * 部分更新演算法版本
 * @param {number} id - 版本 ID
 * @param {Object} data - 更新數據
 */
export const patchVersion = (id, data) => {
  return api.patch(`/api/benchmark/versions/${id}/`, data);
};

/**
 * 刪除演算法版本
 * @param {number} id - 版本 ID
 */
export const deleteVersion = (id) => {
  return api.delete(`/api/benchmark/versions/${id}/`);
};

/**
 * 設定為基準版本
 * @param {number} id - 版本 ID
 */
export const setAsBaseline = (id) => {
  return api.post(`/api/benchmark/versions/${id}/set_as_baseline/`);
};

/**
 * 獲取版本的測試歷史
 * @param {number} id - 版本 ID
 */
export const getVersionTestHistory = (id) => {
  return api.get(`/api/benchmark/versions/${id}/test_history/`);
};

/**
 * 獲取當前基準版本
 */
export const getBaselineVersion = () => {
  return api.get('/api/benchmark/versions/baseline/');
};

// ==================== 匯出所有 API ====================

const benchmarkApi = {
  // Test Cases
  getTestCases,
  getTestCase,
  createTestCase,
  updateTestCase,
  patchTestCase,
  deleteTestCase,
  getTestCaseStatistics,
  bulkActivateTestCases,
  bulkDeactivateTestCases,

  // Test Runs
  getTestRuns,
  getTestRun,
  createTestRun,
  updateTestRun,
  deleteTestRun,
  getTestRunResults,
  startTest,
  stopTest,
  compareTestRuns,

  // Test Results
  getTestResults,
  getTestResult,
  getFailedCases,

  // Versions
  getVersions,
  getVersion,
  createVersion,
  updateVersion,
  patchVersion,
  deleteVersion,
  setAsBaseline,
  getVersionTestHistory,
  getBaselineVersion,
};

export default benchmarkApi;
