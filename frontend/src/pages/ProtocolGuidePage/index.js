import React from 'react';
import { knowledgeBaseConfigs } from '../../config/knowledgeBaseConfig';
import KnowledgeBasePage from '../../components/KnowledgeBase/KnowledgeBasePage';
import GuideDetailModal from '../../components/GuideDetailModal';

/**
 * Protocol Assistant 知識庫頁面
 * 
 * 🎯 使用完整的配置驅動架構：
 * - 配置文件: config/knowledgeBaseConfig.js
 * - 通用 Hook: hooks/useKnowledgeBaseList.js
 * - 通用 Columns: components/KnowledgeBase/createKnowledgeBaseColumns.js
 * - 通用頁面: components/KnowledgeBase/KnowledgeBasePage.jsx
 * 
 * 🚀 架構優勢：
 * - 代碼重用率 98%
 * - 只需 20 行代碼創建新知識庫
 * - 統一的用戶體驗
 */
const ProtocolGuidePage = () => {
  // 獲取 Protocol Assistant 配置
  const config = knowledgeBaseConfigs['protocol-assistant'];
  
  // 使用通用頁面組件
  return (
    <KnowledgeBasePage
      config={config}
      DetailModal={GuideDetailModal}
    />
  );
};

export default ProtocolGuidePage;
