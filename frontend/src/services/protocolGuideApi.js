/**
 * Protocol Guide API Client
 * 
 * 封裝所有 Protocol Guide 相關的 API 調用
 * 包含：Dify Config Versions（Protocol Guide 專用）、Baseline 管理
 */

import axios from 'axios';

// 確保所有請求都帶上認證憑證和 CSRF Token
const api = axios.create({
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
});

// ==================== Dify Config Versions API (Protocol Guide) ====================

/**
 * 獲取 Dify 配置版本列表
 * @param {Object} params - 查詢參數
 * @param {boolean} params.is_active - 啟用狀態篩選
 */
export const getProtocolVersions = (params = {}) => {
  return api.get('/api/dify/versions/', { params });
};

/**
 * 獲取單個 Dify 配置版本
 * @param {number} id - 版本 ID
 */
export const getProtocolVersion = (id) => {
  return api.get(`/api/dify/versions/${id}/`);
};

/**
 * 創建 Dify 配置版本
 * @param {Object} data - 版本資料
 */
export const createProtocolVersion = (data) => {
  return api.post('/api/dify/versions/', data);
};

/**
 * 更新 Dify 配置版本
 * @param {number} id - 版本 ID
 * @param {Object} data - 更新資料
 */
export const updateProtocolVersion = (id, data) => {
  return api.put(`/api/dify/versions/${id}/`, data);
};

/**
 * 刪除 Dify 配置版本
 * @param {number} id - 版本 ID
 */
export const deleteProtocolVersion = (id) => {
  return api.delete(`/api/dify/versions/${id}/`);
};

// ==================== Baseline 管理 API ====================

/**
 * 設定為 Baseline 版本
 * @param {number} id - 版本 ID
 * @returns {Promise} - 包含設定結果的 Promise
 */
export const setProtocolBaseline = (id) => {
  return api.post(`/api/dify/versions/${id}/set_baseline/`);
};

/**
 * 獲取當前 Baseline 版本
 * @returns {Promise} - 包含 Baseline 版本資訊的 Promise
 */
export const getProtocolBaseline = () => {
  return api.get('/api/dify/versions/baseline/');
};

// ==================== 匯出所有 API ====================

export default {
  // Dify Config Versions
  getProtocolVersions,
  getProtocolVersion,
  createProtocolVersion,
  updateProtocolVersion,
  deleteProtocolVersion,
  
  // Baseline 管理
  setProtocolBaseline,
  getProtocolBaseline,
};
