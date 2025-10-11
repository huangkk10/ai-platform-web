import React, { useState, useEffect } from 'react';
import { Image, Spin, message, Space, Tag } from 'antd';
import { 
  PictureOutlined, 
  ExclamationCircleOutlined,
  StarFilled,
  InfoCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';

/**
 * 內容渲染器組件
 * 解析文字內容中的圖片標記並渲染為實際圖片
 * 
 * 支援的圖片標記格式：
 * - 🖼️ [IMG:123] filename.jpg (標題: xxx, 說明: xxx)
 * - 🖼️ filename.jpg (舊格式，向後兼容)
 */
const ContentRenderer = ({ 
  content, 
  showImageTitles = true,     // 是否顯示圖片標題
  showImageDescriptions = true, // 是否顯示圖片描述
  imageMaxWidth = 400,        // 圖片最大寬度
  imageMaxHeight = 300,       // 圖片最大高度
  className = '',
  style = {}
}) => {
  const [imageCache, setImageCache] = useState(new Map()); // 圖片快取
  const [loadingImages, setLoadingImages] = useState(new Set()); // 載入中的圖片
  const [failedImages, setFailedImages] = useState(new Set()); // 載入失敗的圖片

  // 圖片標記正則表達式
  const IMAGE_REGEX = {
    // 新格式：🖼️ [IMG:123] filename.jpg (標題: xxx, 說明: xxx, 📌 主要圖片)
    withId: /🖼️\s*\[IMG:(\d+)\]\s*(.+?)(?:\s+\(([^)]+)\))?(?=\n|$)/g,
    // Markdown格式：**[IMG:123] filename.jpg** 或直接 [IMG:123] filename.jpg
    markdown: /\[IMG:(\d+)\](?:\s*([^\n\*\(]+?))?(?:\s*\(([^)]+)\))?/g,
    // 舊格式：🖼️ filename.jpg (標題: xxx, 說明: xxx)
    legacy: /🖼️\s*([^\(\n\[]+?)(?:\s*\(([^)]+)\))?(?=\n|$)/g
  };

  // 解析圖片標記資訊 (括號內的內容)
  const parseImageInfo = (infoText) => {
    if (!infoText) return {};
    
    const info = {
      title: null,
      description: null,
      isPrimary: false
    };

    // 解析各種資訊
    const titleMatch = infoText.match(/標題:\s*([^,]+)/);
    if (titleMatch) {
      info.title = titleMatch[1].trim();
    }

    const descMatch = infoText.match(/說明:\s*([^,]+)/);
    if (descMatch) {
      info.description = descMatch[1].trim();
    }

    if (infoText.includes('📌 主要圖片')) {
      info.isPrimary = true;
    }

    return info;
  };

  // 從後端載入圖片資料
  const loadImageById = async (imageId) => {
    console.log(`ContentRenderer: 嘗試載入圖片 ID ${imageId}`);
    
    if (imageCache.has(imageId) || loadingImages.has(imageId)) {
      console.log(`ContentRenderer: 圖片 ID ${imageId} 已存在快取或正在載入中`);
      return imageCache.get(imageId);
    }

    setLoadingImages(prev => new Set(prev).add(imageId));

    try {
      console.log(`ContentRenderer: 發送 API 請求載入圖片 ID ${imageId}`);
      const response = await axios.get(`/api/content-images/${imageId}/`, {
        withCredentials: true
      });
      const imageData = response.data;
      
      console.log(`ContentRenderer: 成功載入圖片 ID ${imageId}，資料:`, {
        id: imageData.id,
        filename: imageData.filename,
        hasImageData: !!imageData.image_data,
        contentType: imageData.content_type_mime
      });
      
      // 檢查並生成 data URL
      if (imageData.data_url) {
        console.log(`ContentRenderer: 使用現有 data URL，長度: ${imageData.data_url.length}`);
      } else if (imageData.image_data) {
        imageData.data_url = `data:${imageData.content_type_mime};base64,${imageData.image_data}`;
        console.log(`ContentRenderer: 生成 data URL 成功，長度: ${imageData.data_url.length}`);
      } else {
        console.error(`ContentRenderer: 圖片 ${imageId} 沒有可用的圖片資料`);
        throw new Error('No image data available');
      }
      
      setImageCache(prev => new Map(prev).set(imageId, imageData));
      return imageData;
    } catch (error) {
      console.error(`ContentRenderer: 載入圖片 ${imageId} 失敗:`, error);
      setFailedImages(prev => new Set(prev).add(imageId));
      message.warning(`圖片載入失敗 (ID: ${imageId})`);
      return null;
    } finally {
      setLoadingImages(prev => {
        const newSet = new Set(prev);
        newSet.delete(imageId);
        return newSet;
      });
    }
  };

  // 渲染單個圖片組件
  const renderImage = (imageData, info, imageId = null) => {
    const displayTitle = info.title || imageData?.title || imageData?.filename || '未知圖片';
    const displayDescription = info.description || imageData?.description;

    return (
      <div 
        key={imageId || displayTitle}
        style={{ 
          margin: '16px 0',
          border: '1px solid #f0f0f0',
          borderRadius: '8px',
          overflow: 'hidden',
          backgroundColor: '#fafafa'
        }}
      >
        {/* 圖片標題列 */}
        {showImageTitles && (
          <div style={{
            padding: '8px 12px',
            backgroundColor: '#f8f9fa',
            borderBottom: '1px solid #e9ecef',
            fontSize: '14px'
          }}>
            <Space>
              <PictureOutlined style={{ color: '#1890ff' }} />
              <span style={{ fontWeight: 500 }}>{displayTitle}</span>
              {info.isPrimary && (
                <Tag color="gold" icon={<StarFilled />} size="small">
                  主要圖片
                </Tag>
              )}
              {imageId && (
                <Tag color="blue" size="small">
                  ID: {imageId}
                </Tag>
              )}
            </Space>
          </div>
        )}

        {/* 圖片內容 */}
        <div style={{ padding: '12px', textAlign: 'center' }}>
          {imageData?.data_url ? (
            <Image
              src={imageData.data_url}
              alt={displayTitle}
              style={{ 
                maxWidth: imageMaxWidth,
                maxHeight: imageMaxHeight,
                objectFit: 'contain'
              }}
              preview={{
                mask: <span>點擊預覽</span>
              }}
            />
          ) : failedImages.has(imageId) ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100px',
              color: '#ff4d4f',
              backgroundColor: '#fff2f0',
              border: '1px dashed #ffccc7',
              borderRadius: '4px'
            }}>
              <Space>
                <ExclamationCircleOutlined />
                <span>圖片載入失敗</span>
                {imageId && <span>(ID: {imageId})</span>}
              </Space>
            </div>
          ) : (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100px'
            }}>
              <Spin size="large" />
              <span style={{ marginLeft: 8 }}>載入中...</span>
            </div>
          )}
        </div>

        {/* 圖片描述 */}
        {showImageDescriptions && displayDescription && (
          <div style={{
            padding: '8px 12px',
            backgroundColor: '#f8f9fa',
            borderTop: '1px solid #e9ecef',
            fontSize: '13px',
            color: '#666'
          }}>
            <Space>
              <InfoCircleOutlined style={{ color: '#1890ff' }} />
              <span>{displayDescription}</span>
            </Space>
          </div>
        )}
      </div>
    );
  };

  // 使用 useEffect 來預載入所有圖片
  useEffect(() => {
    if (!content) {
      console.log('ContentRenderer: 沒有內容，跳過圖片載入');
      return;
    }

    console.log('ContentRenderer: 開始解析內容中的圖片標記');
    console.log('ContentRenderer: 內容長度:', content.length);
    console.log('ContentRenderer: 內容片段:', content.substring(0, 500));

    
    // 先檢查內容中是否包含 IMG: 標記
    const imgMatches = content.match(/IMG:\d+/g);

    const withIdMatches = [...content.matchAll(IMAGE_REGEX.withId)];
    const markdownMatches = [...content.matchAll(IMAGE_REGEX.markdown)];
    const allMatches = [...withIdMatches, ...markdownMatches];
    console.log(`ContentRenderer: 正規表達式匹配到 ${withIdMatches.length} 個標準格式, ${markdownMatches.length} 個Markdown格式, 總共 ${allMatches.length} 個圖片標記`);
    
    // 打印所有匹配的詳細信息
    allMatches.forEach((match, index) => {
      console.log(`ContentRenderer: 匹配 ${index + 1}:`, {
        fullMatch: match[0],
        imageId: match[1],
        filename: match[2],
        metadata: match[3]
      });
    });
    
    // 預載入所有圖片
    allMatches.forEach((match, index) => {
      const imageId = match[1];
      console.log(`ContentRenderer: 處理第 ${index + 1} 個圖片，ID: ${imageId}`);
      
      if (!imageCache.has(imageId) && !loadingImages.has(imageId) && !failedImages.has(imageId)) {
        console.log(`ContentRenderer: 開始載入圖片 ID ${imageId}`);
        loadImageById(imageId);
      } else {
        console.log(`ContentRenderer: 跳過圖片 ID ${imageId}，原因: 快取中已存在或正在載入或載入失敗`);
      }
    });
  }, [content]); // eslint-disable-line react-hooks/exhaustive-deps

  // 渲染內容
  const renderContent = () => {
    if (!content) {
      return <div style={{ color: '#999', fontStyle: 'italic' }}>無內容</div>;
    }

    const elements = [];
    let matchFound = false;

    // 先處理新格式 (帶 ID)
    const withIdMatches = [...content.matchAll(IMAGE_REGEX.withId)];
    const markdownMatches = [...content.matchAll(IMAGE_REGEX.markdown)];
    
    // 收集所有匹配
    const allMatches = [];

    // 收集新格式匹配
    for (const match of withIdMatches) {
      allMatches.push({
        type: 'withId',
        match,
        index: match.index,
        imageId: match[1],
        filename: match[2].trim(),
        infoText: match[3]
      });
    }

    // 收集Markdown格式匹配
    for (const match of markdownMatches) {
      allMatches.push({
        type: 'markdown',
        match,
        index: match.index,
        imageId: match[1],
        filename: match[2] ? match[2].trim() : '',
        infoText: match[3]
      });
    }

    // 收集舊格式匹配 (避免與新格式重複)
    const legacyMatches = [...content.matchAll(IMAGE_REGEX.legacy)];
    for (const match of legacyMatches) {
      // 檢查是否與新格式匹配重疊
      const isOverlap = withIdMatches.some(newMatch => 
        Math.abs(match.index - newMatch.index) < 50
      );
      
      if (!isOverlap) {
        allMatches.push({
          type: 'legacy',
          match,
          index: match.index,
          filename: match[1].trim(),
          infoText: match[2]
        });
      }
    }

    // 按位置排序
    allMatches.sort((a, b) => a.index - b.index);

    // 渲染內容
    let currentIndex = 0;
    
    for (let i = 0; i < allMatches.length; i++) {
      const { type, match, index, imageId, filename, infoText } = allMatches[i];
      
      // 添加匹配前的文字
      if (index > currentIndex) {
        const textBefore = content.substring(currentIndex, index);
        if (textBefore.trim()) {
          elements.push(
            <div 
              key={`text-${currentIndex}`} 
              style={{ 
                whiteSpace: 'pre-wrap', 
                marginBottom: '8px',
                lineHeight: '1.6'
              }}
            >
              {textBefore}
            </div>
          );
        }
      }

      // 解析圖片資訊
      const info = parseImageInfo(infoText);

      if (type === 'withId' || type === 'markdown') {
        // 新格式或Markdown格式：根據 ID 載入圖片
        const imageData = imageCache.get(imageId);
        console.log(`ContentRenderer: 渲染圖片 ID ${imageId}, imageData:`, imageData ? '存在' : '不存在');
        elements.push(renderImage(imageData, info, imageId));
      } else {
        // 舊格式：僅顯示檔案名稱和資訊
        elements.push(
          <div 
            key={`legacy-${index}`}
            style={{
              margin: '16px 0',
              padding: '12px',
              backgroundColor: '#fff7e6',
              border: '1px solid #ffd591',
              borderRadius: '6px'
            }}
          >
            <Space>
              <PictureOutlined style={{ color: '#fa8c16' }} />
              <span style={{ fontWeight: 500 }}>{filename}</span>
              <Tag color="orange" size="small">舊格式</Tag>
            </Space>
            {info.title && (
              <div style={{ marginTop: '4px', fontSize: '13px', color: '#666' }}>
                標題: {info.title}
              </div>
            )}
            {info.description && (
              <div style={{ marginTop: '2px', fontSize: '13px', color: '#666' }}>
                說明: {info.description}
              </div>
            )}
          </div>
        );
      }

      currentIndex = index + match[0].length;
      matchFound = true;
    }

    // 添加最後一段文字
    if (currentIndex < content.length) {
      const textAfter = content.substring(currentIndex);
      if (textAfter.trim()) {
        elements.push(
          <div 
            key={`text-${currentIndex}`}
            style={{ 
              whiteSpace: 'pre-wrap',
              lineHeight: '1.6'
            }}
          >
            {textAfter}
          </div>
        );
      }
    }

    // 如果沒有找到任何圖片標記，顯示原始內容
    if (!matchFound) {
      elements.push(
        <div 
          key="original-content" 
          style={{ 
            whiteSpace: 'pre-wrap',
            lineHeight: '1.6'
          }}
        >
          {content}
        </div>
      );
    }

    return elements;
  };

  const content_elements = renderContent();

  return (
    <div className={`content-renderer ${className}`} style={style}>
      {content_elements.length > 0 ? content_elements : (
        <div style={{ 
          whiteSpace: 'pre-wrap',
          lineHeight: '1.6'
        }}>
          {content}
        </div>
      )}
    </div>
  );
};

export default ContentRenderer;