/**
 * 日誌查看器自訂 Hook
 * 
 * 提供日誌查看相關的狀態管理和操作邏輯
 */

import { useState, useEffect, useCallback } from 'react';
import logService from '../services/logService';
import { message } from 'antd';

export const useLogViewer = (initialFilename = null) => {
  // 狀態管理
  const [logFiles, setLogFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(initialFilename);
  const [logContent, setLogContent] = useState([]);
  const [logStats, setLogStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filesLoading, setFilesLoading] = useState(false);
  const [filters, setFilters] = useState({
    level: null,
    search: '',
    lines: 500,  // 預設顯示 500 行
  });

  // 載入日誌檔案列表
  const loadLogFiles = useCallback(async () => {
    setFilesLoading(true);
    try {
      const data = await logService.listLogFiles();
      setLogFiles(data.log_files || []);
      
      // 如果沒有選中檔案，選中第一個
      if (!selectedFile && data.log_files && data.log_files.length > 0) {
        setSelectedFile(data.log_files[0].name);
      }
    } catch (error) {
      message.error('載入日誌檔案列表失敗: ' + (error.response?.data?.error || error.message));
    } finally {
      setFilesLoading(false);
    }
  }, [selectedFile]);

  // 載入日誌內容
  const loadLogContent = useCallback(async () => {
    if (!selectedFile) return;

    setLoading(true);
    try {
      const data = await logService.viewLogFile(selectedFile, {
        lines: filters.lines,
        level: filters.level,
        search: filters.search,
        startDate: filters.dateRange?.[0],
        endDate: filters.dateRange?.[1]
      });

      setLogContent(data.content || []);
    } catch (error) {
      message.error('載入日誌內容失敗: ' + (error.response?.data?.error || error.message));
      setLogContent([]);
    } finally {
      setLoading(false);
    }
  }, [selectedFile, filters]);

  // 載入統計資訊
  const loadLogStats = useCallback(async () => {
    if (!selectedFile) return;

    try {
      const data = await logService.getLogStats(selectedFile);
      setLogStats(data.stats || null);
    } catch (error) {
      console.error('載入統計失敗:', error);
      setLogStats(null);
    }
  }, [selectedFile]);

  // 切換檔案
  const handleFileSelect = useCallback((filename) => {
    setSelectedFile(filename);
    setFilters({
      lines: 500,  // 切換檔案時也使用 500 行
      level: null,
      search: null,
      dateRange: null
    });
  }, []);

  // 更新過濾器
  const updateFilters = useCallback((newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  // 重新整理
  const refresh = useCallback(() => {
    loadLogContent();
    loadLogStats();
  }, [loadLogContent, loadLogStats]);

  // 下載日誌
  const downloadLog = useCallback(async (format = 'txt') => {
    if (!selectedFile) return;

    try {
      await logService.downloadLogFile(selectedFile, format);
      message.success('日誌下載成功');
    } catch (error) {
      message.error('下載失敗: ' + (error.response?.data?.error || error.message));
    }
  }, [selectedFile]);

  // 搜尋日誌
  const searchLogs = useCallback(async (searchQuery) => {
    if (!selectedFile || !searchQuery) return;

    setLoading(true);
    try {
      const data = await logService.searchLogFile(selectedFile, searchQuery);
      setLogContent(data.results || []);
      message.success(`找到 ${data.total_matches} 筆匹配結果`);
    } catch (error) {
      message.error('搜尋失敗: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  }, [selectedFile]);

  // 初始載入
  useEffect(() => {
    loadLogFiles();
  }, [loadLogFiles]);

  // 當選中檔案或過濾器改變時，重新載入內容
  useEffect(() => {
    if (selectedFile) {
      loadLogContent();
      loadLogStats();
    }
  }, [selectedFile, filters, loadLogContent, loadLogStats]);

  return {
    // 狀態
    logFiles,
    selectedFile,
    logContent,
    logStats,
    loading,
    filesLoading,
    filters,

    // 操作
    handleFileSelect,
    updateFilters,
    refresh,
    downloadLog,
    searchLogs,
  };
};

export default useLogViewer;
