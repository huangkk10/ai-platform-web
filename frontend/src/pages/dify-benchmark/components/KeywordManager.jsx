import React, { useState } from 'react';
import { Input, Button, Tag, Space } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';

const KeywordManager = ({ keywords = [], onChange }) => {
  const [keywordInput, setKeywordInput] = useState('');

  // 添加關鍵字
  const handleAddKeyword = () => {
    const trimmed = keywordInput.trim();
    if (trimmed && !keywords.includes(trimmed)) {
      onChange([...keywords, trimmed]);
      setKeywordInput('');
    }
  };

  // 移除關鍵字
  const handleRemoveKeyword = (keyword) => {
    onChange(keywords.filter(k => k !== keyword));
  };

  // 清空所有關鍵字
  const handleClearAll = () => {
    onChange([]);
  };

  return (
    <div style={{ marginBottom: '24px' }}>
      <label style={{ 
        display: 'block', 
        marginBottom: '8px',
        fontWeight: 500,
        fontSize: '14px'
      }}>
        <span style={{ color: 'red' }}>* </span>
        答案關鍵字
      </label>

      {/* 輸入區域 */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
        <Input
          size="large"
          value={keywordInput}
          onChange={(e) => setKeywordInput(e.target.value)}
          onPressEnter={handleAddKeyword}
          placeholder="輸入關鍵字後按 Enter 或點擊添加..."
          style={{ flex: 1 }}
        />
        <Button 
          type="primary" 
          size="large"
          icon={<PlusOutlined />} 
          onClick={handleAddKeyword}
        >
          添加
        </Button>
      </div>

      {/* 關鍵字展示區域 */}
      <div style={{ 
        padding: '16px', 
        background: '#fafafa', 
        borderRadius: '8px',
        border: '1px solid #d9d9d9',
        minHeight: '100px'
      }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: keywords.length > 0 ? '12px' : '0'
        }}>
          <span style={{ color: '#666', fontSize: '14px' }}>
            已添加的關鍵字 ({keywords.length})
          </span>
          {keywords.length > 0 && (
            <Button 
              type="link" 
              danger 
              size="small"
              onClick={handleClearAll}
              icon={<DeleteOutlined />}
            >
              清空全部
            </Button>
          )}
        </div>

        {keywords.length > 0 ? (
          <Space size={[8, 8]} wrap>
            {keywords.map((keyword, index) => (
              <Tag 
                key={index} 
                closable 
                onClose={() => handleRemoveKeyword(keyword)}
                color="purple"
                style={{ 
                  fontSize: '14px', 
                  padding: '8px 12px',
                }}
              >
                {keyword}
              </Tag>
            ))}
          </Space>
        ) : (
          <div style={{ 
            textAlign: 'center', 
            color: '#bfbfbf',
            padding: '24px 0',
            fontSize: '14px'
          }}>
            尚未添加關鍵字
          </div>
        )}
      </div>

      {/* 提示文字 */}
      <div style={{ 
        marginTop: '8px', 
        color: '#8c8c8c', 
        fontSize: '12px'
      }}>
        💡 提示：輸入關鍵字後按 <Tag style={{ margin: '0 4px' }}>Enter</Tag> 也可快速添加
      </div>
    </div>
  );
};

export default KeywordManager;
