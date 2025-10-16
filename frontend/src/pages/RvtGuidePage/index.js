import React from 'react';
import { knowledgeBaseConfigs } from '../../config/knowledgeBaseConfig';
import KnowledgeBasePage from '../../components/KnowledgeBase/KnowledgeBasePage';
import GuideDetailModal from '../../components/GuideDetailModal';

/**
 * RVT Assistant 知識庫頁面（重構版）
 * 
 * 🎯 代碼精簡：166 行 → 20 行 (-88%)
 * 
 * 🔧 使用完整的配置驅動架構：
 * - 配置文件: config/knowledgeBaseConfig.js
 * - 通用 Hook: hooks/useKnowledgeBaseList.js
 * - 通用 Columns: components/KnowledgeBase/createKnowledgeBaseColumns.js
 * - 通用頁面: components/KnowledgeBase/KnowledgeBasePage.jsx
 * 
 * 🚀 未來創建新知識庫只需：
 * 1. 在 knowledgeBaseConfig.js 添加配置（10-20 行）
 * 2. 創建類似此文件的入口（20 行）
 * 3. 完成！
 */
const RvtGuidePage = () => {
  // 獲取 RVT Assistant 配置
  const config = knowledgeBaseConfigs['rvt-assistant'];
  
  // 使用通用頁面組件
  return (
    <KnowledgeBasePage
      config={config}
      DetailModal={GuideDetailModal}
    />
  );
};

export default RvtGuidePage;
