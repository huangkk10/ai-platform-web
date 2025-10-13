import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Image, Spin, message, Space, Tag } from 'antd';
import { 
  PictureOutlined, 
  ExclamationCircleOutlined,
  StarFilled,
  InfoCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';

/**
 * 修復版內容渲染器組件
 * 解決圖片載入的競態條件和重複請求問題
 */
const ContentRenderer = ({ 
  content, 
  showImageTitles = true,
  showImageDescriptions = true, 
  imageMaxWidth = 400,
  imageMaxHeight = 300,
  className = '',
  style = {}
}) => {
  const [imageCache, setImageCache] = useState(new Map());
  const [loadingImages, setLoadingImages] = useState(new Set());
  const [failedImages, setFailedImages] = useState(new Set());
  
  // 🔧 修復1: 使用 useRef 追蹤正在進行的請求，避免重複請求
  const loadingPromises = useRef(new Map());
  
  // 🔧 修復2: 使用 useRef 追蹤組件是否已掛載，避免在卸載後更新狀態
  const isMountedRef = useRef(true);
  
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      // 清理所有進行中的請求 Promise
      loadingPromises.current.clear();
    };
  }, []);

  // 圖片標記正則表達式
  const IMAGE_REGEX = {
    withId: /🖼️\s*\[IMG:(\d+)\]\s*(.+?)(?:\s+\(([^)]+)\))?(?=\n|$)/g,
    markdown: /\[IMG:(\d+)\](?:\s*([^\s，。,\n]+?))?(?:\s*\(([^)]+)\))?(?=[\s，。,\n]|$)/g,
    legacy: /🖼️\s*([^\(\n\[]+?)(?:\s*\(([^)]+)\))?(?=\n|$)/g
  };

  // 解析圖片標記資訊
  const parseImageInfo = useCallback((infoText) => {
    if (!infoText) return {};
    
    const info = {
      title: null,
      description: null,
      isPrimary: false
    };

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
  }, []);

  // 🔧 修復3: 改良的圖片載入函數，加強防重複機制和錯誤處理
  const loadImageById = useCallback(async (imageId) => {
    console.log(`ContentRenderer: 嘗試載入圖片 ID ${imageId}`);
    
    // 檢查快取
    if (imageCache.has(imageId)) {
      console.log(`ContentRenderer: 圖片 ID ${imageId} 已存在快取`);
      return imageCache.get(imageId);
    }

    // 檢查是否正在載入 - 如果是，等待現有的 Promise
    if (loadingPromises.current.has(imageId)) {
      console.log(`ContentRenderer: 圖片 ID ${imageId} 正在載入中，等待現有請求`);
      return loadingPromises.current.get(imageId);
    }

    // 創建新的載入 Promise
    const loadPromise = (async () => {
      if (!isMountedRef.current) return null;
      
      setLoadingImages(prev => new Set(prev).add(imageId));

      try {
        console.log(`ContentRenderer: 發送 API 請求載入圖片 ID ${imageId}`);
        const response = await axios.get(`/api/content-images/${imageId}/`, {
          withCredentials: true,
          timeout: 10000 // 🔧 增加超時設定
        });
        
        if (!isMountedRef.current) return null;
        
        const imageData = response.data;
        
        console.log(`ContentRenderer: 成功載入圖片 ID ${imageId}，資料:`, {
          id: imageData.id,
          filename: imageData.filename,
          hasImageData: !!imageData.image_data,
          hasDataUrl: !!imageData.data_url,
          contentType: imageData.content_type_mime
        });
        
        // 確保有 data URL
        if (imageData.data_url) {
          console.log(`ContentRenderer: 使用現有 data URL，長度: ${imageData.data_url.length}`);
        } else if (imageData.image_data) {
          imageData.data_url = `data:${imageData.content_type_mime};base64,${imageData.image_data}`;
          console.log(`ContentRenderer: 生成 data URL 成功，長度: ${imageData.data_url.length}`);
        } else {
          console.error(`ContentRenderer: 圖片 ${imageId} 沒有可用的圖片資料`);
          throw new Error('No image data available');
        }
        
        // 🔧 修復4: 確保狀態更新在組件掛載時才執行
        if (isMountedRef.current) {
          setImageCache(prev => new Map(prev).set(imageId, imageData));
          setFailedImages(prev => {
            const newSet = new Set(prev);
            newSet.delete(imageId); // 移除失敗標記（如果有）
            return newSet;
          });
        }
        
        return imageData;
        
      } catch (error) {
        if (!isMountedRef.current) return null;
        
        console.error(`ContentRenderer: 載入圖片 ${imageId} 失敗:`, error);
        
        setFailedImages(prev => new Set(prev).add(imageId));
        message.warning(`圖片載入失敗 (ID: ${imageId}): ${error.message}`);
        return null;
        
      } finally {
        if (isMountedRef.current) {
          setLoadingImages(prev => {
            const newSet = new Set(prev);
            newSet.delete(imageId);
            return newSet;
          });
        }
        // 清理 Promise 參考
        loadingPromises.current.delete(imageId);
      }
    })();

    // 儲存 Promise 參考
    loadingPromises.current.set(imageId, loadPromise);
    return loadPromise;
  }, [imageCache]); // 🔧 添加依賴

  // 🔧 修復5: 使用 useMemo 來解析圖片標記，避免重複計算
  const parsedImages = useMemo(() => {
    if (!content) return [];

    console.log('ContentRenderer: 開始解析內容中的圖片標記');
    console.log('ContentRenderer: 內容長度:', content.length);
    console.log('ContentRenderer: 內容片段:', content.substring(0, 200));

    const allMatches = [];

    // 收集新格式匹配
    const withIdMatches = [...content.matchAll(IMAGE_REGEX.withId)];
    for (const match of withIdMatches) {
      allMatches.push({
        type: 'withId',
        match,
        index: match.index,
        imageId: match[1],
        filename: match[2] ? match[2].trim() : '',
        infoText: match[3]
      });
    }

    // 收集Markdown格式匹配
    const markdownMatches = [...content.matchAll(IMAGE_REGEX.markdown)];
    for (const match of markdownMatches) {
      // 避免與 withId 格式重複
      const isDuplicate = allMatches.some(existing => 
        Math.abs(existing.index - match.index) < 10
      );
      
      if (!isDuplicate) {
        allMatches.push({
          type: 'markdown',
          match,
          index: match.index,
          imageId: match[1],
          filename: match[2] ? match[2].trim() : '',
          infoText: match[3]
        });
      }
    }

    // 收集舊格式匹配
    const legacyMatches = [...content.matchAll(IMAGE_REGEX.legacy)];
    for (const match of legacyMatches) {
      const isDuplicate = allMatches.some(existing => 
        Math.abs(existing.index - match.index) < 50
      );
      
      if (!isDuplicate) {
        allMatches.push({
          type: 'legacy',
          match,
          index: match.index,
          filename: match[1] ? match[1].trim() : '',
          infoText: match[2]
        });
      }
    }

    allMatches.sort((a, b) => a.index - b.index);
    
    console.log(`ContentRenderer: 解析完成，找到 ${allMatches.length} 個圖片標記`);
    return allMatches;
  }, [content]);

  // 🔧 修復6: 優化的預載入邏輯，避免重複載入
  useEffect(() => {
    if (!parsedImages.length) return;

    console.log(`ContentRenderer: 開始預載入 ${parsedImages.length} 個圖片`);
    
    // 只載入有 ID 的圖片
    const imageIds = parsedImages
      .filter(item => item.imageId && (item.type === 'withId' || item.type === 'markdown'))
      .map(item => item.imageId);
    
    // 去重
    const uniqueImageIds = [...new Set(imageIds)];
    
    console.log(`ContentRenderer: 需要載入的唯一圖片 IDs:`, uniqueImageIds);
    
    uniqueImageIds.forEach(imageId => {
      if (!imageCache.has(imageId) && 
          !loadingPromises.current.has(imageId) && 
          !failedImages.has(imageId)) {
        console.log(`ContentRenderer: 開始預載入圖片 ID ${imageId}`);
        loadImageById(imageId).catch(error => {
          console.warn(`預載入圖片 ${imageId} 失敗:`, error);
        });
      } else {
        console.log(`ContentRenderer: 跳過圖片 ID ${imageId}，已存在或載入中`);
      }
    });
  }, [parsedImages, imageCache, failedImages, loadImageById]);

  // 渲染單個圖片組件
  const renderImage = useCallback((imageData, info, imageId = null) => {
    const displayTitle = info.title || imageData?.title || imageData?.filename || '未知圖片';
    const displayDescription = info.description || imageData?.description;

    // 🔧 修復7: 改善圖片渲染邏輯，更好的載入狀態處理
    const isLoading = loadingImages.has(imageId) || loadingPromises.current.has(imageId);
    const hasFailed = failedImages.has(imageId);
    const hasData = imageData?.data_url;

    console.log(`ContentRenderer: 渲染圖片 ID ${imageId}:`, {
      isLoading,
      hasFailed, 
      hasData: !!hasData,
      imageDataExists: !!imageData
    });

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
              {isLoading && (
                <Tag color="orange" size="small">
                  載入中
                </Tag>
              )}
            </Space>
          </div>
        )}

        <div style={{ padding: '12px', textAlign: 'center' }}>
          {hasData ? (
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
              onError={() => {
                console.error(`圖片渲染失敗: ID ${imageId}`);
                setFailedImages(prev => new Set(prev).add(imageId));
              }}
            />
          ) : hasFailed ? (
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
  }, [imageMaxWidth, imageMaxHeight, showImageTitles, showImageDescriptions, loadingImages, failedImages]);

  // 渲染內容
  const renderContent = useCallback(() => {
    if (!content) {
      return <div style={{ color: '#999', fontStyle: 'italic' }}>無內容</div>;
    }

    if (!parsedImages.length) {
      return (
        <div style={{ 
          whiteSpace: 'pre-wrap',
          lineHeight: '1.6'
        }}>
          {content}
        </div>
      );
    }

    const elements = [];
    let currentIndex = 0;
    
    for (let i = 0; i < parsedImages.length; i++) {
      const { type, match, index, imageId, filename, infoText } = parsedImages[i];
      
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

      const info = parseImageInfo(infoText);

      if (type === 'withId' || type === 'markdown') {
        const imageData = imageCache.get(imageId);
        elements.push(renderImage(imageData, info, imageId));
      } else {
        // 舊格式處理
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

    return elements;
  }, [content, parsedImages, imageCache, parseImageInfo, renderImage]);

  const contentElements = renderContent();

  return (
    <div className={`content-renderer ${className}`} style={style}>
      {contentElements}
    </div>
  );
};

export default ContentRenderer;