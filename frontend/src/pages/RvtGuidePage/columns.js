import React from 'react';
import { Button, Space, Tooltip, Typography, Modal } from 'antd';
import { 
  EyeOutlined, 
  EditOutlined, 
  DeleteOutlined 
} from '@ant-design/icons';
import dayjs from 'dayjs';

const { Text } = Typography;

/**
 * 創建 RVT Guide 表格列配置
 * 
 * @param {Function} navigate - React Router 的 navigate 函數
 * @param {Object} user - 當前用戶對象
 * @param {Function} handleViewDetail - 查看詳細內容的處理函數
 * @param {Function} handleDelete - 刪除處理函數
 * @returns {Array} Ant Design Table 的 columns 配置
 */
export const createRvtGuideColumns = (navigate, user, handleViewDetail, handleDelete) => {
  return [
    {
      title: '查看',
      key: 'view',
      width: 80,
      fixed: 'left',
      render: (_, record) => (
        <Button 
          icon={<EyeOutlined />}
          size="small"
          type="text"
          onClick={() => handleViewDetail(record)}
          title="查看詳細內容"
          style={{ color: '#1890ff' }}
        />
      ),
    },
    {
      title: '標題',
      dataIndex: 'title',
      key: 'title',
      width: 250,
      fixed: 'left',
      ellipsis: {
        showTitle: true,
      },
      render: (text) => (
        <Tooltip title={text}>
          <Text strong style={{ cursor: 'help' }} ellipsis>
            {text}
          </Text>
        </Tooltip>
      ),
      sorter: (a, b) => a.title.localeCompare(b.title),
    },
    {
      title: '建立時間',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 140,
      render: (text) => dayjs(text).format('YYYY-MM-DD HH:mm'),
      sorter: (a, b) => dayjs(a.created_at).unix() - dayjs(b.created_at).unix(),
      defaultSortOrder: 'descend',
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            icon={<EditOutlined />}
            size="small"
            type="text"
            onClick={() => navigate(`/knowledge/rvt-guide/markdown-edit/${record.id}`)}
            title="編輯 (Markdown 編輯器)"
            style={{ color: '#1890ff' }}
          />
          {user?.is_staff && (
            <Button
              icon={<DeleteOutlined />}
              size="small"
              type="text"
              danger
              onClick={() => handleDelete(record)}
              title="刪除"
            />
          )}
        </Space>
      ),
    },
  ];
};

/**
 * 顯示刪除確認對話框
 * 
 * @param {Object} record - 要刪除的記錄
 * @param {Function} onConfirm - 確認刪除的回調函數
 */
export const showDeleteConfirm = (record, onConfirm) => {
  Modal.confirm({
    title: '確認刪除',
    content: `確定要刪除指導文檔 "${record.title}" 嗎？`,
    okText: '確認',
    cancelText: '取消',
    okType: 'danger',
    onOk: () => onConfirm(record.id, record.title),
  });
};
