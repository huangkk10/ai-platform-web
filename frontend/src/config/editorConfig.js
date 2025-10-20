/**
 * Markdown 編輯器配置
 * 用於不同類型內容的編輯器配置管理
 * 
 * 支援的內容類型：
 * - rvt-guide: RVT Assistant 知識庫
 * - protocol-guide: Protocol Assistant 知識庫（未來）
 * - know-issue: Know Issue 問題庫（未來）
 */

export const EDITOR_CONFIGS = {
  'rvt-guide': {
    // 內容類型標識
    contentType: 'rvt-guide',
    
    // API 端點
    apiEndpoint: '/api/rvt-guides/',
    imageEndpoint: '/api/content-images/',
    
    // 路由配置
    listRoute: '/knowledge/rvt-log',
    createRoute: '/knowledge/rvt-guide/markdown-create',
    editRoute: '/knowledge/rvt-guide/markdown-edit',
    
    // 事件名稱
    saveEventName: 'markdown-editor-save',
    
    // UI 文案
    labels: {
      title: '標題 *',
      content: '內容編輯 (支援 Markdown 語法)',
      imageManager: '圖片管理',
      imageManagerStaging: '圖片管理 (暫存)',
      saveButton: '儲存',
      cancelButton: '取消',
      createTitle: '新建 RVT Guide (Markdown 編輯器)',
      editTitle: '編輯 RVT Guide (Markdown 編輯器)',
    },
    
    // 圖片配置
    imageConfig: {
      maxImages: 10,
      maxSizeMB: 2,
      supportedFormats: ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'],
    },
    
    // 預設值（新建時）
    defaults: {
      category: 'general',
      issue_type: 'guide',
    },
    
    // Markdown 編輯器插件
    editorPlugins: [
      'header',
      'font-bold',
      'font-italic',
      'font-underline',
      'font-strikethrough',
      'list-unordered',
      'list-ordered',
      'block-quote',
      'block-wrap',
      'block-code-inline',
      'block-code-block',
      'table',
      'image',
      'link',
      'clear',
      'logger',
      'mode-toggle',
      'full-screen'
    ],
    
    // 提示信息
    hints: {
      markdown: '💡 提示：支援 Markdown 語法，包括標題、列表、連結、圖片、表格等。使用工具欄按鈕或直接輸入 Markdown 語法。可以切換到預覽模式查看效果。',
      imageStaging: '⚡ 暫存模式：圖片將暫存於瀏覽器中，儲存文檔時統一上傳。',
      imageNormal: '💡 游標插入模式：上傳圖片時會在文字編輯區域的游標位置插入圖片資訊。',
    }
  },
  
  // 未來的 Protocol Assistant 配置範例
  'protocol-guide': {
    contentType: 'protocol-guide',
    apiEndpoint: '/api/protocol-guides/',
    imageEndpoint: '/api/content-images/',
    listRoute: '/knowledge/protocol-log',
    createRoute: '/knowledge/protocol-guide/markdown-create',
    editRoute: '/knowledge/protocol-guide/markdown-edit',
    saveEventName: 'protocol-editor-save',
    
    labels: {
      title: 'Protocol 標題 *',
      content: 'Protocol 內容編輯',
      imageManager: 'Protocol 圖片管理',
      imageManagerStaging: 'Protocol 圖片管理 (暫存)',
      saveButton: '儲存協議',
      cancelButton: '取消',
      createTitle: '新建 Protocol Guide',
      editTitle: '編輯 Protocol Guide',
    },
    
    imageConfig: {
      maxImages: 15,
      maxSizeMB: 5,
      supportedFormats: ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'],
    },
    
    defaults: {
      category: 'protocol',
      issue_type: 'guide',
    },
    
    editorPlugins: [
      'header',
      'font-bold',
      'font-italic',
      'list-unordered',
      'list-ordered',
      'block-code-block',
      'table',
      'image',
      'link',
      'full-screen'
    ],
    
    hints: {
      markdown: '💡 Protocol 文檔支援 Markdown 語法，建議使用表格和代碼塊清晰展示協議內容。',
      imageStaging: '⚡ 圖片將在儲存時統一上傳。',
      imageNormal: '💡 可在編輯器中插入協議流程圖和示例圖片。',
    }
  },
  
  // 未來的 Know Issue 配置範例
  'know-issue': {
    contentType: 'know-issue',
    apiEndpoint: '/api/know-issues/',
    imageEndpoint: '/api/content-images/',
    listRoute: '/knowledge/know-issues',
    createRoute: '/knowledge/know-issue/markdown-create',
    editRoute: '/knowledge/know-issue/markdown-edit',
    saveEventName: 'know-issue-editor-save',
    
    labels: {
      title: '問題標題 *',
      content: '問題詳情',
      imageManager: '問題截圖管理',
      imageManagerStaging: '問題截圖管理 (暫存)',
      saveButton: '儲存問題',
      cancelButton: '取消',
      createTitle: '新建 Know Issue',
      editTitle: '編輯 Know Issue',
    },
    
    imageConfig: {
      maxImages: 20,
      maxSizeMB: 3,
      supportedFormats: ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'],
    },
    
    defaults: {
      category: 'issue',
      status: 'open',
    },
    
    editorPlugins: [
      'header',
      'font-bold',
      'list-unordered',
      'list-ordered',
      'block-code-inline',
      'block-code-block',
      'table',
      'image',
      'link',
      'full-screen'
    ],
    
    hints: {
      markdown: '💡 詳細描述問題現象、重現步驟和解決方案，建議附上截圖。',
      imageStaging: '⚡ 問題截圖將在儲存時統一上傳。',
      imageNormal: '💡 可添加錯誤截圖、日誌截圖等輔助說明。',
    }
  }
};

/**
 * 獲取編輯器配置
 * @param {string} contentType - 內容類型
 * @param {object} customConfig - 自定義配置（可選）
 * @returns {object} 合併後的配置
 */
export const getEditorConfig = (contentType, customConfig = {}) => {
  const baseConfig = EDITOR_CONFIGS[contentType];
  
  if (!baseConfig) {
    console.warn(`⚠️ 未找到內容類型 "${contentType}" 的配置，使用 rvt-guide 作為默認配置`);
    return { ...EDITOR_CONFIGS['rvt-guide'], ...customConfig };
  }
  
  // 深度合併配置
  return {
    ...baseConfig,
    ...customConfig,
    labels: { ...baseConfig.labels, ...customConfig.labels },
    imageConfig: { ...baseConfig.imageConfig, ...customConfig.imageConfig },
    defaults: { ...baseConfig.defaults, ...customConfig.defaults },
  };
};

/**
 * 獲取所有支援的內容類型
 * @returns {string[]} 內容類型列表
 */
export const getSupportedContentTypes = () => {
  return Object.keys(EDITOR_CONFIGS);
};

/**
 * 檢查是否為有效的內容類型
 * @param {string} contentType - 內容類型
 * @returns {boolean} 是否有效
 */
export const isValidContentType = (contentType) => {
  return contentType in EDITOR_CONFIGS;
};

export default EDITOR_CONFIGS;
