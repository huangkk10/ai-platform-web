/**
 * Protocol Assistant 聊天頁面
 * ===========================
 * 
 * 使用通用 CommonAssistantChatPage 組件
 * 只需配置參數即可
 */

import React, { useState, useEffect } from 'react';
import { Alert, Space, Tag } from 'antd';
import { StarFilled, SyncOutlined, InfoCircleOutlined } from '@ant-design/icons';
import CommonAssistantChatPage from '../components/chat/CommonAssistantChatPage';
import useProtocolAssistantChat from '../hooks/useProtocolAssistantChat';
import difyBenchmarkApi from '../services/difyBenchmarkApi';
import '../components/markdown/ReactMarkdown.css';
import './ProtocolAssistantChatPage.css';

// Protocol Assistant 專用歡迎訊息
const PROTOCOL_WELCOME_MESSAGE = '🛠️ 歡迎使用 Protocol Assistant！我是你的 Protocol 測試專家助手，可以協助你解決 Protocol 相關的問題。\n\n**我可以幫助你：**\n- Protocol 測試流程指導\n- 故障排除和問題診斷\n- Protocol 工具使用方法\n\n**💡 搜尋技巧：**\n想獲得完整文檔？在查詢中使用以下關鍵字：\n- **SOP、標準作業流程、操作流程** → 取得完整 SOP\n- **完整、全部、所有步驟、全文** → 取得完整內容\n- **教學、指南、手冊** → 取得完整教學文檔\n\n範例：「IOL 放測 **SOP**」、「請給我 **完整** 的 CrystalDiskMark 教學」\n\n現在就開始吧！有什麼 Protocol 相關的問題需要協助嗎？';

const ProtocolAssistantChatPage = ({ collapsed = false }) => {
  const [baselineVersion, setBaselineVersion] = useState(null);
  const [loading, setLoading] = useState(true);

  // 載入 Baseline 版本資訊
  useEffect(() => {
    const fetchBaselineVersion = async () => {
      try {
        const response = await difyBenchmarkApi.getDifyBaseline();
        if (response.data && response.data.baseline) {
          setBaselineVersion(response.data.baseline);
        }
      } catch (error) {
        console.error('載入 Baseline 版本失敗:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchBaselineVersion();
  }, []);

  // 檢查是否為動態版本
  const isDynamic = baselineVersion?.rag_settings?.stage1?.use_dynamic_threshold || 
                   baselineVersion?.rag_settings?.stage2?.use_dynamic_threshold;

  return (
    <div style={{ height: '100vh', position: 'relative' }}>
      {/* Baseline 資訊欄（固定在頂部） */}
      {!loading && baselineVersion && (
        <Alert
          message={
            <Space size="middle">
              <Space size="small">
                <StarFilled style={{ color: '#faad14' }} />
                <span style={{ fontWeight: 'bold' }}>
                  Benchmark Baseline: {baselineVersion.version_name}
                </span>
              </Space>
              {isDynamic && (
                <Tag color="orange" icon={<SyncOutlined spin />}>
                  動態 Threshold
                </Tag>
              )}
            </Space>
          }
          description={
            <div style={{ fontSize: '12px' }}>
              <InfoCircleOutlined style={{ marginRight: '6px' }} />
              此配置僅用於 <strong>Benchmark 測試</strong>。
              Chat 功能的檢索參數在 <strong>Dify 工作室</strong> 中配置，與 Baseline 無關。
            </div>
          }
          type="info"
          showIcon={false}
          style={{
            position: 'fixed',
            top: '64px',
            left: collapsed ? 80 : 300,
            right: 0,
            zIndex: 999,
            margin: 0,
            borderRadius: 0,
            borderLeft: 'none',
            borderRight: 'none',
            transition: 'left 0.2s'
          }}
        />
      )}

      {/* 聊天組件（需要根據是否顯示 Baseline 調整 padding） */}
      <div style={{ 
        height: '100%', 
        paddingTop: (!loading && baselineVersion) ? '88px' : '0'  // 為 Baseline 欄預留空間
      }}>
        <CommonAssistantChatPage
          assistantType="protocol"
          assistantName="Protocol Assistant"
          useChatHook={useProtocolAssistantChat}
          configApiPath="/api/protocol-assistant/config/"
          storageKey="protocol-assistant"
          permissionKey="webProtocolAssistant"
          placeholder="請描述你的 Protocol 問題..."
          welcomeMessage={PROTOCOL_WELCOME_MESSAGE}
          collapsed={collapsed}
        />
      </div>
    </div>
  );
};

export default ProtocolAssistantChatPage;
