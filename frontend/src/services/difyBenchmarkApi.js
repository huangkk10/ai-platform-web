/**
 * Dify Benchmark API Client
 * 
 * 封裝所有 Dify Benchmark 系統的 API 調用
 * 包含：Dify Config Versions、Dify Test Cases、Dify Test Runs
 */

import axios from 'axios';

// 確保所有請求都帶上認證憑證
const api = axios.create({
  withCredentials: true,
});

// ==================== Dify Config Versions API ====================

/**
 * 獲取 Dify 配置版本列表
 * @param {Object} params - 查詢參數
 * @param {boolean} params.is_active - 啟用狀態篩選
 */
export const getDifyVersions = (params = {}) => {
  return api.get('/api/dify-benchmark/versions/', { params });
};

/**
 * 獲取單個 Dify 配置版本
 * @param {number} id - 版本 ID
 */
export const getDifyVersion = (id) => {
  return api.get(`/api/dify-benchmark/versions/${id}/`);
};

/**
 * 創建 Dify 配置版本
 * @param {Object} data - 版本數據
 * @param {string} data.version_name - 版本名稱
 * @param {string} data.version_code - 版本代碼
 * @param {string} data.description - 描述
 * @param {string} data.dify_app_id - Dify App ID
 * @param {string} data.dify_api_key - Dify API Key
 * @param {string} data.dify_api_url - Dify API URL
 * @param {boolean} data.is_active - 是否啟用
 */
export const createDifyVersion = (data) => {
  return api.post('/api/dify-benchmark/versions/', data);
};

/**
 * 更新 Dify 配置版本
 * @param {number} id - 版本 ID
 * @param {Object} data - 更新數據
 */
export const updateDifyVersion = (id, data) => {
  return api.put(`/api/dify-benchmark/versions/${id}/`, data);
};

/**
 * 部分更新 Dify 配置版本
 * @param {number} id - 版本 ID
 * @param {Object} data - 更新數據
 */
export const patchDifyVersion = (id, data) => {
  return api.patch(`/api/dify-benchmark/versions/${id}/`, data);
};

/**
 * 刪除 Dify 配置版本
 * @param {number} id - 版本 ID
 */
export const deleteDifyVersion = (id) => {
  return api.delete(`/api/dify-benchmark/versions/${id}/`);
};

/**
 * 設定為基準版本
 * @param {number} id - 版本 ID
 */
export const setDifyBaseline = (id) => {
  return api.post(`/api/dify-benchmark/versions/${id}/set_baseline/`);
};

/**
 * 執行 Benchmark 測試
 * @param {number} id - 版本 ID
 * @param {Object} params - 測試參數
 * @param {Array<number>} params.test_case_ids - 測試案例 ID 列表（可選）
 * @param {boolean} params.force_retest - 是否強制重測（可選）
 */
export const runDifyBenchmark = (id, params = {}) => {
  return api.post(`/api/dify-benchmark/versions/${id}/run_benchmark/`, params);
};

/**
 * 獲取版本統計資訊
 * @param {number} id - 版本 ID
 */
export const getDifyVersionStatistics = (id) => {
  return api.get(`/api/dify-benchmark/versions/${id}/statistics/`);
};

/**
 * 批量測試多個 Dify 版本（支援多線程並行執行）
 * @param {Object} data - 批量測試配置
 * @param {Array<number>} data.version_ids - 版本 ID 列表（可選，null 表示所有版本）
 * @param {Array<number>} data.test_case_ids - 測試案例 ID 列表（可選，null 表示所有啟用案例）
 * @param {string} data.batch_name - 批次名稱（可選）
 * @param {string} data.notes - 備註（可選）
 * @param {boolean} data.force_retest - 是否強制重測（可選，預設 false）
 * @param {boolean} data.use_parallel - 是否並行執行（可選，預設 true）
 * @param {number} data.max_workers - 最大並行線程數（可選，預設 5）
 * 
 * 效能提升：
 * - 10 個測試：30 秒 → 6 秒（80% 提升）
 * - 50 個測試：150 秒 → 30 秒（80% 提升）
 */
export const batchTestDifyVersions = (data) => {
  // 設定預設值
  const requestData = {
    ...data,
    use_parallel: data.use_parallel !== undefined ? data.use_parallel : true,  // 預設啟用並行
    max_workers: data.max_workers || 5,  // 預設 5 個並行線程
  };
  
  return api.post('/api/dify-benchmark/versions/batch_test/', requestData);
};

// ==================== Dify Test Cases API ====================

/**
 * 獲取 Dify 測試案例列表
 * @param {Object} params - 查詢參數
 * @param {string} params.test_class_name - 測試類別篩選
 * @param {string} params.difficulty_level - 難度篩選
 * @param {string} params.question_type - 問題類型篩選
 * @param {boolean} params.is_active - 啟用狀態篩選
 * @param {string} params.search - 搜尋關鍵字
 */
export const getDifyTestCases = (params = {}) => {
  return api.get('/api/dify-benchmark/test-cases/', { params });
};

/**
 * 獲取單個 Dify 測試案例
 * @param {number} id - 測試案例 ID
 */
export const getDifyTestCase = (id) => {
  return api.get(`/api/dify-benchmark/test-cases/${id}/`);
};

/**
 * 創建 Dify 測試案例
 * @param {Object} data - 測試案例數據
 * @param {string} data.question - 問題
 * @param {string} data.test_class_name - 測試類別
 * @param {string} data.expected_answer - 預期答案
 * @param {Array<string>} data.answer_keywords - 答案關鍵字
 * @param {string} data.difficulty_level - 難度等級 (easy/medium/hard)
 * @param {string} data.question_type - 問題類型
 * @param {number} data.max_score - 最高分數
 * @param {string} data.evaluation_criteria - 評分標準
 * @param {boolean} data.is_active - 是否啟用
 */
export const createDifyTestCase = (data) => {
  return api.post('/api/dify-benchmark/test-cases/', data);
};

/**
 * 更新 Dify 測試案例
 * @param {number} id - 測試案例 ID
 * @param {Object} data - 更新數據
 */
export const updateDifyTestCase = (id, data) => {
  return api.put(`/api/dify-benchmark/test-cases/${id}/`, data);
};

/**
 * 部分更新 Dify 測試案例
 * @param {number} id - 測試案例 ID
 * @param {Object} data - 更新數據
 */
export const patchDifyTestCase = (id, data) => {
  return api.patch(`/api/dify-benchmark/test-cases/${id}/`, data);
};

/**
 * 刪除 Dify 測試案例
 * @param {number} id - 測試案例 ID
 */
export const deleteDifyTestCase = (id) => {
  return api.delete(`/api/dify-benchmark/test-cases/${id}/`);
};

/**
 * 批量導入 Dify 測試案例
 * @param {Object} data - 導入數據
 * @param {Array<Object>} data.test_cases - 測試案例列表
 * @param {string} data.format - 格式 (json/csv)
 * @param {boolean} data.overwrite_existing - 是否覆蓋現有案例
 */
export const bulkImportDifyTestCases = (data) => {
  return api.post('/api/dify-benchmark/test-cases/bulk_import/', data);
};

/**
 * 批量導出 Dify 測試案例
 * @param {Object} params - 查詢參數
 * @param {string} params.format - 格式 (json/csv)
 * @param {boolean} params.is_active - 是否只導出啟用的案例
 */
export const bulkExportDifyTestCases = (params = {}) => {
  return api.get('/api/dify-benchmark/test-cases/bulk_export/', { 
    params,
    responseType: 'blob'  // 用於下載檔案
  });
};

/**
 * 切換測試案例啟用狀態
 * @param {number} id - 測試案例 ID
 */
export const toggleDifyTestCase = (id) => {
  return api.patch(`/api/dify-benchmark/test-cases/${id}/toggle_active/`);
};

// ==================== Dify Test Runs API ====================

/**
 * 獲取 Dify 測試執行列表
 * @param {Object} params - 查詢參數
 * @param {number} params.config_version_id - 配置版本 ID 篩選
 * @param {string} params.batch_id - 批次 ID 篩選
 * @param {string} params.status - 狀態篩選
 * @param {number} params.days - 時間範圍篩選（天數）
 */
export const getDifyTestRuns = (params = {}) => {
  return api.get('/api/dify-benchmark/test-runs/', { params });
};

/**
 * 獲取單個 Dify 測試執行
 * @param {number} id - 測試執行 ID
 */
export const getDifyTestRun = (id) => {
  return api.get(`/api/dify-benchmark/test-runs/${id}/`);
};

/**
 * 創建 Dify 測試執行
 * @param {Object} data - 測試執行數據
 * @param {number} data.config_version_id - 配置版本 ID
 * @param {string} data.run_name - 執行名稱
 * @param {string} data.batch_id - 批次 ID（可選）
 * @param {string} data.notes - 備註（可選）
 */
export const createDifyTestRun = (data) => {
  return api.post('/api/dify-benchmark/test-runs/', data);
};

/**
 * 更新 Dify 測試執行
 * @param {number} id - 測試執行 ID
 * @param {Object} data - 更新數據
 */
export const updateDifyTestRun = (id, data) => {
  return api.put(`/api/dify-benchmark/test-runs/${id}/`, data);
};

/**
 * 刪除 Dify 測試執行
 * @param {number} id - 測試執行 ID
 */
export const deleteDifyTestRun = (id) => {
  return api.delete(`/api/dify-benchmark/test-runs/${id}/`);
};

/**
 * 獲取測試執行的所有結果
 * @param {number} id - 測試執行 ID
 */
export const getDifyTestRunResults = (id) => {
  return api.get(`/api/dify-benchmark/test-runs/${id}/results/`);
};

/**
 * 批量對比測試執行
 * @param {Object} data - 對比配置
 * @param {Array<number>} data.test_run_ids - 測試執行 ID 列表
 */
export const compareDifyTestRuns = (data) => {
  return api.post('/api/dify-benchmark/test-runs/comparison/', data);
};

/**
 * 獲取批次歷史
 * @param {string} batchId - 批次 ID
 */
export const getDifyBatchHistory = (batchId) => {
  return api.get(`/api/dify-benchmark/test-runs/batch_history/`, {
    params: { batch_id: batchId }
  });
};

// ==================== 匯出所有 API ====================

const difyBenchmarkApi = {
  // Dify Config Versions
  getDifyVersions,
  getDifyVersion,
  createDifyVersion,
  updateDifyVersion,
  patchDifyVersion,
  deleteDifyVersion,
  setDifyBaseline,
  runDifyBenchmark,
  getDifyVersionStatistics,
  batchTestDifyVersions,

  // Dify Test Cases
  getDifyTestCases,
  getDifyTestCase,
  createDifyTestCase,
  updateDifyTestCase,
  patchDifyTestCase,
  deleteDifyTestCase,
  bulkImportDifyTestCases,
  bulkExportDifyTestCases,
  toggleDifyTestCase,

  // Dify Test Runs
  getDifyTestRuns,
  getDifyTestRun,
  createDifyTestRun,
  updateDifyTestRun,
  deleteDifyTestRun,
  getDifyTestRunResults,
  compareDifyTestRuns,
  getDifyBatchHistory,
};

export default difyBenchmarkApi;
