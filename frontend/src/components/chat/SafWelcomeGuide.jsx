/**
 * SAF Assistant 折疊式歡迎引導組件      { text: '總共有多少專案？', query: '總共有多少專案？' },
    ]
  },
  {
    key: 'fw-version-query',=====================
 * 
 * 功能：
 * - 顯示可折疊的功能類別列表
 * - 點擊類別可展開/收起範例問句
 * - 點擊範例問句可自動填入輸入框
 * 
 * 使用方式：
 * <SafWelcomeGuide onExampleClick={(query) => setInputMessage(query)} />
 */

import React from 'react';
import { Collapse, Typography } from 'antd';
import { CaretRightOutlined } from '@ant-design/icons';
import './SafWelcomeGuide.css';

const { Text } = Typography;

// SAF Assistant 功能類別資料結構（精簡版：6 大類別）
const GUIDE_CATEGORIES = [
  {
    key: 'project-query',
    icon: '🏢',
    title: '專案查詢',
    examples: [
      { text: 'WD 有哪些專案？', query: 'WD 有哪些專案？' },
      { text: 'SM2264 用在哪些專案？', query: 'SM2264 用在哪些專案？' },
      { text: 'PVF01 專案的詳細資訊', query: 'PVF01 專案的詳細資訊' },
      { text: '總共有多少專案？', query: '總共有多少專案？' },
    ]
  },
  {
    key: 'test-results',
    icon: '�',
    title: '測試結果',
    examples: [
      { text: 'Springsteen FW PH10YC3H_Pyrite_4K 測試結果如何？', query: 'Springsteen FW PH10YC3H_Pyrite_4K 測試結果如何？' },
      { text: 'Springsteen FW PH10YC3H_Pyrite_4K 有多少測試通過？', query: 'Springsteen FW PH10YC3H_Pyrite_4K 有多少測試通過？' },
      { text: 'Springsteen FW PH10YC3H_Pyrite_4K 的 Compliance 測試結果', query: 'Springsteen FW PH10YC3H_Pyrite_4K 的 Compliance 測試結果' },
      { text: 'Springsteen 最新 5個 FW 測試結果 比較', query: 'Springsteen 最新 5個 FW 測試結果 比較' },
    ]
  },
  {
    key: 'test-item-results',
    icon: '�',
    title: '測試項目結果',
    examples: [
      { text: 'Springsteen FW G210X74A 的測試項目結果？', query: 'Springsteen FW G210X74A 的測試項目結果？' },
      { text: '比較 Springsteen 不同 FW 的測試項目結果 G210X74A G210Y1NA G210Y33A', query: '比較 Springsteen 不同 FW 的測試項目結果 G210X74A G210Y1NA G210Y33A' }
    ]
  },
  {
    key: 'fw-version-query',
    icon: '🔖',
    title: 'FW 版本查詢',
    examples: [
      { text: 'Springsteen 有哪些 FW 版本？', query: 'Springsteen 有哪些 FW 版本？' },
      { text: 'Springsteen 近 2 個月有哪些 FW 版本', query: 'Springsteen 近 2 個月有哪些 FW 版本' },
      { text: 'Springsteen FW XX 支援哪些容量？', query: 'Springsteen FW XX 支援哪些容量？' },
    ]
  },
  {
    key: 'fw-test-analysis',
    icon: '🎯',
    title: 'FW 測試分析',
    examples: [
      { text: 'Springsteen FW PH10YC3H_Pyrite_4K 測試結果如何？', query: 'Springsteen FW PH10YC3H_Pyrite_4K 測試結果如何？' },
      { text: 'Springsteen PH10YC3H_Pyrite_4K 的測試項目結果', query: 'Springsteen PH10YC3H_Pyrite_4K 的測試項目結果' },
    ]
  },
  {
    key: 'known-issues',
    icon: '⚠️',
    title: 'Known Issues 查詢',
    examples: [
      { text: 'Springsteen 專案有多少 Known Issues？', query: 'Springsteen 專案有多少 Known Issues？' },
      { text: '哪些專案的 Known Issues 最多？', query: '哪些專案的 Known Issues 最多？' },
    ]
  },
  {
    key: 'system-info',
    icon: '�',
    title: '系統資訊',
    examples: [
      { text: '有哪些客戶？', query: '有哪些客戶？' },
      { text: '有哪些控制器？', query: '有哪些控制器？' },
    ]
  },
];

/**
 * SafWelcomeGuide 組件
 * @param {Function} onExampleClick - 點擊範例問句時的回調函數
 */
const SafWelcomeGuide = ({ onExampleClick }) => {
  
  // 處理範例問句點擊
  const handleExampleClick = (query, e) => {
    e.stopPropagation(); // 防止觸發折疊/展開
    if (onExampleClick) {
      onExampleClick(query);
    }
  };

  // 生成 Collapse 的 items
  const collapseItems = GUIDE_CATEGORIES.map((category) => ({
    key: category.key,
    label: (
      <span className="saf-guide-category-label">
        <span className="saf-guide-category-icon">{category.icon}</span>
        <span className="saf-guide-category-title">{category.title}</span>
      </span>
    ),
    children: (
      <div className="saf-guide-examples">
        {category.examples.map((example, idx) => (
          <div
            key={idx}
            className="saf-guide-example-item"
            onClick={(e) => handleExampleClick(example.query, e)}
          >
            <span className="saf-guide-example-bullet">•</span>
            <span className="saf-guide-example-text">「{example.text}」</span>
          </div>
        ))}
      </div>
    ),
  }));

  return (
    <div className="saf-welcome-guide">
      {/* 標題區域 */}
      <div className="saf-guide-header">
        <div className="saf-guide-title">🔧 <strong>歡迎使用 SAF Assistant！</strong></div>
        <div className="saf-guide-subtitle">
          我是 SAF 專案管理系統的智能助手，可以協助你快速查詢專案相關資訊。
        </div>
      </div>

      {/* 功能類別區域 */}
      <div className="saf-guide-section">
        <div className="saf-guide-section-title">📋 我可以幫助你：</div>
        
        <Collapse
          ghost
          expandIcon={({ isActive }) => (
            <CaretRightOutlined 
              rotate={isActive ? 90 : 0} 
              style={{ fontSize: '12px', color: '#666' }}
            />
          )}
          defaultActiveKey={[]}  // 預設全部收起
          className="saf-guide-collapse"
          items={collapseItems}
        />
      </div>

      {/* 提示區域 */}
      <div className="saf-guide-tip">
        <Text type="secondary">
          💡 <strong>提示</strong>：點擊類別展開查看範例，點擊範例可快速提問！
        </Text>
      </div>

      {/* 結尾文字 */}
      <div className="saf-guide-footer">
        現在就開始吧！有什麼 SAF 專案相關的問題需要查詢嗎？
      </div>
    </div>
  );
};

export default SafWelcomeGuide;
