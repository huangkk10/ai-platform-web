/**
 * 系統日誌查看器頁面
 * 
 * 功能：
 * - 列出所有日誌檔案
 * - 查看日誌內容
 * - 過濾和搜尋
 * - 下載日誌
 * - 顯示統計資訊
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Layout, Card, List, Button, Space, Input,
  Statistic, Tag, Progress, Divider, message, Dropdown, Menu, Switch, Badge, Typography, Spin, Pagination
} from 'antd';
import {
  ReloadOutlined, DownloadOutlined, SearchOutlined, FilterOutlined,
  FileTextOutlined, InfoCircleOutlined
} from '@ant-design/icons';
import { useLogViewer } from '../../hooks/useLogViewer';
import LogContentViewer from '../../components/LogViewer/LogContentViewer';
import './SystemLogViewerPage.css';

const { Sider, Content } = Layout;
const { Text } = Typography;

const SystemLogViewerPage = () => {
  const {
    logFiles,
    selectedFile,
    logContent,
    logStats,
    loading,
    filesLoading,
    filters,
    handleFileSelect,
    updateFilters,
    refresh,
    downloadLog
  } = useLogViewer();

  const [autoRefresh, setAutoRefresh] = useState(false);
  const [searchInput, setSearchInput] = useState('');
  
  // 分頁狀態
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(100);  // 預設每頁 100 行
  
  // 計算分頁後的日誌內容
  const paginatedContent = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return logContent.slice(startIndex, endIndex);
  }, [logContent, currentPage, pageSize]);
  
  // 當日誌內容改變時，重置到第一頁
  useEffect(() => {
    setCurrentPage(1);
  }, [logContent]);

  // 處理搜尋
  const handleSearch = () => {
    if (!searchInput.trim()) {
      message.warning('請輸入搜尋關鍵字');
      return;
    }
    updateFilters({ search: searchInput });
  };

  // 清除搜尋
  const handleClearSearch = () => {
    setSearchInput('');
    updateFilters({ search: null });
  };

  // 處理下載
  const handleDownload = (format) => {
    downloadLog(format);
  };

  // 過濾器選單
  const filterMenu = (
    <Menu>
      <Menu.ItemGroup title="日誌等級">
        <Menu.Item key="all" onClick={() => updateFilters({ level: null })}>
          全部
        </Menu.Item>
        <Menu.Item key="info" onClick={() => updateFilters({ level: 'INFO' })}>
          INFO
        </Menu.Item>
        <Menu.Item key="warning" onClick={() => updateFilters({ level: 'WARNING' })}>
          WARNING
        </Menu.Item>
        <Menu.Item key="error" onClick={() => updateFilters({ level: 'ERROR' })}>
          ERROR
        </Menu.Item>
        <Menu.Item key="critical" onClick={() => updateFilters({ level: 'CRITICAL' })}>
          CRITICAL
        </Menu.Item>
      </Menu.ItemGroup>
    </Menu>
  );

  // 下載選單
  const downloadMenu = (
    <Menu>
      <Menu.Item key="txt" onClick={() => handleDownload('txt')}>
        下載為 TXT
      </Menu.Item>
      <Menu.Item key="json" onClick={() => handleDownload('json')}>
        下載為 JSON
      </Menu.Item>
    </Menu>
  );

  // 計算錯誤百分比
  const getErrorPercentage = () => {
    if (!logStats || !logStats.level_distribution) return 0;
    const total = Object.values(logStats.level_distribution).reduce((sum, val) => sum + val, 0);
    const errors = (logStats.level_distribution.ERROR || 0) + (logStats.level_distribution.CRITICAL || 0);
    return total > 0 ? (errors / total * 100).toFixed(1) : 0;
  };

  return (
    <Layout className="system-log-viewer-page">
      {/* 左側：日誌檔案列表 */}
      <Sider width={300} theme="light" className="log-sider">
        <Card
          title={
            <Space>
              <FileTextOutlined />
              <span>日誌檔案</span>
              {filesLoading && <Spin size="small" />}
            </Space>
          }
          size="small"
          className="log-files-card"
        >
          <List
            dataSource={logFiles}
            loading={filesLoading}
            renderItem={(file) => (
              <List.Item
                className={selectedFile === file.name ? 'selected-file' : ''}
                onClick={() => handleFileSelect(file.name)}
                style={{ cursor: 'pointer', padding: '12px' }}
              >
                <List.Item.Meta
                  avatar={
                    <FileTextOutlined 
                      style={{ 
                        fontSize: '24px', 
                        color: file.type === 'error' ? '#ff4d4f' : '#1890ff' 
                      }} 
                    />
                  }
                  title={
                    <Space>
                      <Text strong>{file.name}</Text>
                      {file.type === 'error' && <Badge status="error" />}
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size={0}>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {file.size_human}
                      </Text>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {file.line_count} 行
                      </Text>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        </Card>

        {/* 統計資訊卡片 */}
        {logStats && (
          <Card
            title={
              <Space>
                <InfoCircleOutlined />
                <span>統計資訊</span>
              </Space>
            }
            size="small"
            style={{ marginTop: 16 }}
          >
            <Space direction="vertical" style={{ width: '100%' }} size={12}>
              <Statistic
                title="總行數"
                value={logStats.total_lines}
                prefix={<FileTextOutlined />}
              />

              <Divider style={{ margin: '8px 0' }} />

              <div>
                <Text type="secondary">錯誤率</Text>
                <Progress
                  percent={parseFloat(getErrorPercentage())}
                  status={getErrorPercentage() > 5 ? 'exception' : 'normal'}
                  format={(percent) => `${percent}%`}
                />
              </div>

              <div>
                <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                  日誌等級分佈
                </Text>
                <Space wrap size={[8, 8]}>
                  {logStats.level_distribution && Object.entries(logStats.level_distribution).map(([level, count]) => (
                    count > 0 && (
                      <Tag
                        key={level}
                        color={
                          level === 'ERROR' || level === 'CRITICAL' ? 'error' :
                          level === 'WARNING' ? 'warning' :
                          level === 'INFO' ? 'success' : 'default'
                        }
                      >
                        {level}: {count}
                      </Tag>
                    )
                  ))}
                </Space>
              </div>

              <Divider style={{ margin: '8px 0' }} />

              <div>
                <Space direction="vertical" size={4} style={{ width: '100%' }}>
                  <div>
                    <Text type="secondary">檔案大小</Text>
                    <div>{logStats.file_size}</div>
                  </div>
                  <div>
                    <Text type="secondary">最後更新</Text>
                    <div style={{ fontSize: '12px' }}>
                      {new Date(logStats.last_modified).toLocaleString('zh-TW')}
                    </div>
                  </div>
                </Space>
              </div>
            </Space>
          </Card>
        )}
      </Sider>

      {/* 主內容區：日誌查看器 */}
      <Content style={{ padding: '16px', background: '#f0f2f5' }}>
        {/* 工具列 */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <Space wrap style={{ width: '100%' }}>
            {/* 搜尋框 */}
            <Input.Search
              placeholder="搜尋日誌內容..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onSearch={handleSearch}
              style={{ width: 300 }}
              enterButton={<SearchOutlined />}
              allowClear
              onClear={handleClearSearch}
            />

            {/* 過濾器 */}
            <Dropdown overlay={filterMenu} trigger={['click']}>
              <Button icon={<FilterOutlined />}>
                過濾器
                {filters.level && <Badge dot />}
              </Button>
            </Dropdown>

            {/* 下載按鈕 */}
            <Dropdown overlay={downloadMenu} trigger={['click']}>
              <Button icon={<DownloadOutlined />}>
                下載
              </Button>
            </Dropdown>

            {/* 重新整理 */}
            <Button
              icon={<ReloadOutlined />}
              onClick={refresh}
              loading={loading}
            >
              重新整理
            </Button>

            {/* 自動更新開關 */}
            <Switch
              checkedChildren="自動更新"
              unCheckedChildren="手動更新"
              checked={autoRefresh}
              onChange={setAutoRefresh}
            />

            {/* 顯示當前過濾條件 */}
            <div style={{ marginLeft: 'auto' }}>
              <Space>
                {filters.level && (
                  <Tag closable onClose={() => updateFilters({ level: null })}>
                    等級: {filters.level}
                  </Tag>
                )}
                {filters.search && (
                  <Tag closable onClose={() => updateFilters({ search: null })}>
                    搜尋: {filters.search}
                  </Tag>
                )}
              </Space>
            </div>
          </Space>
        </Card>

        {/* 日誌內容 */}
        <Card
          title={
            <Space>
              <FileTextOutlined />
              <span>{selectedFile || '請選擇日誌檔案'}</span>
              {loading && <Spin size="small" />}
            </Space>
          }
          size="small"
        >
          <LogContentViewer
            content={paginatedContent}
            loading={loading}
            searchKeyword={filters.search}
          />
          
          {/* 分頁組件 */}
          {logContent.length > 0 && (
            <div style={{ 
              marginTop: '16px', 
              padding: '16px', 
              background: '#f5f5f5',
              borderRadius: '4px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <Space>
                <Text type="secondary">
                  共 {logContent.length} 行，顯示第 {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, logContent.length)} 行
                </Text>
              </Space>
              
              <Pagination
                current={currentPage}
                pageSize={pageSize}
                total={logContent.length}
                onChange={(page, newPageSize) => {
                  setCurrentPage(page);
                  if (newPageSize !== pageSize) {
                    setPageSize(newPageSize);
                  }
                }}
                onShowSizeChange={(current, size) => {
                  setCurrentPage(1);
                  setPageSize(size);
                }}
                showSizeChanger
                showQuickJumper
                showTotal={(total, range) => `第 ${range[0]}-${range[1]} 行，共 ${total} 行`}
                pageSizeOptions={['50', '100', '200', '500', '1000']}
              />
            </div>
          )}
        </Card>
      </Content>
    </Layout>
  );
};

export default SystemLogViewerPage;
