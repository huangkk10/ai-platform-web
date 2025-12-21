import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

// 設置 axios 默認配置
axios.defaults.withCredentials = true;
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';
// 不再設置 baseURL，使用相對路徑

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [permissions, setPermissions] = useState({});
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);

  // 檢查當前用戶是否已登入
  const checkAuthStatus = async () => {
    console.log('AuthContext: Checking auth status...');
    try {
      const response = await axios.get('/api/auth/user/', {
        withCredentials: true
      });
      console.log('AuthContext: Auth API response:', response.data);
      if (response.data.success && response.data.authenticated) {
        setUser(response.data.user);
        setIsAuthenticated(true);
        console.log('AuthContext: User authenticated:', response.data.user);
        
        // 獲取用戶權限信息
        await fetchUserPermissions();
      } else {
        setUser(null);
        setUserProfile(null);
        setPermissions({});
        setIsAuthenticated(false);
        console.log('AuthContext: User not authenticated');
      }
    } catch (error) {
      console.error('AuthContext: 檢查認證狀態失敗:', error);
      setUser(null);
      setUserProfile(null);
      setPermissions({});
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
      setInitialized(true);
      console.log('AuthContext: Loading completed, initialized');
    }
  };

  // 獲取用戶權限
  const fetchUserPermissions = async () => {
    try {
      const response = await axios.get('/api/profiles/my-permissions/', {
        withCredentials: true
      });
      if (response.data.success) {
        setUserProfile(response.data.data);
        
        // 提取權限信息
        const permissionsData = {
          webProtocolRAG: response.data.data.web_protocol_rag,
          webAIOCR: response.data.data.web_ai_ocr,
          webRVTAssistant: response.data.data.web_rvt_assistant,
          webProtocolAssistant: response.data.data.web_protocol_assistant,
          kbProtocolRAG: response.data.data.kb_protocol_rag,
          kbAIOCR: response.data.data.kb_ai_ocr,
          kbRVTAssistant: response.data.data.kb_rvt_assistant,
          kbProtocolAssistant: response.data.data.kb_protocol_assistant,
          isSuperAdmin: response.data.data.is_super_admin,
          canManagePermissions: response.data.data.can_manage_permissions,
          // 系統管理權限
          isStaff: response.data.data.is_staff || false,
          isSuperuser: response.data.data.is_superuser || false
        };
        
        setPermissions(permissionsData);
        console.log('AuthContext: User permissions loaded:', permissionsData);
      }
    } catch (error) {
      console.error('AuthContext: 獲取用戶權限失敗:', error);
      setPermissions({});
    }
  };

  // 登入函數
  const login = async (username, password) => {
    try {
      const response = await axios.post('/api/auth/login/', {
        username,
        password
      }, {
        withCredentials: true
      });

      if (response.data.success) {
        // 修正：後端回傳的結構是 response.data.data.user
        const userData = response.data.data?.user || response.data.user;
        setUser(userData);
        setIsAuthenticated(true);
        
        // 登入成功後獲取權限
        await fetchUserPermissions();
        
        return { success: true, message: response.data.message };
      } else {
        return { success: false, message: response.data.message };
      }
    } catch (error) {
      console.error('登入失敗:', error);
      
      const errorData = error.response?.data;
      
      // 🆕 處理審核狀態錯誤
      if (errorData?.status === 'pending') {
        return { 
          success: false, 
          message: errorData.error || '您的帳號尚未通過審核，請耐心等待',
          status: 'pending'
        };
      } else if (errorData?.status === 'rejected') {
        return { 
          success: false, 
          message: errorData.error || '您的帳號申請已被拒絕',
          status: 'rejected',
          rejection_reason: errorData.rejection_reason
        };
      } else if (errorData?.status === 'suspended') {
        return { 
          success: false, 
          message: errorData.error || '您的帳號已被停用',
          status: 'suspended'
        };
      } else if (errorData?.error) {
        return { success: false, message: errorData.error };
      } else if (errorData?.message) {
        return { success: false, message: errorData.message };
      } else if (error.response?.status === 401) {
        return { success: false, message: '用戶名或密碼錯誤' };
      } else if (error.response?.status === 400) {
        return { success: false, message: '請求格式錯誤' };
      } else if (error.response?.status === 403) {
        return { success: false, message: '帳號無法登入' };
      } else {
        return { success: false, message: '網路連接失敗，請稍後再試' };
      }
    }
  };

  // 登出函數
  const logout = async () => {
    try {
      const response = await axios.post('/api/auth/logout/', {}, {
        withCredentials: true
      });
      
      // 無論 API 回應如何，都清除前端狀態
      setUser(null);
      setUserProfile(null);
      setPermissions({});
      setIsAuthenticated(false);
      
      if (response.data.success) {
        return { success: true, message: response.data.message };
      } else {
        return { success: true, message: '已清除登入狀態' };
      }
    } catch (error) {
      console.error('登出失敗:', error);
      // 即使 API 失敗，也清除本地狀態
      setUser(null);
      setUserProfile(null);
      setPermissions({});
      setIsAuthenticated(false);
      return { success: true, message: '已清除登入狀態' };
    }
  };

  // 獲取用戶資訊
  const refreshUserInfo = async () => {
    if (!isAuthenticated) return;
    
    try {
      const response = await axios.get('/api/auth/user/', {
        withCredentials: true
      });
      if (response.data.success && response.data.authenticated) {
        setUser(response.data.user);
      }
    } catch (error) {
      console.error('刷新用戶資訊失敗:', error);
    }
  };

  // 組件掛載時檢查認證狀態
  useEffect(() => {
    checkAuthStatus();
  }, []);

  // 權限檢查工具函數
  const hasPermission = (permissionName) => {
    return permissions[permissionName] || false;
  };

  const hasAnyWebPermission = () => {
    return permissions.webProtocolRAG || permissions.webAIOCR || permissions.webRVTAssistant;
  };

  const hasAnyKBPermission = () => {
    return permissions.kbProtocolRAG || permissions.kbAIOCR || permissions.kbRVTAssistant || permissions.kbProtocolAssistant;
  };

  const canManagePermissions = () => {
    return permissions.isSuperAdmin || permissions.canManagePermissions;
  };

  const value = {
    user,
    userProfile,
    permissions,
    isAuthenticated,
    loading,
    initialized,
    login,
    logout,
    refreshUserInfo,
    fetchUserPermissions,
    checkAuthStatus,
    // 權限檢查函數
    hasPermission,
    hasAnyWebPermission,
    hasAnyKBPermission,
    canManagePermissions
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;