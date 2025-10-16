import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  Table,
  message
} from 'antd';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../../contexts/AuthContext';
import { knowledgeBaseConfigs } from '../../config/knowledgeBaseConfig';
import useKnowledgeBaseList from '../../hooks/useKnowledgeBaseList';
import { createRvtGuideColumns, showDeleteConfirm } from './columns';
import GuideDetailModal from '../../components/GuideDetailModal';

/**
 * RVT Assistant 知識庫頁面
 * 顯示 RVT Guide 列表，支持查看、編輯、刪除等操作
 * 
 * 🔧 使用配置驅動架構：
 * - 配置文件: config/knowledgeBaseConfig.js
 * - 通用 Hook: hooks/useKnowledgeBaseList.js
 */
const RvtGuidePage = () => {
  const { user, isAuthenticated, loading: authLoading, initialized } = useAuth();
  const navigate = useNavigate();
  
  // 獲取 RVT Assistant 配置
  const config = knowledgeBaseConfigs['rvt-assistant'];
  
  // 使用通用 Hook 管理數據
  const { 
    items: guides, 
    loading, 
    fetchItems: fetchGuides, 
    getItemDetail: getGuideDetail, 
    deleteItem: deleteGuide 
  } = useKnowledgeBaseList(config, initialized, isAuthenticated);
  
  // Modal 狀態管理
  const [detailModalState, setDetailModalState] = useState({
    visible: false,
    guide: null
  });

  // 初始載入數據
  useEffect(() => {
    if (initialized && isAuthenticated) {
      fetchGuides();
    }
  }, [initialized, isAuthenticated, fetchGuides]);

  // 監聽來自 TopHeader 的重新整理事件（使用配置中的事件名稱）
  useEffect(() => {
    const handleReload = () => {
      fetchGuides();
    };
    
    // 使用配置中定義的事件名稱
    const eventName = config.events.reload;
    window.addEventListener(eventName, handleReload);
    
    return () => {
      window.removeEventListener(eventName, handleReload);
    };
  }, [config.events.reload, fetchGuides]);

  // 處理查看詳細內容
  const handleViewDetail = async (record) => {
    try {
      const guide = await getGuideDetail(record.id);
      setDetailModalState({
        visible: true,
        guide: guide
      });
    } catch (error) {
      // 錯誤已在 Hook 中處理
    }
  };

  // 處理刪除（使用配置中的權限判斷）
  const handleDelete = (record) => {
    // 使用配置中定義的權限判斷
    if (!config.permissions.canDelete(user)) {
      message.error('您沒有權限執行此操作');
      return;
    }

    // 使用配置中的刪除確認文字
    showDeleteConfirm(record, async (id, title) => {
      await deleteGuide(id, title);
    }, config);
  };

  // 關閉 Modal
  const handleCloseModal = () => {
    setDetailModalState({
      visible: false,
      guide: null
    });
  };

  // 編輯文檔（使用配置中的路由）
  const handleEditGuide = (id) => {
    handleCloseModal();
    // 使用配置中定義的路由生成方法
    const editPath = config.routes.getEditPath(id);
    navigate(editPath);
  };

  // 生成表格列配置（傳入 config 以支持配置驅動）
  const columns = useMemo(
    () => createRvtGuideColumns(navigate, user, handleViewDetail, handleDelete, config),
    [navigate, user, config, handleViewDetail, handleDelete]
  );

  // 載入中狀態
  if (!initialized || authLoading) {
    return <div style={{ padding: '20px' }}>載入中...</div>;
  }

  // 未認證狀態（使用配置中的標題）
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
            dataSource={guides}
            rowKey="id"
            loading={loading}
            scroll={config.table.scroll}
            pagination={config.table.pagination}
            size="middle"
          />
        </div>
      </Card>

      {/* 詳細內容 Modal */}
      <GuideDetailModal
        visible={detailModalState.visible}
        guide={detailModalState.guide}
        onClose={handleCloseModal}
        onEdit={handleEditGuide}
      />
    </div>
  );
};

export default RvtGuidePage;
