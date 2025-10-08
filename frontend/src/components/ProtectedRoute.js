import React from 'react';
import { Card, Typography, Spin } from 'antd';
import { useAuth } from '../contexts/AuthContext';

const { Title, Paragraph } = Typography;

/**
 * 受保護的路由組件
 * @param {Object} props
 * @param {React.ReactNode} props.children - 子組件
 * @param {string} props.permission - 需要的權限名稱
 * @param {string} props.fallbackTitle - 權限不足時顯示的標題
 * @param {string} props.fallbackMessage - 權限不足時顯示的訊息
 */
const ProtectedRoute = ({ 
  children, 
  permission, 
  fallbackTitle = "存取受限",
  fallbackMessage = "您沒有權限訪問此頁面"
}) => {
  const { isAuthenticated, hasPermission, initialized } = useAuth();

  // 載入中
  if (!initialized) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: '16px' }}>載入中...</div>
      </div>
    );
  }

  // 檢查認證和權限
  if (!isAuthenticated || (permission && !hasPermission(permission))) {
    let message = fallbackMessage;
    
    if (!isAuthenticated) {
      message = "請先登入才能訪問此頁面";
    } else if (permission && !hasPermission(permission)) {
      message = `您沒有 ${permission} 權限，請聯絡管理員`;
    }

    return (
      <div style={{ padding: '24px' }}>
        <Card>
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Title level={3}>{fallbackTitle}</Title>
            <Paragraph>{message}</Paragraph>
          </div>
        </Card>
      </div>
    );
  }

  // 有權限，渲染子組件
  return children;
};

export default ProtectedRoute;