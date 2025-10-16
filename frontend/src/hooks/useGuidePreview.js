import { useState, useEffect } from 'react';
import { message } from 'antd';
import axios from 'axios';

/**
 * Guide 預覽 Hook
 * 
 * 用於載入和管理 Guide 詳細資料
 * 支持配置驅動，可用於任何知識庫系統
 * 
 * @param {string|number} guideId - Guide ID
 * @param {Object} config - 知識庫配置對象（來自 knowledgeBaseConfig.js）
 * @returns {Object} { guide, loading, error, refetch }
 * 
 * @example
 * import { knowledgeBaseConfigs } from '@/config/knowledgeBaseConfig';
 * import useGuidePreview from '@/hooks/useGuidePreview';
 * 
 * const config = knowledgeBaseConfigs['rvt-assistant'];
 * const { guide, loading, error, refetch } = useGuidePreview(id, config);
 */
const useGuidePreview = (guideId, config) => {
  const [guide, setGuide] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 驗證參數
  if (!config) {
    console.error('❌ useGuidePreview: config 參數為必需');
  }

  if (!config?.apiEndpoint) {
    console.error('❌ useGuidePreview: config.apiEndpoint 未定義');
  }

  /**
   * 載入 Guide 詳細資料
   */
  const fetchGuide = async () => {
    if (!guideId) {
      console.log('⏸️ useGuidePreview: guideId 未提供，跳過載入');
      setLoading(false);
      return;
    }

    if (!config?.apiEndpoint) {
      setError('配置錯誤：缺少 API endpoint');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const url = `${config.apiEndpoint}${guideId}/`;
      console.log(`📡 useGuidePreview: 正在載入 Guide，URL: ${url}`);

      const response = await axios.get(url, {
        withCredentials: true,
        timeout: 10000
      });

      console.log('✅ useGuidePreview: Guide 載入成功', {
        id: response.data.id,
        title: response.data.title,
        hasContent: !!response.data.content,
        contentLength: response.data.content?.length || 0
      });

      setGuide(response.data);
      setError(null);

    } catch (err) {
      console.error('❌ useGuidePreview: 載入 Guide 失敗', err);

      // 錯誤處理
      let errorMessage = '載入失敗';
      
      if (err.response) {
        // 服務器返回錯誤
        switch (err.response.status) {
          case 404:
            errorMessage = '找不到此文檔';
            break;
          case 403:
            errorMessage = '沒有權限查看此文檔';
            break;
          case 401:
            errorMessage = '請先登入';
            break;
          default:
            errorMessage = `載入失敗 (${err.response.status})`;
        }
      } else if (err.request) {
        // 請求發送但沒有收到響應
        errorMessage = '網絡連接失敗';
      } else {
        // 其他錯誤
        errorMessage = err.message || '未知錯誤';
      }

      setError(errorMessage);
      message.error(config.labels?.detailFailed || errorMessage);

    } finally {
      setLoading(false);
    }
  };

  // 當 guideId 或 config 變化時重新載入
  useEffect(() => {
    fetchGuide();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [guideId, config?.apiEndpoint]);

  /**
   * 手動重新載入
   */
  const refetch = () => {
    fetchGuide();
  };

  return {
    guide,        // Guide 資料對象
    loading,      // 載入狀態
    error,        // 錯誤訊息
    refetch       // 重新載入函數
  };
};

export default useGuidePreview;
