import React, { useState, useEffect } from 'react';
import { Spin, Modal, Image, message } from 'antd';

/**
 * MessageImages 組件 - 處理聊天消息中的圖片展示
 * @param {string[]} filenames - 圖片檔名列表
 * @param {Function} onImageLoad - 圖片載入回調函數
 */
const MessageImages = ({ filenames, onImageLoad }) => {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadImages = async () => {
      // 檢查檔名有效性
      if (!filenames || !Array.isArray(filenames) || filenames.length === 0) {
        console.log('📊 MessageImages: 無有效檔名列表，跳過載入');
        setLoading(false);
        setImages([]);
        return;
      }

      // 過濾明顯無效的檔名
      const validFilenames = filenames.filter(filename => {
        const isValid = filename && 
          typeof filename === 'string' && 
          filename.length >= 8 && 
          /\.(png|jpg|jpeg|gif|bmp|webp)$/i.test(filename) &&
          !/[\s\n\r,，。()]/.test(filename);
        
        if (!isValid) {
          console.log('⚠️ MessageImages: 過濾無效檔名:', filename);
        }
        
        return isValid;
      });

      if (validFilenames.length === 0) {
        console.log('📊 MessageImages: 沒有有效的圖片檔名');
        setLoading(false);
        setImages([]);
        return;
      }

      try {
        console.log('📊 MessageImages: 開始載入圖片', { 
          originalCount: filenames.length,
          validCount: validFilenames.length,
          validFilenames 
        });
        
        setLoading(true);
        setError(null);
        
        const loadedImages = await onImageLoad(validFilenames);
        
        console.log('📊 MessageImages: 載入結果:', {
          requestedCount: validFilenames.length,
          loadedCount: loadedImages?.length || 0,
          hasData: !!loadedImages
        });
        
        if (loadedImages && Array.isArray(loadedImages) && loadedImages.length > 0) {
          // 過濾掉無效的圖片資料
          const validImages = loadedImages.filter(img => 
            img && (img.data_url || img.image_data) && img.filename
          );
          
          console.log('📊 MessageImages: 有效圖片數量:', validImages.length);
          setImages(validImages);
        } else {
          console.log('📊 MessageImages: 無有效圖片資料');
          setImages([]);
        }
        
      } catch (err) {
        console.error('❌ MessageImages: 圖片載入失敗:', err);
        
        // 根據錯誤類型設置不同的錯誤訊息
        let errorMessage = '載入圖片時發生錯誤';
        if (err.response?.status === 404) {
          errorMessage = '圖片不存在或已被移除';
        } else if (err.response?.status === 403) {
          errorMessage = '沒有權限訪問圖片';
        } else if (err.message?.includes('timeout')) {
          errorMessage = '圖片載入超時';
        }
        
        setError(errorMessage);
        setImages([]);
        
        // 不要顯示錯誤訊息給用戶，只記錄到控制台
        // message.warning(errorMessage);
        
      } finally {
        setLoading(false);
      }
    };

    loadImages();
  }, [filenames, onImageLoad]);

  const showImageModal = (imageData) => {
    Modal.info({
      title: `📸 ${imageData.title || imageData.filename}`,
      width: 800,
      content: (
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <Image
            src={imageData.data_url}
            alt={imageData.title || imageData.filename}
            style={{ maxWidth: '100%', maxHeight: '500px', objectFit: 'contain' }}
            preview={{
              mask: '🔍 點擊放大查看'
            }}
          />
          {imageData.description && (
            <div style={{ marginTop: '16px', color: '#666', fontSize: '14px' }}>
              📝 {imageData.description}
            </div>
          )}
          <div style={{ marginTop: '12px', fontSize: '12px', color: '#999' }}>
            尺寸: {imageData.dimensions_display || '未知'} | 大小: {imageData.size_display || '未知'}
          </div>
        </div>
      ),
      okText: '關閉',
      icon: null
    });
  };

  const showDebugInfo = () => {
    // 顯示最近的除錯資訊
    const debugKeys = Object.keys(sessionStorage).filter(key => 
      key.includes('ai_image_debug_') || key.includes('image_load_debug_')
    ).sort().reverse().slice(0, 2);
    
    if (debugKeys.length > 0) {
      let debugContent = '';
      debugKeys.forEach(key => {
        const data = JSON.parse(sessionStorage.getItem(key) || '{}');
        debugContent += `\n\n=== ${key} ===\n${JSON.stringify(data, null, 2)}`;
      });
      
      Modal.info({
        title: '🐛 圖片載入除錯資訊',
        width: 800,
        content: (
          <pre style={{ 
            whiteSpace: 'pre-wrap', 
            fontSize: '12px', 
            maxHeight: '400px', 
            overflow: 'auto',
            backgroundColor: '#f5f5f5',
            padding: '12px',
            borderRadius: '4px'
          }}>
            {debugContent}
          </pre>
        ),
        okText: '關閉'
      });
    } else {
      message.info('暫無除錯資訊');
    }
  };

  if (loading) {
    return (
      <div style={{ marginTop: '12px', borderTop: '1px solid #f0f0f0', paddingTop: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#666' }}>
          <Spin size="small" />
          <span style={{ fontSize: '12px' }}>正在載入圖片...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ marginTop: '12px', borderTop: '1px solid #f0f0f0', paddingTop: '12px' }}>
        <div style={{ fontSize: '12px', color: '#ff4d4f' }}>
          ❌ {error}
        </div>
        <div style={{ fontSize: '11px', color: '#999', marginTop: '4px' }}>
          請檢查網路連線或聯絡系統管理員
        </div>
      </div>
    );
  }

  if (images.length === 0) {
    // 沒有載入到圖片，顯示檔名連結
    return (
      <div style={{ margin: '8px 0' }}>
        <div style={{ fontSize: '12px', color: '#666', marginBottom: '6px' }}>
          📸 相關圖片 ({filenames.length} 張)：
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {filenames.map((filename, index) => (
            <div 
              key={index} 
              style={{ 
                padding: '6px 10px', 
                backgroundColor: '#f0f0f0', 
                border: '1px solid #d9d9d9',
                borderRadius: '6px',
                fontSize: '12px',
                color: '#666'
              }}
            >
              🖼️ {filename.length > 30 ? filename.substring(0, 30) + '...' : filename}
            </div>
          ))}
        </div>
        <div style={{ fontSize: '11px', color: '#999', marginTop: '8px' }}>
          💡 圖片資料暫時無法載入，請前往知識庫查看
        </div>
      </div>
    );
  }

  // 有成功載入圖片，直接顯示
  console.log('📊 MessageImages: 渲染圖片區域', { imagesLength: images.length, images });
  
  return (
    <div style={{ margin: '8px 0', maxWidth: '200px' }}>
      <div style={{ fontSize: '12px', color: '#666', marginBottom: '6px' }}>
        📸 相關圖片 ({images.length} 張)：
      </div>
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fill, 40px)', 
        gap: '2px',
        justifyContent: 'start'
      }}>
        {images.map((image, index) => (
          <div 
            key={index} 
            style={{
              border: '1px solid #e8e8e8',
              borderRadius: '8px',
              overflow: 'hidden',
              backgroundColor: '#fff',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onClick={() => showImageModal(image)}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            <div style={{ position: 'relative', paddingTop: '60%', overflow: 'hidden' }}>
              <img
                src={image.data_url}
                alt={image.title || image.filename}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover'
                }}
                onLoad={(e) => {
                  console.log('✅ 圖片載入成功:', image.filename);
                }}
                onError={(e) => {
                  console.error('❌ 圖片載入失敗:', image.filename, e);
                  console.log('❌ 失敗的 data_url 開頭:', image.data_url?.substring(0, 100));
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
              <div 
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  display: 'none',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: '#f5f5f5',
                  color: '#999',
                  fontSize: '12px'
                }}
              >
                🖼️ 圖片載入失敗
              </div>
            </div>
            <div style={{ padding: '8px' }}>
              <div style={{ 
                fontSize: '12px', 
                fontWeight: '500',
                color: '#333',
                marginBottom: '4px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                {image.title || image.filename}
              </div>
              {image.description && (
                <div style={{ 
                  fontSize: '11px', 
                  color: '#666',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  {image.description}
                </div>
              )}
              <div style={{ 
                fontSize: '10px', 
                color: '#999',
                marginTop: '4px'
              }}>
                {image.dimensions_display} • {image.size_display}
              </div>
            </div>
          </div>
        ))}
      </div>
      <div style={{ fontSize: '11px', color: '#999', marginTop: '8px', lineHeight: '1.4' }}>
        💡 點擊圖片可放大查看，圖片直接來自知識庫
        <span 
          style={{ 
            marginLeft: '10px', 
            color: '#1890ff', 
            cursor: 'pointer',
            textDecoration: 'underline'
          }}
          onClick={showDebugInfo}
        >
          🐛 除錯
        </span>
      </div>
    </div>
  );
};

export default MessageImages;