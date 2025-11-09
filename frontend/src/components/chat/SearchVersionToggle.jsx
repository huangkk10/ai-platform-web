import React from 'react';
import { Switch, Tooltip } from 'antd';
import { ExperimentOutlined, RocketOutlined } from '@ant-design/icons';

/**
 * SearchVersionToggle 組件
 * 用於切換搜尋版本（V1/V2）的切換按鈕
 * 
 * @param {string} searchVersion - 當前搜尋版本 ('v1' 或 'v2')
 * @param {Function} onVersionChange - 版本變更回調函數
 * @param {boolean} disabled - 是否禁用（例如：正在載入時）
 */
const SearchVersionToggle = ({ searchVersion, onVersionChange, disabled = false }) => {
  // 切換版本
  const handleToggle = (checked) => {
    const newVersion = checked ? 'v2' : 'v1';
    onVersionChange(newVersion);
  };

  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      gap: '8px',
      padding: '8px 12px',
      background: '#f5f5f5',
      borderRadius: '8px'
    }}>
      {/* V1 圖標 */}
      <Tooltip title="基礎搜尋：快速搜尋，僅返回最相關的段落">
        <RocketOutlined 
          style={{ 
            color: searchVersion === 'v1' ? '#1890ff' : '#999',
            fontSize: '16px'
          }} 
        />
      </Tooltip>
      
      {/* V1 標籤 */}
      <span style={{ 
        color: searchVersion === 'v1' ? '#1890ff' : '#999',
        fontWeight: searchVersion === 'v1' ? 600 : 400,
        fontSize: '13px'
      }}>
        V1
      </span>
      
      {/* 切換開關 */}
      <Switch 
        checked={searchVersion === 'v2'}
        onChange={handleToggle}
        disabled={disabled}
        size="small"
        style={{ margin: '0 4px' }}
      />
      
      {/* V2 標籤 */}
      <span style={{ 
        color: searchVersion === 'v2' ? '#52c41a' : '#999',
        fontWeight: searchVersion === 'v2' ? 600 : 400,
        fontSize: '13px'
      }}>
        V2
      </span>
      
      {/* V2 圖標 */}
      <Tooltip title="上下文增強搜尋：包含前後段落和父子段落，提供更完整的資訊">
        <ExperimentOutlined 
          style={{ 
            color: searchVersion === 'v2' ? '#52c41a' : '#999',
            fontSize: '16px'
          }} 
        />
      </Tooltip>
      
      {/* 版本說明 */}
      <Tooltip 
        title={
          <div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>搜尋版本說明</div>
            <div style={{ marginBottom: 8 }}>
              <strong>V1 - 基礎搜尋</strong><br/>
              • 快速搜尋，僅返回最相關的段落<br/>
              • 適合快速查找特定資訊
            </div>
            <div>
              <strong>V2 - 上下文增強搜尋</strong><br/>
              • 包含前後段落和父子段落<br/>
              • 提供更完整的上下文資訊<br/>
              • 適合需要深入理解的場景
            </div>
          </div>
        }
        placement="bottomRight"
      >
        <span style={{ 
          cursor: 'help',
          color: '#999',
          fontSize: '12px',
          marginLeft: '4px',
          userSelect: 'none'
        }}>
          ⓘ
        </span>
      </Tooltip>
    </div>
  );
};

export default SearchVersionToggle;
