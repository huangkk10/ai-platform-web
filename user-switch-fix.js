// 用戶切換修復代碼片段
// 添加到 RvtAssistantChatPage.js 中

// 1. 在導入部分添加:
import { useAuth } from '../contexts/AuthContext';

// 2. 在組件開始添加用戶認證:
const { user, isAuthenticated } = useAuth();

// 3. 在狀態變量中添加:
const [currentUserId, setCurrentUserId] = useState(user?.id || null);

// 4. 在 useEffect 中添加用戶切換監聽:
useEffect(() => {
  const newUserId = user?.id || null;
  
  // 檢查用戶是否發生變化（避免初始化時的誤觸發）
  if (currentUserId !== null && currentUserId !== newUserId) {
    console.log('🔄 用戶切換偵測:', currentUserId, '->', newUserId);
    
    // 清除舊的對話狀態
    clearStoredChat();
    setConversationId('');
    setFeedbackStates({});
    
    // 重置為歡迎消息
    setMessages([{ ...DEFAULT_WELCOME_MESSAGE, timestamp: new Date() }]);
    
    // 顯示用戶切換提示
    if (newUserId) {
      message.info({
        content: `🔄 偵測到用戶切換，對話已重置。歡迎 ${user?.username || '新用戶'}！`,
        duration: 3
      });
    } else {
      message.info({
        content: '🔄 用戶登出，對話已重置。您可以繼續以訪客身份使用。',
        duration: 3
      });
    }
  }
  
  // 更新當前用戶ID
  setCurrentUserId(newUserId);
}, [user?.id, currentUserId]);