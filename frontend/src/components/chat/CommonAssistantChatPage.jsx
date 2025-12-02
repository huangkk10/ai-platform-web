/**
 * 通用 Assistant 聊天頁面組件
 * =============================
 * 
 * 用途：所有 Assistant (RVT, Protocol, QA 等) 的統一聊天介面
 * 優點：
 * - 統一的 UI 和 UX
 * - 集中維護，修改一處即可影響所有 Assistant
 * - 新增 Assistant 只需配置，無需重寫頁面
 * 
 * 使用範例：
 * ```jsx
 * <CommonAssistantChatPage
 *   assistantType="rvt"
 *   assistantName="RVT Assistant"
 *   useChatHook={useRvtChat}
 *   configApiPath="/api/rvt-guide/config/"
 *   storageKey="rvt"
 *   permissionKey="webRvtAssistant"
 *   placeholder="請描述你的 RVT 問題..."
 *   collapsed={collapsed}
 *   enableFileUpload={true}  // 🆕 啟用檔案上傳功能
 * />
 * ```
 */

import React, { useState, useRef, useEffect } from 'react';
import { Layout, Input, message } from 'antd';
import { SendOutlined, MinusSquareFilled } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useChatContext } from '../../contexts/ChatContext';
import { useAuth } from '../../contexts/AuthContext';
import MessageList from './MessageList';
import useMessageStorage from '../../hooks/useMessageStorage';
import useMessageFeedback from '../../hooks/useMessageFeedback';
// 🆕 檔案上傳相關
import useFileUpload, { MAX_TEXT_CONTENT_LENGTH, RECOMMENDED_CONTENT_LENGTH } from '../../hooks/useFileUpload';
import FileUploadButton from './FileUploadButton';
import FilePreviewInline from './FilePreviewInline';  // 🎨 使用內聯預覽版本
import { analyzeImageOCR } from '../../services/ocrService';  // 🆕 直接導入 OCR 服務

const { Content } = Layout;
const { TextArea } = Input;

const CommonAssistantChatPage = ({
  assistantType,
  assistantName,
  storageKey,
  useChatHook,
  configApiPath,
  permissionKey,
  placeholder,
  welcomeMessage,
  collapsed = false,
  enableFileUpload = false  // 🆕 是否啟用檔案上傳功能
}) => {
  const { user, permissions } = useAuth();
  // eslint-disable-next-line no-unused-vars
  const navigate = useNavigate();  // 保留以備未來使用
  const { registerClearFunction, clearClearFunction } = useChatContext();
  
  const {
    messages,
    conversationId,
    currentUserId,
    setMessages,
    setConversationId,
    clearChat,
    checkUserSwitch,
    handleUserSwitch
  } = useMessageStorage(user, storageKey, welcomeMessage);
  
  const [inputMessage, setInputMessage] = useState('');
  const [assistantConfig, setAssistantConfig] = useState(null);
  const [textareaRows, setTextareaRows] = useState(1); // 🎯 方案 B：控制 TextArea 行數
  const messagesEndRef = useRef(null);
  
  // 🆕 檔案上傳 Hook（必須無條件調用，但根據 enableFileUpload 決定是否使用）
  const fileUploadHook = useFileUpload();
  // 只在啟用時才使用 hook 的返回值
  const fileUpload = enableFileUpload ? fileUploadHook : null;
  
  // 使用傳入的 Chat Hook
  const chatHookReturn = useChatHook(
    conversationId,
    setConversationId,
    setMessages,
    user,
    currentUserId
  );
  
  const { 
    sendMessage, 
    loading, 
    loadingStartTime, 
    stopRequest,
    // 🆕 取得 loading 控制函數（供 OCR 前置處理使用）
    setLoading,
    setLoadingStartTime
  } = chatHookReturn;
  
  const { feedbackStates, submitFeedback } = useMessageFeedback();
  
  // 權限檢查函數
  const hasPermission = (key) => {
    return permissions[key] === true;
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 載入 Assistant 配置
  useEffect(() => {
    loadAssistantConfig();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadAssistantConfig = async () => {
    try {
      const response = await fetch(configApiPath, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setAssistantConfig(data.config);
        }
      }
    } catch (error) {
      console.error(`載入 ${assistantName} 配置失敗:`, error);
    }
  };

  // 🆕 輔助函數：將檔案轉換為 base64 URL（供訊息顯示用）
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject(new Error('讀取檔案失敗'));
      reader.readAsDataURL(file);
    });
  };

  const handleSendMessage = async () => {
    console.log('🎬 [CommonAssistantChatPage] handleSendMessage 開始執行');
    console.log('  - inputMessage:', inputMessage);
    console.log('  - assistantType:', assistantType);
    console.log('  - enableFileUpload:', enableFileUpload);
    console.log('  - hasFile:', fileUpload?.hasFile);
    
    // 檢查是否有訊息或待處理的檔案可發送
    const hasTextContent = inputMessage.trim().length > 0;
    const hasPendingFile = enableFileUpload && fileUpload?.hasFile;
    
    if (!hasTextContent && !hasPendingFile) {
      console.log('⚠️ [CommonAssistantChatPage] 沒有訊息或檔案，返回');
      return;
    }

    const sendTimeUserId = user?.id || null;
    if (checkUserSwitch(sendTimeUserId)) {
      handleUserSwitch(sendTimeUserId);
      message.warning('偵測到用戶切換，請重新發送您的消息。');
      return;
    }

    // ========== 步驟 1：保存檔案資訊並轉換為 base64（供 UI 顯示）==========
    let fileToProcess = null;
    let imageBase64 = null;
    
    if (enableFileUpload && fileUpload?.hasFile) {
      // 保存檔案引用
      fileToProcess = {
        file: fileUpload.uploadedFile,
        isImage: fileUpload.isImage,
        fileName: fileUpload.uploadedFile?.name
      };
      console.log('📎 [CommonAssistantChatPage] 保存檔案引用:', fileToProcess.fileName);
      
      // 🖼️ 如果是圖片，轉換為 base64 供訊息顯示
      if (fileToProcess.isImage) {
        try {
          imageBase64 = await fileToBase64(fileToProcess.file);
          console.log('🖼️ [CommonAssistantChatPage] 圖片已轉換為 base64，長度:', imageBase64?.length);
        } catch (err) {
          console.warn('⚠️ [CommonAssistantChatPage] 圖片 base64 轉換失敗:', err);
        }
      }
      
      // 立即清除輸入框預覽
      fileUpload.clearFile();
    }

    // ========== 步驟 2：立即顯示用戶訊息（含圖片）並清空輸入框 ==========
    const userMessageText = inputMessage.trim();
    const fileAttachment = fileToProcess ? {
      fileName: fileToProcess.fileName,
      fileType: fileToProcess.isImage ? 'image' : 'text',
      isImage: fileToProcess.isImage,
      imageUrl: imageBase64  // 🖼️ 圖片 base64 URL
    } : null;
    
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: userMessageText || (fileAttachment ? `[已上傳檔案: ${fileAttachment.fileName}]` : ''),
      timestamp: new Date(),
      attachment: fileAttachment
    };

    console.log('📨 [CommonAssistantChatPage] 立即顯示 userMessage:', userMessage);
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setTextareaRows(1);

    // 🆕 步驟 2.5：如果有檔案要處理，立即啟動 loading 動畫（在 OCR 處理前就顯示）
    // 如果沒有檔案，讓 sendMessage() 自己控制 loading
    const needPreLoading = fileToProcess && setLoading && setLoadingStartTime;
    if (needPreLoading) {
      console.log('⏳ [CommonAssistantChatPage] 啟動 loading 動畫（OCR 前置處理）');
      setLoading(true);
      setLoadingStartTime(Date.now());
    }

    // ========== 步驟 3：處理 OCR（此時用戶已看到訊息 + loading 動畫）==========
    let finalMessage = userMessageText;
    let fileContextString = null;
    
    if (fileToProcess) {
      console.log('📎 [CommonAssistantChatPage] 開始處理檔案 OCR...');
      
      try {
        let ocrText = '';
        
        if (fileToProcess.isImage) {
          // 🔧 圖片：直接呼叫 OCR API
          console.log('📷 [CommonAssistantChatPage] 呼叫 OCR API...');
          const ocrResult = await analyzeImageOCR(fileToProcess.file);
          console.log('📋 [CommonAssistantChatPage] OCR 結果:', ocrResult);
          
          if (ocrResult.success) {
            ocrText = ocrResult.text;
            console.log('✅ [CommonAssistantChatPage] OCR 成功，文字長度:', ocrText?.length);
          } else {
            throw new Error(ocrResult.error || 'OCR 辨識失敗');
          }
        } else {
          // 文字檔：直接讀取
          console.log('📄 [CommonAssistantChatPage] 讀取文字檔...');
          ocrText = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = () => reject(new Error('讀取檔案失敗'));
            reader.readAsText(fileToProcess.file);
          });
          console.log('✅ [CommonAssistantChatPage] 讀取成功，文字長度:', ocrText?.length);
          
          // 🔧 2025-12-02：新增內容長度檢查，防止大檔案導致系統問題
          if (ocrText.length > MAX_TEXT_CONTENT_LENGTH) {
            const fileSizeKB = (ocrText.length / 1000).toFixed(0);
            message.error(`檔案內容過大（${fileSizeKB}K 字元），最大支援 ${MAX_TEXT_CONTENT_LENGTH / 1000}K 字元。建議上傳較小的檔案或擷取關鍵內容。`);
            console.warn(`⚠️ [CommonAssistantChatPage] 檔案內容過大: ${ocrText.length} > ${MAX_TEXT_CONTENT_LENGTH}`);
            // 清除 loading 狀態並中止處理
            if (setLoading) setLoading(false);
            if (setLoadingStartTime) setLoadingStartTime(null);
            return;
          }
          
          // 超過建議值顯示警告（但仍允許繼續）
          if (ocrText.length > RECOMMENDED_CONTENT_LENGTH) {
            const fileSizeKB = (ocrText.length / 1000).toFixed(0);
            message.warning(`檔案內容較大（${fileSizeKB}K 字元），處理可能需要較長時間。`);
            console.log(`⚠️ [CommonAssistantChatPage] 檔案內容較大: ${ocrText.length} > ${RECOMMENDED_CONTENT_LENGTH}`);
          }
        }
        
        // 組合檔案內容（改進 prompt 格式，讓 AI 知道要分析而非展示）
        const prefix = fileToProcess.isImage 
          ? `【用戶上傳了一張圖片，以下是 OCR 辨識出的文字內容，請根據這些內容回答用戶的問題】\n`
          : `【用戶上傳了文字檔 ${fileToProcess.fileName}，以下是檔案內容，請根據這些內容回答用戶的問題】\n`;
        
        fileContextString = `${prefix}---\n${ocrText}\n---\n\n用戶問題：`;
        console.log('✅ [CommonAssistantChatPage] 檔案內容組合完成');
        
      } catch (err) {
        console.error('❌ [CommonAssistantChatPage] 檔案處理失敗:', err);
        message.error(`檔案處理失敗: ${err.message}`);
        // 即使 OCR 失敗，也繼續發送原始訊息
      }
    }
    
    // ========== 步驟 4：組合最終訊息並發送到 AI ==========
    if (fileContextString) {
      console.log('📎 [CommonAssistantChatPage] 附加檔案內容到訊息');
      // 格式：[OCR 內容] + 用戶問題：[用戶輸入]
      // 這樣 AI 知道要根據 OCR 內容回答問題，而不是展示 OCR 內容
      if (finalMessage) {
        finalMessage = `${fileContextString}${finalMessage}`;
      } else {
        // 如果用戶沒有輸入問題，根據檔案類型動態調整預設問題
        const defaultQuestion = fileToProcess?.isImage 
          ? '請說明這張圖片的內容'
          : `請說明這個檔案的內容`;
        finalMessage = `${fileContextString}${defaultQuestion}`;
      }
    }
    
    console.log('📨 [CommonAssistantChatPage] 最終訊息長度:', finalMessage.length);
    console.log('🔗 [CommonAssistantChatPage] 調用 sendMessage');
    
    try {
      await sendMessage({ ...userMessage, content: finalMessage });
      console.log('✅ [CommonAssistantChatPage] sendMessage 執行完成');
    } catch (error) {
      console.error('❌ [CommonAssistantChatPage] sendMessage 執行錯誤:', error);
    }
  };

  // 🎯 方案 B：處理輸入變化，只在實際換行時才調整高度
  const handleInputChange = (e) => {
    const text = e.target.value;
    
    // 計算實際的換行符數量（只計算 \n，不考慮自動 word-wrap）
    const actualLineBreaks = (text.match(/\n/g) || []).length;
    const calculatedRows = Math.min(actualLineBreaks + 1, 12); // 最多 12 行
    
    // 只在實際行數改變時才更新（避免不必要的 re-render）
    if (calculatedRows !== textareaRows) {
      setTextareaRows(calculatedRows);
      console.log('📏 [CommonAssistantChatPage] TextArea 行數調整:', textareaRows, '→', calculatedRows);
    }
    
    setInputMessage(text);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 🆕 處理剪貼簿貼上事件（支援截圖直接貼上）
  const handlePaste = (e) => {
    // 檢查是否啟用檔案上傳功能
    if (!enableFileUpload || !fileUpload) return;
    
    // 檢查剪貼簿內容
    const clipboardItems = e.clipboardData?.items;
    if (!clipboardItems) return;
    
    // 遍歷剪貼簿項目，尋找圖片
    for (const item of clipboardItems) {
      if (item.type.startsWith('image/')) {
        e.preventDefault();  // 阻止預設貼上行為
        
        // 轉換為 File 對象
        const file = item.getAsFile();
        if (!file) {
          console.warn('⚠️ [CommonAssistantChatPage] 無法從剪貼簿獲取圖片檔案');
          return;
        }
        
        // 檢查是否已有檔案
        if (fileUpload.hasFile) {
          message.warning('已有檔案待處理，請先清除或發送後再貼上新圖片');
          return;
        }
        
        // 使用現有的檔案處理函數
        console.log('📋 [CommonAssistantChatPage] 從剪貼簿貼上圖片:', file.type, file.size);
        fileUpload.handleFileSelect(file);
        message.success('截圖已貼上，可輸入問題後發送');
        
        return;  // 處理完圖片後返回
      }
    }
    // 如果沒有圖片，讓預設行為（貼上文字）繼續
  };

  useEffect(() => {
    registerClearFunction(clearChat);
    return () => clearClearFunction();
  }, [registerClearFunction, clearClearFunction, clearChat]);

  // 權限檢查（如果 permissionKey 為 null，則跳過權限檢查，允許訪客使用）
  if (permissionKey && !hasPermission(permissionKey)) {
    return (
      <Layout style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <h2>⚠️ 權限不足</h2>
          <p>您沒有使用 {assistantName} 的權限，請聯絡管理員。</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout style={{ height: '100vh', background: '#f5f5f5' }} className={`chat-page ${assistantType}-assistant-chat-page`}>
      <Content style={{ display: 'flex', flexDirection: 'column', padding: '0', height: '100%', paddingTop: '64px' }}>
        <MessageList
          messages={messages}
          loading={loading}
          loadingStartTime={loadingStartTime}
          feedbackStates={feedbackStates}
          onFeedback={submitFeedback}
          messagesEndRef={messagesEndRef}
          assistantName={assistantName}
        />
        <div className="input-area" style={{
          position: 'fixed',
          bottom: 0,
          left: collapsed ? 80 : 300,
          right: 0,
          transition: 'left 0.2s',
          zIndex: 10,
          background: 'white',
          borderTop: '1px solid #e8e8e8',
          padding: '16px 24px',
          boxShadow: '0 -2px 8px rgba(0, 0, 0, 0.06)'
        }}>
          {/* � 檔案預覽已移到輸入框內部（參考 Web AI OCR） */}
          
          <div className="input-container" style={{
            display: 'flex',
            alignItems: 'flex-end',
            gap: '8px',
            maxWidth: '800px',
            margin: '0 auto'
          }}>
            {/* � 參考 Web AI OCR 的 input-with-buttons 結構：按鈕在輸入框內部 */}
            <div className="input-with-buttons" style={{
              flex: 1,
              position: 'relative',
              display: 'flex',
              alignItems: 'flex-start',
              border: '1px solid #d9d9d9',
              borderRadius: '20px',
              background: 'white',
              transition: 'all 0.3s',
              padding: '8px',
              flexWrap: 'wrap',
              gap: '8px'
            }}>
              {/* �🆕 檔案上傳按鈕（在輸入框內部左側） */}
              {enableFileUpload && (
                <FileUploadButton
                  onFileSelect={fileUpload?.handleFileSelect}
                  disabled={loading || fileUpload?.isProcessing}
                  isProcessing={fileUpload?.isProcessing}
                  hasFile={fileUpload?.hasFile}
                />
              )}
              
              {/* 🆕 檔案預覽區（在輸入框內部，按鈕右側） */}
              {enableFileUpload && fileUpload?.hasFile && (
                <div className="file-preview-inline" style={{
                  display: 'flex',
                  gap: '6px',
                  alignItems: 'center'
                }}>
                  <FilePreviewInline
                    file={fileUpload.uploadedFile}
                    fileContent={fileUpload.fileContent}
                    isProcessing={fileUpload.isProcessing}
                    isProcessed={fileUpload.isProcessed}
                    onRemove={fileUpload.clearFile}
                  />
                </div>
              )}
              
              <TextArea
                value={inputMessage}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                onPaste={handlePaste}
                placeholder={`${placeholder} (按 Enter 發送，Shift + Enter 換行${assistantConfig ? ` • ${assistantConfig.app_name}` : ''}${enableFileUpload ? ' • 可直接貼上截圖' : ''})`}
                rows={textareaRows}
                disabled={loading}
                className="chat-input-area textarea-with-button"
                style={{ 
                  flex: 1,
                  border: 'none',
                  outline: 'none',
                  resize: 'none',
                  padding: '4px 8px',
                  fontSize: '14px',
                  lineHeight: '1.5',
                  background: 'transparent',
                  minHeight: '24px'
                }}
              />
            </div>
            
            <button
              onClick={() => {
                console.log('🖱️ [CommonAssistantChatPage] 發送按鈕被點擊');
                console.log('  - loading:', loading);
                console.log('  - inputMessage:', inputMessage);
                console.log('  - hasFile:', fileUpload?.hasFile);  // 🔧 改為檢查 hasFile
                if (loading) {
                  console.log('  - 執行 stopRequest');
                  stopRequest();
                } else {
                  console.log('  - 執行 handleSendMessage');
                  handleSendMessage();
                }
              }}
              disabled={!loading && !inputMessage.trim() && !(enableFileUpload && fileUpload?.hasFile)}
              title={loading ? "點擊停止當前任務" : "發送消息"}
              style={{ 
                borderRadius: '50%', 
                width: '40px', 
                height: '40px',
                marginLeft: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: loading 
                  ? '#595959' 
                  : ((!inputMessage.trim() && !(enableFileUpload && fileUpload?.hasFile)) 
                    ? '#d9d9d9' 
                    : '#1890ff'),
                color: '#fff',
                border: `1px solid ${loading 
                  ? '#595959' 
                  : ((!inputMessage.trim() && !(enableFileUpload && fileUpload?.hasFile)) 
                    ? '#d9d9d9' 
                    : '#1890ff')}`,
                cursor: (loading || inputMessage.trim() || (enableFileUpload && fileUpload?.hasFile)) 
                  ? 'pointer' 
                  : 'not-allowed',
                fontSize: '16px',
                transition: 'all 0.3s ease',
                outline: 'none'
              }}
            >
              {loading ? <MinusSquareFilled /> : <SendOutlined />}
            </button>
          </div>
        </div>
      </Content>
    </Layout>
  );
};

export default CommonAssistantChatPage;
