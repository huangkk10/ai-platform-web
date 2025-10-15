import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  message
} from 'antd';
import { useNavigate } from 'react-router-dom';
import { 
  PlusOutlined, 
  ReloadOutlined,
  ToolOutlined
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import useRvtGuideList from '../../hooks/useRvtGuideList';
import { createRvtGuideColumns, showDeleteConfirm } from './columns';
import RvtGuideDetailModal from '../../components/RvtGuideDetailModal';

const { Title } = Typography;

/**
 * RVT Assistant 知識庫頁面
 * 顯示 RVT Guide 列表，支持查看、編輯、刪除等操作
 */
const RvtGuidePage = () => {
  const { user, isAuthenticated, loading: authLoading, initialized } = useAuth();
  const navigate = useNavigate();
  
  // 使用自定義 Hook 管理數據
  const { guides, loading, fetchGuides, getGuideDetail, deleteGuide } = useRvtGuideList(initialized, isAuthenticated);
  
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

  // 處理刪除
  const handleDelete = (record) => {
    if (!user?.is_staff) {
      message.error('您沒有權限執行此操作');
      return;
    }

    showDeleteConfirm(record, async (id, title) => {
      await deleteGuide(id, title);
    });
  };

  // 關閉 Modal
  const handleCloseModal = () => {
    setDetailModalState({
      visible: false,
      guide: null
    });
  };

  // 編輯文檔
  const handleEditGuide = (id) => {
    handleCloseModal();
    navigate(`/knowledge/rvt-guide/markdown-edit/${id}`);
  };

  // 生成表格列配置
  const columns = useMemo(
    () => createRvtGuideColumns(navigate, user, handleViewDetail, handleDelete),
    [navigate, user]
  );

  // 載入中狀態
  if (!initialized || authLoading) {
    return <div style={{ padding: '20px' }}>載入中...</div>;
  }

  // 未認證狀態
  if (!isAuthenticated) {
    return (
      <Card title="RVT Assistant 知識庫" style={{ margin: '20px' }}>
        <p>請先登入以查看 RVT Assistant 知識庫內容。</p>
      </Card>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      {/* 主要內容 */}
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ToolOutlined />
            <Title level={4} style={{ margin: 0 }}>RVT Assistant 知識庫</Title>
          </div>
        }
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchGuides}
              loading={loading}
            >
              重新整理
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => navigate('/knowledge/rvt-guide/markdown-create')}
            >
              新增 User Guide
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={guides}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1400, y: 600 }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 項，共 ${total} 項`,
            pageSize: 10,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
          size="middle"
        />
      </Card>

      {/* 詳細內容 Modal */}
      <RvtGuideDetailModal
        visible={detailModalState.visible}
        guide={detailModalState.guide}
        onClose={handleCloseModal}
        onEdit={handleEditGuide}
      />
    </div>
  );
};

export default RvtGuidePage;
