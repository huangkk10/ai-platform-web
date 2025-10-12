import { useState, useCallback } from 'react';
import { message } from 'antd';

/**
 * Markdown 編輯器游標管理 Hook
 * 處理游標位置追蹤、保存、恢復和圖片插入功能
 * 
 * @param {Object} editorRef - MdEditor 的 ref 對象
 * @param {Object} formData - 表單數據對象 {title, content}
 * @param {Function} setFormData - 更新表單數據的函數
 * @returns {Object} 游標管理相關的狀態和方法
 */
const useMarkdownCursor = (editorRef, formData, setFormData) => {
  const [cursorPosition, setCursorPosition] = useState(0);

  /**
   * 處理編輯器游標位置變更
   * 支援點擊、按鍵、選擇、滑鼠事件
   */
  const handleEditorCursorChange = useCallback((event) => {
    if (editorRef.current) {
      try {
        const editor = editorRef.current;
        const textArea = editor.nodeMdText?.current;
        
        if (textArea) {
          const newPosition = textArea.selectionStart || 0;
          setCursorPosition(newPosition);
          
          // 儲存到 localStorage 以便在失去焦點時保持
          localStorage.setItem('markdown-editor-cursor-position', newPosition.toString());
          
          console.log('🎯 游標位置更新:', newPosition);
        }
      } catch (error) {
        console.warn('無法獲取游標位置:', error);
      }
    }
  }, [editorRef]);

  /**
   * 當編輯器失去焦點時保存游標位置
   */
  const handleEditorBlur = useCallback(() => {
    if (editorRef.current) {
      try {
        const editor = editorRef.current;
        const textArea = editor.nodeMdText?.current;
        
        if (textArea) {
          const position = textArea.selectionStart || 0;
          setCursorPosition(position);
          localStorage.setItem('markdown-editor-cursor-position', position.toString());
          console.log('💾 編輯器失去焦點，保存游標位置:', position);
        }
      } catch (error) {
        console.warn('保存游標位置失敗:', error);
      }
    }
  }, [editorRef]);

  /**
   * 當編輯器重新獲得焦點時恢復游標位置
   */
  const handleEditorFocus = useCallback(() => {
    setTimeout(() => {
      if (editorRef.current) {
        try {
          const editor = editorRef.current;
          const textArea = editor.nodeMdText?.current;
          
          if (textArea) {
            const savedPosition = localStorage.getItem('markdown-editor-cursor-position');
            if (savedPosition) {
              const position = parseInt(savedPosition, 10);
              textArea.setSelectionRange(position, position);
              setCursorPosition(position);
              console.log('🎯 恢復游標位置:', position);
            }
          }
        } catch (error) {
          console.warn('恢復游標位置失敗:', error);
        }
      }
    }, 50); // 短暫延遲確保編輯器完全聚焦
  }, [editorRef]);

  /**
   * 在指定游標位置插入圖片資訊
   * @param {string} imageInfo - 要插入的圖片 Markdown 語法
   */
  const insertImageAtCursor = useCallback((imageInfo) => {
    const currentContent = formData.content || '';
    const beforeCursor = currentContent.slice(0, cursorPosition);
    const afterCursor = currentContent.slice(cursorPosition);
    
    // 插入圖片資訊
    const newContent = beforeCursor + imageInfo + afterCursor;
    
    // 更新內容
    setFormData(prev => ({
      ...prev,
      content: newContent
    }));
    
    // 更新編輯器內容
    if (editorRef.current) {
      editorRef.current.setText(newContent);
    }
    
    // 更新游標位置到插入內容之後
    const newCursorPos = cursorPosition + imageInfo.length;
    setCursorPosition(newCursorPos);
    
    // 更新 localStorage 中的游標位置
    localStorage.setItem('markdown-editor-cursor-position', newCursorPos.toString());
    
    message.success('圖片已插入到編輯器中');
    
    console.log('📷 圖片已插入，新游標位置:', newCursorPos);
  }, [formData.content, cursorPosition, editorRef, setFormData]);

  /**
   * 清除本地存儲的游標位置
   */
  const clearSavedCursorPosition = useCallback(() => {
    localStorage.removeItem('markdown-editor-cursor-position');
    console.log('🗑️ 已清除保存的游標位置');
  }, []);

  /**
   * 獲取當前游標位置
   * @returns {number} 當前游標位置
   */
  const getCurrentCursorPosition = useCallback(() => {
    if (editorRef.current) {
      try {
        const editor = editorRef.current;
        const textArea = editor.nodeMdText?.current;
        
        if (textArea) {
          return textArea.selectionStart || 0;
        }
      } catch (error) {
        console.warn('無法獲取當前游標位置:', error);
      }
    }
    return cursorPosition;
  }, [editorRef, cursorPosition]);

  /**
   * 設置游標到指定位置
   * @param {number} position - 目標位置
   */
  const setCursorToPosition = useCallback((position) => {
    if (editorRef.current) {
      try {
        const editor = editorRef.current;
        const textArea = editor.nodeMdText?.current;
        
        if (textArea) {
          textArea.setSelectionRange(position, position);
          setCursorPosition(position);
          localStorage.setItem('markdown-editor-cursor-position', position.toString());
          console.log('🎯 游標已設置到位置:', position);
        }
      } catch (error) {
        console.warn('設置游標位置失敗:', error);
      }
    }
  }, [editorRef]);

  return {
    // 狀態
    cursorPosition,
    
    // 事件處理器 (用於 MdEditor 組件)
    handleEditorCursorChange,
    handleEditorBlur,
    handleEditorFocus,
    
    // 功能方法
    insertImageAtCursor,
    clearSavedCursorPosition,
    getCurrentCursorPosition,
    setCursorToPosition
  };
};

export default useMarkdownCursor;