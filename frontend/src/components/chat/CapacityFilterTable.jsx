/**
 * CapacityFilterTable - 具有容量過濾功能的測試項目表格
 * 
 * 用於「所有測試項目」區塊，讓用戶可以透過下拉選單篩選特定 Capacity 的資料
 * 
 * 功能：
 * - 下拉選單選擇 Capacity（預設：全部容量）
 * - 根據選擇的 Capacity 動態過濾顯示的資料
 * - 統計數字會根據篩選結果更新
 * - 按 Category 分組顯示（可展開/收合）
 * 
 * @author AI Platform Team
 * @date 2025-12-18
 */

import React, { useState, useMemo } from 'react';
import { Select, Collapse, Table, Tag, Typography, Space, Empty } from 'antd';
import { FolderOutlined, CheckCircleOutlined, CloseCircleOutlined, MinusCircleOutlined } from '@ant-design/icons';

const { Panel } = Collapse;
const { Text } = Typography;

/**
 * 狀態對應的顯示圖標和顏色
 */
const STATUS_CONFIG = {
  'Pass': { icon: <CheckCircleOutlined />, color: '#52c41a', text: '✅' },
  'PASS': { icon: <CheckCircleOutlined />, color: '#52c41a', text: '✅' },
  'Fail': { icon: <CloseCircleOutlined />, color: '#ff4d4f', text: '❌' },
  'FAIL': { icon: <CloseCircleOutlined />, color: '#ff4d4f', text: '❌' },
  'ONGOING': { icon: null, color: '#1890ff', text: '🔄' },
  'CANCEL': { icon: null, color: '#d9d9d9', text: '🚫' },
  'N/A': { icon: <MinusCircleOutlined />, color: '#d9d9d9', text: '➖' },
};

/**
 * 渲染狀態 Cell
 */
const StatusCell = ({ status }) => {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG['N/A'];
  return (
    <span style={{ fontSize: '16px' }}>
      {config.text}
    </span>
  );
};

/**
 * CapacityFilterTable 主組件
 * 
 * @param {Object} props
 * @param {string[]} props.availableCapacities - 可用的 Capacity 列表
 * @param {Object} props.allItemsByCategory - 按 Category 分組的所有測試項目
 * @param {string[]} props.fwVersions - FW 版本列表（用於表格欄位）
 */
const CapacityFilterTable = ({ 
  availableCapacities = [], 
  allItemsByCategory = {},
  fwVersions = []
}) => {
  // 選中的 Capacity（預設：全部）
  const [selectedCapacity, setSelectedCapacity] = useState('all');
  
  // 無意義的狀態（用於過濾）
  const invalidStatuses = new Set(['N/A', 'CANCEL', 'Cancel', '']);
  
  /**
   * 根據選中的 Capacity 過濾資料
   */
  const filteredData = useMemo(() => {
    const result = {};
    
    Object.entries(allItemsByCategory).forEach(([category, items]) => {
      // 過濾出符合 Capacity 條件的項目
      let filteredItems = items;
      
      if (selectedCapacity !== 'all') {
        filteredItems = items.filter(item => item.capacity === selectedCapacity);
      }
      
      // 過濾掉所有 FW 版本都沒有有效結果的項目
      filteredItems = filteredItems.filter(item => {
        const statuses = item.statuses || {};
        return fwVersions.some(fw => !invalidStatuses.has(statuses[fw] || 'N/A'));
      });
      
      if (filteredItems.length > 0) {
        result[category] = filteredItems;
      }
    });
    
    return result;
  }, [allItemsByCategory, selectedCapacity, fwVersions, invalidStatuses]);
  
  /**
   * 計算各 Category 的統計
   */
  const categoryStats = useMemo(() => {
    const stats = {};
    
    Object.entries(filteredData).forEach(([category, items]) => {
      let passCount = 0;
      let failCount = 0;
      
      items.forEach(item => {
        const statuses = item.statuses || {};
        // 只要任一版本有 Pass/Fail，就計入
        const hasPass = fwVersions.some(fw => 
          statuses[fw] === 'Pass' || statuses[fw] === 'PASS'
        );
        const hasFail = fwVersions.some(fw => 
          statuses[fw] === 'Fail' || statuses[fw] === 'FAIL'
        );
        
        // 統計邏輯：如果有 Fail 則 +1 Fail，有 Pass 則 +1 Pass
        if (hasFail) failCount++;
        if (hasPass && !hasFail) passCount++;
      });
      
      stats[category] = {
        total: items.length,
        pass: passCount,
        fail: failCount
      };
    });
    
    return stats;
  }, [filteredData, fwVersions]);
  
  /**
   * 生成表格欄位配置
   */
  const columns = useMemo(() => {
    const cols = [
      {
        title: 'Test Item',
        dataIndex: 'test_item',
        key: 'test_item',
        width: 300,
        ellipsis: true,
        render: (text) => (
          <Text style={{ fontSize: '13px' }} ellipsis={{ tooltip: text }}>
            {text}
          </Text>
        )
      }
    ];
    
    // 只有選擇「全部容量」時才顯示 Capacity 欄位
    if (selectedCapacity === 'all') {
      cols.push({
        title: 'Capacity',
        dataIndex: 'capacity',
        key: 'capacity',
        width: 100,
        render: (text) => <Tag>{text}</Tag>
      });
    }
    
    // 動態添加每個 FW 版本的欄位
    fwVersions.forEach(fw => {
      cols.push({
        title: fw,
        dataIndex: ['statuses', fw],
        key: fw,
        width: 100,
        align: 'center',
        render: (status) => <StatusCell status={status || 'N/A'} />
      });
    });
    
    return cols;
  }, [fwVersions, selectedCapacity]);
  
  /**
   * 渲染 Category Panel Header
   */
  const renderPanelHeader = (category) => {
    const stats = categoryStats[category] || { total: 0, pass: 0, fail: 0 };
    return (
      <Space>
        <FolderOutlined style={{ color: '#faad14' }} />
        <Text strong>{category}</Text>
        <Text type="secondary">
          （{stats.total} 項，
          <Text style={{ color: '#52c41a' }}>✅ {stats.pass}</Text>
          {' / '}
          <Text style={{ color: '#ff4d4f' }}>❌ {stats.fail}</Text>
          ）
        </Text>
      </Space>
    );
  };
  
  // 如果沒有資料
  if (Object.keys(allItemsByCategory).length === 0) {
    return <Empty description="沒有測試項目資料" />;
  }
  
  return (
    <div className="capacity-filter-table">
      {/* 容量篩選下拉選單 */}
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
        <Text strong>📦 容量篩選：</Text>
        <Select
          value={selectedCapacity}
          onChange={setSelectedCapacity}
          style={{ width: 180 }}
          options={[
            { value: 'all', label: '全部容量' },
            ...availableCapacities.map(cap => ({ value: cap, label: cap }))
          ]}
        />
        {selectedCapacity !== 'all' && (
          <Tag color="blue">已篩選：{selectedCapacity}</Tag>
        )}
      </div>
      
      {/* 按 Category 分組的可摺疊表格 */}
      {Object.keys(filteredData).length > 0 ? (
        <Collapse 
          defaultActiveKey={Object.keys(filteredData).slice(0, 2)}
          style={{ background: '#fafafa' }}
        >
          {Object.entries(filteredData)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([category, items]) => (
              <Panel 
                header={renderPanelHeader(category)} 
                key={category}
              >
                <Table
                  columns={columns}
                  dataSource={items.map((item, idx) => ({ 
                    ...item, 
                    key: `${category}-${item.test_item}-${item.capacity}-${idx}` 
                  }))}
                  pagination={false}
                  size="small"
                  scroll={{ x: 'max-content' }}
                  bordered
                />
              </Panel>
            ))}
        </Collapse>
      ) : (
        <Empty description={`沒有 ${selectedCapacity} 的測試資料`} />
      )}
    </div>
  );
};

export default CapacityFilterTable;
