import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Card,
  Table,
  message
} from 'antd';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../../contexts/AuthContext';
import useKnowledgeBaseList from '../../hooks/useKnowledgeBaseList';
import { createKnowledgeBaseColumns, showDeleteConfirm } from './createKnowledgeBaseColumns';

/**
 * 通用知識庫頁面組件
 * 
 * 配置驅動的知識庫列表頁面，支持查看、編輯、刪除等標準操作
 * 
 * @param {Object} props - 組件屬性
 * @param {Object} props.config - 知識庫配置對象（來自 knowledgeBaseConfig.js）
 * @param {React.Component} props.DetailModal - 詳細內容 Modal 組件（可選）
 * @param {Function} props.onItemClick - 點擊項目的回調函數（可選）
 * @param {Object} props.extraTableProps - 額外的 Table 屬性（可選）
 * 
 * @example
 * import { knowledgeBaseConfigs } from '@/config/knowledgeBaseConfig';
 * import KnowledgeBasePage from '@/components/KnowledgeBase/KnowledgeBasePage';
 * import GuideDetailModal from '@/components/GuideDetailModal';
 * 
 * const RvtGuidePage = () => (
 *   <KnowledgeBasePage
 *     config={knowledgeBaseConfigs['rvt-assistant']}
 *     DetailModal={GuideDetailModal}
 *   />
 * );
 */
const KnowledgeBasePage = ({
  config,
  DetailModal = null,
  onItemClick = null,
  extraTableProps = {}
}) => {
  // 驗證必需參數
  if (!config) {
    console.error('❌ KnowledgeBasePage: config 參數為必需');
    throw new Error('KnowledgeBasePage 需要 config 參數');
  }

  const { user, isAuthenticated, loading: authLoading, initialized } = useAuth();
  const navigate = useNavigate();
  
  // 使用通用 Hook 管理數據
  const { 
    items, 
    loading, 
    fetchItems, 
    getItemDetail, 
    deleteItem 
  } = useKnowledgeBaseList(config, initialized, isAuthenticated);
  
  // Modal 狀態管理
  const [detailModalState, setDetailModalState] = useState({
    visible: false,
    item: null
  });

  // 初始載入數據
  useEffect(() => {
    if (initialized && isAuthenticated) {
      fetchItems();
    }
  }, [initialized, isAuthenticated, fetchItems]);

  // 監聽來自 TopHeader 的重新整理事件
  useEffect(() => {
    const handleReload = () => {
      console.log(`🔄 收到重新整理事件: ${config.events.reload}`);
      fetchItems();
    };
    
    // 使用配置中定義的事件名稱
    const eventName = config.events.reload;
    window.addEventListener(eventName, handleReload);
    
    return () => {
      window.removeEventListener(eventName, handleReload);
    };
  }, [config.events.reload, fetchItems]);

  // 處理查看詳細內容
  const handleViewDetail = useCallback(async (record) => {
    try {
      // 如果提供了自定義點擊回調，使用它
      if (onItemClick) {
        onItemClick(record);
        return;
      }

      // 如果提供了 DetailModal，獲取詳細資料並顯示
      if (DetailModal) {
        const item = await getItemDetail(record.id);
        setDetailModalState({
          visible: true,
          item: item
        });
      } else {
        // 如果沒有提供 Modal，直接跳轉到編輯頁面
        const editPath = config.routes.getEditPath(record.id);
        navigate(editPath);
      }
    } catch (error) {
      // 錯誤已在 Hook 中處理
      console.error('❌ 處理查看詳細內容時發生錯誤:', error);
    }
  }, [getItemDetail, onItemClick, DetailModal, config, navigate]);

  // 處理刪除
  const handleDelete = useCallback((record) => {
    // 使用配置中定義的權限判斷
    if (!config.permissions.canDelete(user)) {
      message.error('您沒有權限執行此操作');
      return;
    }

    // 使用配置中的刪除確認文字
    showDeleteConfirm(record, async (id, title) => {
      await deleteItem(id, title);
    }, config);
  }, [config, user, deleteItem]);

  // 關閉 Modal
  const handleCloseModal = useCallback(() => {
    setDetailModalState({
      visible: false,
      item: null
    });
  }, []);

  // 編輯項目（從 Modal 觸發）
  const handleEditItem = useCallback((id) => {
    handleCloseModal();
    // 使用配置中定義的路由生成方法
    const editPath = config.routes.getEditPath(id);
    navigate(editPath);
  }, [config, navigate, handleCloseModal]);

  // 生成表格列配置
  const columns = useMemo(
    () => createKnowledgeBaseColumns(config, navigate, user, handleViewDetail, handleDelete),
    [config, navigate, user, handleViewDetail, handleDelete]
  );

  // 載入中狀態
  if (!initialized || authLoading) {
    return (
      <div style={{ 
        padding: '20px', 
        textAlign: 'center',
        fontSize: '16px',
        color: '#666'
      }}>
        載入中...
      </div>
    );
  }

  // 未認證狀態
  if (!isAuthenticated) {
    return (
      <Card title={config.labels.pageTitle} style={{ margin: '20px' }}>
        <p>請先登入以查看 {config.labels.pageTitle} 內容。</p>
      </Card>
    );
  }

  return (
    <div style={{ 
      height: 'calc(100vh - 64px)', // 扣除 TopHeader 高度
      display: 'flex',
      flexDirection: 'column',
      padding: '20px'
    }}>
      {/* 主要內容 */}
      <Card style={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <Table
            columns={columns}
            dataSource={items}
            rowKey="id"
            loading={loading}
            scroll={config.table.scroll}
            pagination={config.table.pagination}
            size="middle"
            {...extraTableProps}
          />
        </div>
      </Card>

      {/* 詳細內容 Modal（如果提供） */}
      {DetailModal && (
        <DetailModal
          visible={detailModalState.visible}
          guide={detailModalState.item}  // 保持 guide 命名以兼容 GuideDetailModal
          item={detailModalState.item}    // 同時提供 item 命名以支持新組件
          onClose={handleCloseModal}
          onEdit={handleEditItem}
        />
      )}
    </div>
  );
};

export default KnowledgeBasePage;
