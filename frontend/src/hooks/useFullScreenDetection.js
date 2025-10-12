import { useState, useEffect, useCallback } from 'react';

/**
 * 全螢幕模式偵測 Hook
 * 支援多種瀏覽器的全螢幕 API 和 MdEditor 的全螢幕模式
 * 
 * @returns {Object} 全螢幕相關的狀態和方法
 */
const useFullScreenDetection = () => {
  const [isFullScreen, setIsFullScreen] = useState(false);

  /**
   * 檢測當前是否處於全螢幕模式
   * 支援標準 API 和 MdEditor 的 CSS 類別檢測
   */
  const checkFullScreenStatus = useCallback(() => {
    // 檢查瀏覽器原生全螢幕 API
    const nativeFullScreen = !!(
      document.fullscreenElement || 
      document.webkitFullscreenElement ||
      document.mozFullScreenElement ||
      document.msFullscreenElement
    );

    // 檢查 MdEditor 的全螢幕模式 CSS 類
    const mdEditorFullScreen = !!document.querySelector('.rc-md-editor.full');

    // 任一條件滿足即視為全螢幕模式
    const isFullScreenNow = nativeFullScreen || mdEditorFullScreen;

    return isFullScreenNow;
  }, []);

  /**
   * 處理全螢幕狀態變化
   */
  const handleFullScreenChange = useCallback(() => {
    const isFullScreenNow = checkFullScreenStatus();
    
    // 調試信息
    console.log('🔍 全螢幕狀態變化:', isFullScreenNow);
    console.log('📱 fullscreenElement:', document.fullscreenElement);
    console.log('🖥️ MdEditor full class:', document.querySelector('.rc-md-editor.full'));
    
    setIsFullScreen(isFullScreenNow);
  }, [checkFullScreenStatus]);

  /**
   * 進入全螢幕模式
   * @param {HTMLElement} element - 要全螢幕的元素，預設為 document.documentElement
   */
  const enterFullScreen = useCallback(async (element = document.documentElement) => {
    try {
      if (element.requestFullscreen) {
        await element.requestFullscreen();
      } else if (element.webkitRequestFullscreen) {
        await element.webkitRequestFullscreen();
      } else if (element.mozRequestFullScreen) {
        await element.mozRequestFullScreen();
      } else if (element.msRequestFullscreen) {
        await element.msRequestFullscreen();
      }
    } catch (error) {
      console.warn('進入全螢幕模式失敗:', error);
    }
  }, []);

  /**
   * 退出全螢幕模式
   */
  const exitFullScreen = useCallback(async () => {
    try {
      if (document.exitFullscreen) {
        await document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        await document.webkitExitFullscreen();
      } else if (document.mozCancelFullScreen) {
        await document.mozCancelFullScreen();
      } else if (document.msExitFullscreen) {
        await document.msExitFullscreen();
      }
    } catch (error) {
      console.warn('退出全螢幕模式失敗:', error);
    }
  }, []);

  /**
   * 切換全螢幕模式
   * @param {HTMLElement} element - 要全螢幕的元素
   */
  const toggleFullScreen = useCallback(async (element) => {
    if (isFullScreen) {
      await exitFullScreen();
    } else {
      await enterFullScreen(element);
    }
  }, [isFullScreen, enterFullScreen, exitFullScreen]);

  /**
   * 檢查瀏覽器是否支援全螢幕 API
   */
  const isFullScreenSupported = useCallback(() => {
    return !!(
      document.fullscreenEnabled ||
      document.webkitFullscreenEnabled ||
      document.mozFullScreenEnabled ||
      document.msFullscreenEnabled
    );
  }, []);

  // 設置事件監聽器
  useEffect(() => {
    // 瀏覽器原生全螢幕事件
    const fullScreenEvents = [
      'fullscreenchange',
      'webkitfullscreenchange', 
      'mozfullscreenchange',
      'MSFullscreenChange'
    ];

    // 添加事件監聽器
    fullScreenEvents.forEach(event => {
      document.addEventListener(event, handleFullScreenChange);
    });

    // 使用 MutationObserver 監聽 DOM 變化（用於 MdEditor 全螢幕模式）
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        // 監聽 class 屬性變化
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          // 檢查是否有 MdEditor 相關的全螢幕類別變化
          const target = mutation.target;
          if (target.classList && (
            target.classList.contains('rc-md-editor') ||
            target.closest('.rc-md-editor')
          )) {
            handleFullScreenChange();
          }
        }
      });
    });

    // 觀察整個文檔的 class 變化
    observer.observe(document.body, {
      attributes: true,
      subtree: true,
      attributeFilter: ['class']
    });

    // 初始檢查
    handleFullScreenChange();

    // 清理函數
    return () => {
      // 移除事件監聽器
      fullScreenEvents.forEach(event => {
        document.removeEventListener(event, handleFullScreenChange);
      });
      
      // 斷開 MutationObserver
      observer.disconnect();
    };
  }, [handleFullScreenChange]);

  return {
    // 狀態
    isFullScreen,
    isFullScreenSupported: isFullScreenSupported(),
    
    // 方法
    enterFullScreen,
    exitFullScreen,
    toggleFullScreen,
    checkFullScreenStatus,
    
    // 事件處理器 (如果需要手動觸發)
    handleFullScreenChange
  };
};

export default useFullScreenDetection;