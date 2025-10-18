import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Space, Spin, Alert, Card } from 'antd';
import { ArrowLeftOutlined, EditOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeHighlight from 'rehype-highlight';

import TopHeader from '../../components/TopHeader';
import { knowledgeBaseConfigs } from '../../config/knowledgeBaseConfig';
import useGuidePreview from '../../hooks/useGuidePreview';
import { fixAllMarkdownTables } from '../../utils/markdownTableFixer';
import { convertImageReferencesToMarkdown } from '../../utils/imageReferenceConverter';
import ContentRenderer from '../../components/ContentRenderer';

import '../../components/markdown/ReactMarkdown.css';
import './GuidePreviewPage.css';

/**
 * Guide 預覽頁面（整頁模式）
 * 
 * 功能：
 * - 整頁顯示 Markdown 內容
 * - 使用 ReactMarkdown 渲染（與 RVT Assistant Chat 一致）
 * - 支持圖片顯示（使用 ContentRenderer 邏輯）
 * - 提供返回和編輯按鈕
 * 
 * 路由：/knowledge/rvt-guide/preview/:id
 */
const GuidePreviewPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = window.location || { pathname: '' };

  // 🎯 根據 URL 路徑自動識別配置
  const isProtocolGuide = location.pathname?.includes('/protocol-guide/');
  const configKey = isProtocolGuide ? 'protocol-assistant' : 'rvt-assistant';
  const config = knowledgeBaseConfigs[configKey];

  // 使用 Hook 載入數據
  const { guide, loading, error } = useGuidePreview(id, config);

  /**
   * 自定義圖片組件
   * 整合 ContentRenderer 的圖片處理邏輯
   */
  const CustomImage = ({ src, alt, ...props }) => {
    // 檢測是否為 IMG:ID 格式
    const imgIdMatch = (src || alt || '').match(/IMG:(\d+)/);

    if (imgIdMatch) {
      const imageId = imgIdMatch[1];
      console.log(`🖼️ 檢測到圖片引用: IMG:${imageId}`);

      // 使用 ContentRenderer 的圖片處理邏輯
      // 注意：ContentRenderer 期望接收完整的內容字符串
      // 這裡我們只渲染單個圖片標記
      return (
        <div style={{ margin: '16px 0' }}>
          <ContentRenderer
            content={`[IMG:${imageId}]`}
            showImageTitles={true}
            showImageDescriptions={true}
            imageMaxWidth={600}
            imageMaxHeight={400}
          />
        </div>
      );
    }

    // 普通圖片（標準 URL）
    return (
      <img
        src={src}
        alt={alt}
        style={{
          maxWidth: '100%',
          height: 'auto',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          margin: '16px 0'
        }}
        {...props}
      />
    );
  };

  /**
   * ReactMarkdown 配置
   * 參考 MessageFormatter.jsx 的配置
   */
  const markdownConfig = {
    remarkPlugins: [remarkGfm],
    rehypePlugins: [rehypeRaw, rehypeHighlight],
    components: {
      // 自定義圖片渲染
      img: CustomImage,

      // 自定義表格渲染
      table: ({ node, ...props }) => (
        <table className="markdown-table" {...props} />
      ),

      // 自定義代碼塊渲染
      code: ({ node, inline, className, children, ...props }) => {
        if (inline) {
          return <code className="inline-code" {...props}>{children}</code>;
        }
        return (
          <pre className="code-block">
            <code className={className} {...props}>
              {children}
            </code>
          </pre>
        );
      },

      // 自定義標題渲染（添加錨點）
      h1: ({ node, children, ...props }) => (
        <h1 id={String(children).toLowerCase().replace(/\s+/g, '-')} {...props}>
          {children}
        </h1>
      ),
      h2: ({ node, children, ...props }) => (
        <h2 id={String(children).toLowerCase().replace(/\s+/g, '-')} {...props}>
          {children}
        </h2>
      ),
    }
  };

  /**
   * 處理內容
   * 修復表格、轉換圖片引用
   */
  const processContent = (content) => {
    if (!content) return '';

    let processed = content;

    // 修復表格分隔線格式
    processed = fixAllMarkdownTables(processed);

    // 🎯 關鍵：將 [IMG:ID] 轉換為 Markdown 圖片格式 ![IMG:ID](IMG:ID)
    // 這樣 ReactMarkdown 才會調用 CustomImage 組件
    processed = convertImageReferencesToMarkdown(processed);

    console.log('📝 內容處理完成', {
      original: content.length,
      processed: processed.length,
      hasImages: processed.includes('![IMG:')
    });

    return processed;
  };

  /**
   * 處理返回
   */
  const handleBack = () => {
    navigate(config.routes.list);
  };

  /**
   * 處理編輯
   */
  const handleEdit = () => {
    if (guide) {
      const editPath = config.routes.getEditPath(guide.id);
      navigate(editPath);
    }
  };

  // TopHeader 按鈕
  const extraActions = (
    <Space>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={handleBack}
        size="large"
      >
        返回列表
      </Button>
      <Button
        type="primary"
        icon={<EditOutlined />}
        onClick={handleEdit}
        size="large"
        disabled={!guide}
      >
        編輯
      </Button>
    </Space>
  );

  // 載入中狀態
  if (loading) {
    return (
      <div className="guide-preview-container">
        <TopHeader
          pageTitle="載入中..."
          extraActions={extraActions}
        />
        <div className="guide-preview-loading">
          <Spin size="large" tip="正在載入文檔..." />
        </div>
      </div>
    );
  }

  // 錯誤狀態
  if (error) {
    return (
      <div className="guide-preview-container">
        <TopHeader
          pageTitle="載入失敗"
          extraActions={extraActions}
        />
        <div className="guide-preview-error">
          <Alert
            message="載入失敗"
            description={error}
            type="error"
            showIcon
            action={
              <Button size="small" onClick={handleBack}>
                返回列表
              </Button>
            }
          />
        </div>
      </div>
    );
  }

  // 沒有數據
  if (!guide) {
    return (
      <div className="guide-preview-container">
        <TopHeader
          pageTitle="找不到文檔"
          extraActions={extraActions}
        />
        <div className="guide-preview-error">
          <Alert
            message="找不到文檔"
            description="請檢查文檔 ID 是否正確"
            type="warning"
            showIcon
          />
        </div>
      </div>
    );
  }

  // 處理內容
  const processedContent = processContent(guide.content);

  // 正常顯示
  return (
    <div className="guide-preview-container">
      <TopHeader
        pageTitle={guide.title || '文檔預覽'}
        extraActions={extraActions}
      />

      <div className="guide-preview-wrapper">
        <Card className="guide-preview-card">
          {/* 文檔元信息 */}
          {guide.full_category_name && (
            <div className="guide-preview-meta">
              <span className="meta-label">分類：</span>
              <span className="meta-value">{guide.full_category_name}</span>
            </div>
          )}

          {guide.created_at && (
            <div className="guide-preview-meta">
              <span className="meta-label">建立時間：</span>
              <span className="meta-value">
                {new Date(guide.created_at).toLocaleString('zh-TW')}
              </span>
            </div>
          )}

          {/* Markdown 內容 */}
          <div className="guide-preview-content markdown-content">
            <ReactMarkdown {...markdownConfig}>
              {processedContent}
            </ReactMarkdown>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default GuidePreviewPage;
