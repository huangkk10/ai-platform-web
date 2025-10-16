/**
 * 知識庫配置文件
 * 
 * 用於統一管理不同知識庫的配置資訊，包括 API、路由、事件、標籤、權限等
 * 
 * 使用方式：
 * import { knowledgeBaseConfigs } from '@/config/knowledgeBaseConfig';
 * const config = knowledgeBaseConfigs['rvt-assistant'];
 * 
 * 新增知識庫：
 * 只需複製現有配置，修改對應的值即可快速創建新的知識庫系統
 */

export const knowledgeBaseConfigs = {
  /**
   * RVT Assistant 知識庫配置
   */
  'rvt-assistant': {
    // ===== API 配置 =====
    apiEndpoint: '/api/rvt-guides/',
    pageSize: 100, // 列表每頁顯示數量
    
    // ===== 路由配置 =====
    routes: {
      list: '/knowledge/rvt-log',                           // 列表頁
      create: '/knowledge/rvt-guide/markdown-create',       // 新建頁
      edit: '/knowledge/rvt-guide/markdown-edit/:id',       // 編輯頁
      preview: '/knowledge/rvt-guide/preview/:id',          // 預覽頁
      // 輔助方法：生成編輯路徑
      getEditPath: (id) => `/knowledge/rvt-guide/markdown-edit/${id}`,
      // 輔助方法：生成預覽路徑
      getPreviewPath: (id) => `/knowledge/rvt-guide/preview/${id}`,
    },
    
    // ===== 事件名稱 =====
    events: {
      reload: 'rvt-guide-reload',  // 重新載入列表的事件名稱
    },
    
    // ===== 顯示文字 =====
    labels: {
      pageTitle: 'RVT Assistant 知識庫',
      createButton: '新增 User Guide',
      reloadButton: '重新整理',
      editTitle: '編輯 RVT Guide',
      createTitle: '新建 RVT Guide',
      deleteConfirmTitle: '確認刪除',
      deleteConfirmContent: (title) => `確定要刪除指導文檔 "${title}" 嗎？`,
      deleteSuccess: '刪除成功',
      deleteFailed: '刪除失敗',
      fetchSuccess: 'RVT Guide 列表載入成功',
      fetchFailed: '獲取資料失敗',
      detailSuccess: '文檔詳細資料載入成功',
      detailFailed: '獲取詳細資料失敗',
    },
    
    // ===== Table 欄位配置 =====
    columns: {
      primaryField: 'title',      // 主要顯示欄位
      dateField: 'created_at',    // 日期欄位
      sortField: 'created_at',    // 預設排序欄位
      sortOrder: 'descend',       // 預設排序方向
      // 可擴展：未來可添加額外欄位
      extraColumns: [],
    },
    
    // ===== 權限配置 =====
    permissions: {
      // 刪除權限：只有管理員可以刪除
      canDelete: (user) => user?.is_staff === true,
      // 編輯權限：所有已登入用戶都可以編輯
      canEdit: (user) => !!user,
      // 查看權限：所有已登入用戶都可以查看
      canView: (user) => !!user,
    },
    
    // ===== Table 配置 =====
    table: {
      scroll: { x: 1400, y: 'calc(100vh - 220px)' },
      pagination: {
        defaultPageSize: 10,
        pageSizeOptions: ['10', '20', '50', '100'],
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total, range) => `第 ${range[0]}-${range[1]} 項，共 ${total} 項`,
      },
    },
  },

  /**
   * 🚀 未來擴展範例：Protocol Assistant 知識庫
   * 
   * 創建新知識庫時，只需複製以下配置並修改對應值即可
   */
  'protocol-assistant': {
    apiEndpoint: '/api/protocol-guides/',
    pageSize: 100,
    
    routes: {
      list: '/knowledge/protocol-log',
      create: '/knowledge/protocol-guide/markdown-create',
      edit: '/knowledge/protocol-guide/markdown-edit/:id',
      getEditPath: (id) => `/knowledge/protocol-guide/markdown-edit/${id}`,
    },
    
    events: {
      reload: 'protocol-guide-reload',
    },
    
    labels: {
      pageTitle: 'Protocol Assistant 知識庫',
      createButton: '新增 Protocol Guide',
      reloadButton: '重新整理',
      editTitle: '編輯 Protocol Guide',
      createTitle: '新建 Protocol Guide',
      deleteConfirmTitle: '確認刪除',
      deleteConfirmContent: (title) => `確定要刪除協議文檔 "${title}" 嗎？`,
      deleteSuccess: '刪除成功',
      deleteFailed: '刪除失敗',
      fetchSuccess: 'Protocol Guide 列表載入成功',
      fetchFailed: '獲取資料失敗',
      detailSuccess: '文檔詳細資料載入成功',
      detailFailed: '獲取詳細資料失敗',
    },
    
    columns: {
      primaryField: 'title',
      dateField: 'created_at',
      sortField: 'created_at',
      sortOrder: 'descend',
      extraColumns: [],
    },
    
    permissions: {
      canDelete: (user) => user?.is_staff === true,
      canEdit: (user) => !!user,
      canView: (user) => !!user,
    },
    
    table: {
      scroll: { x: 1400, y: 'calc(100vh - 220px)' },
      pagination: {
        defaultPageSize: 10,
        pageSizeOptions: ['10', '20', '50', '100'],
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total, range) => `第 ${range[0]}-${range[1]} 項，共 ${total} 項`,
      },
    },
  },
};

/**
 * 獲取知識庫配置
 * @param {string} configKey - 配置鍵名
 * @returns {Object} 配置對象
 * @throws {Error} 如果配置不存在
 */
export const getKnowledgeBaseConfig = (configKey) => {
  const config = knowledgeBaseConfigs[configKey];
  if (!config) {
    throw new Error(`知識庫配置 '${configKey}' 不存在`);
  }
  return config;
};

/**
 * 獲取所有可用的知識庫配置鍵名
 * @returns {string[]} 配置鍵名陣列
 */
export const getAvailableKnowledgeBases = () => {
  return Object.keys(knowledgeBaseConfigs);
};

/**
 * 檢查知識庫配置是否存在
 * @param {string} configKey - 配置鍵名
 * @returns {boolean}
 */
export const hasKnowledgeBaseConfig = (configKey) => {
  return configKey in knowledgeBaseConfigs;
};
