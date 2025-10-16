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
 * 通用知識庫表格列生成器
 * 
 * 根據配置自動生成 Ant Design Table 的 columns 配置
 * 支持查看、編輯、刪除等標準操作
 * 
 * @param {Object} config - 知識庫配置對象（來自 knowledgeBaseConfig.js）
 * @param {Function} navigate - React Router 的 navigate 函數
 * @param {Object} user - 當前用戶對象
 * @param {Function} handleViewDetail - 查看詳細內容的處理函數
 * @param {Function} handleDelete - 刪除處理函數
 * @returns {Array} Ant Design Table 的 columns 配置
 * 
 * @example
 * import { knowledgeBaseConfigs } from '@/config/knowledgeBaseConfig';
 * import { createKnowledgeBaseColumns } from '@/components/KnowledgeBase/createKnowledgeBaseColumns';
 * 
 * const config = knowledgeBaseConfigs['rvt-assistant'];
 * const columns = createKnowledgeBaseColumns(config, navigate, user, handleViewDetail, handleDelete);
 */
export const createKnowledgeBaseColumns = (
  config,
  navigate,
  user,
  handleViewDetail,
  handleDelete
) => {
  // 驗證必需參數
  if (!config) {
    console.error('❌ createKnowledgeBaseColumns: config 參數為必需');
    throw new Error('createKnowledgeBaseColumns 需要 config 參數');
  }

  // 從配置中提取欄位資訊
  const primaryField = config.columns?.primaryField || 'title';
  const dateField = config.columns?.dateField || 'created_at';
  const sortField = config.columns?.sortField || dateField;
  const sortOrder = config.columns?.sortOrder || 'descend';

  // 基礎列配置
  const columns = [
    // ===== 查看列 =====
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

    // ===== 主要欄位列（動態） =====
    {
      title: getPrimaryFieldTitle(primaryField),
      dataIndex: primaryField,
      key: primaryField,
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
      sorter: (a, b) => String(a[primaryField]).localeCompare(String(b[primaryField])),
    },

    // ===== 日期欄位列（動態） =====
    {
      title: getDateFieldTitle(dateField),
      dataIndex: dateField,
      key: dateField,
      width: 140,
      render: (text) => text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '-',
      sorter: (a, b) => {
        const dateA = a[dateField] ? dayjs(a[dateField]).unix() : 0;
        const dateB = b[dateField] ? dayjs(b[dateField]).unix() : 0;
        return dateA - dateB;
      },
      defaultSortOrder: dateField === sortField ? sortOrder : undefined,
    },
  ];

  // ===== 添加額外欄位（如果配置中有定義） =====
  if (config.columns?.extraColumns && Array.isArray(config.columns.extraColumns)) {
    config.columns.extraColumns.forEach(extraColumn => {
      columns.push({
        title: extraColumn.title,
        dataIndex: extraColumn.dataIndex,
        key: extraColumn.key || extraColumn.dataIndex,
        width: extraColumn.width || 150,
        render: extraColumn.render || ((text) => text || '-'),
        sorter: extraColumn.sorter,
        ...extraColumn, // 允許完全自定義
      });
    });
  }

  // ===== 操作列 =====
  columns.push({
    title: '操作',
    key: 'actions',
    width: 120,
    fixed: 'right',
    render: (_, record) => {
      // 使用配置中的路由生成方法
      const editPath = config.routes?.getEditPath 
        ? config.routes.getEditPath(record.id)
        : '#';
      
      // 使用配置中的權限判斷
      const canEdit = config.permissions?.canEdit 
        ? config.permissions.canEdit(user)
        : true;
      
      const canDelete = config.permissions?.canDelete 
        ? config.permissions.canDelete(user)
        : false;
      
      return (
        <Space size="small">
          {canEdit && (
            <Button
              icon={<EditOutlined />}
              size="small"
              type="text"
              onClick={() => navigate(editPath)}
              title="編輯"
              style={{ color: '#1890ff' }}
            />
          )}
          {canDelete && (
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
      );
    },
  });

  return columns;
};

/**
 * 獲取主要欄位的標題（根據欄位名稱推斷）
 * @param {string} fieldName - 欄位名稱
 * @returns {string} 欄位標題
 */
function getPrimaryFieldTitle(fieldName) {
  const titleMap = {
    'title': '標題',
    'name': '名稱',
    'subject': '主題',
    'description': '描述',
    'content': '內容',
  };
  return titleMap[fieldName] || '標題';
}

/**
 * 獲取日期欄位的標題（根據欄位名稱推斷）
 * @param {string} fieldName - 欄位名稱
 * @returns {string} 欄位標題
 */
function getDateFieldTitle(fieldName) {
  const titleMap = {
    'created_at': '建立時間',
    'updated_at': '更新時間',
    'modified_at': '修改時間',
    'date': '日期',
    'timestamp': '時間戳記',
  };
  return titleMap[fieldName] || '時間';
}

/**
 * 顯示刪除確認對話框（通用版本）
 * 
 * @param {Object} record - 要刪除的記錄
 * @param {Function} onConfirm - 確認刪除的回調函數
 * @param {Object} config - 知識庫配置對象
 */
export const showDeleteConfirm = (record, onConfirm, config) => {
  // 從配置中獲取文字（帶預設值）
  const title = config?.labels?.deleteConfirmTitle || '確認刪除';
  
  // 支持函數或字串格式的內容
  let content;
  if (typeof config?.labels?.deleteConfirmContent === 'function') {
    content = config.labels.deleteConfirmContent(record.title || record.name || '此項目');
  } else if (typeof config?.labels?.deleteConfirmContent === 'string') {
    content = config.labels.deleteConfirmContent;
  } else {
    // 預設內容
    const itemName = record.title || record.name || '此項目';
    content = `確定要刪除 "${itemName}" 嗎？`;
  }
  
  Modal.confirm({
    title: title,
    content: content,
    okText: '確認',
    cancelText: '取消',
    okType: 'danger',
    onOk: () => {
      // 支持傳入 id 和 title/name
      const itemId = record.id;
      const itemTitle = record.title || record.name || '項目';
      onConfirm(itemId, itemTitle);
    },
  });
};

/**
 * 創建自定義欄位配置輔助函數
 * 
 * 用於在配置文件中快速定義額外欄位
 * 
 * @example
 * extraColumns: [
 *   createCustomColumn('status', '狀態', 100, (text) => <Tag>{text}</Tag>),
 *   createCustomColumn('priority', '優先級', 80),
 * ]
 */
export const createCustomColumn = (
  dataIndex,
  title,
  width = 150,
  render = null,
  sorter = null
) => {
  return {
    dataIndex,
    title,
    width,
    render: render || ((text) => text || '-'),
    sorter: sorter,
  };
};

export default createKnowledgeBaseColumns;
