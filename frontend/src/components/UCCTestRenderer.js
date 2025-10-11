import React from 'react';
import { Card } from 'antd';
import ContentRenderer from './ContentRenderer';

const UCCTestRenderer = () => {
  // 使用實際的UCC Tool內容進行測試
  const uccContent = `# UCC(UART Control Center) User Guide

本文件簡要說明 UCC(UART Control Center) 控制中心軟體的主要操作介面與功能。

使用者可透過本 UI 進行 UART 板卡數量查詢、全部掃描、單一板卡掃描，以及各種 UART 相關控制與狀態監控，協助快速確認硬體連線、進行資料記錄與分析。

🖼️ [IMG:8] ucc_ui.png (📌 主要圖片, 標題: UCC Tool)


## UART Board Count — Display Connected Board Quantity
**UART 板數量**功能會顯示 UART 控制中心電腦目前偵測到的 UART 板總數。

圖示（示意）：UART 板數量顯示區，會列出目前被偵測到的板卡數量與各板的簡短狀態摘要。`;

  return (
    <Card title="UCC Guide 測試 - ContentRenderer" style={{ margin: '20px 0' }}>
      <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
        <ContentRenderer 
          content={uccContent}
          showImageTitles={true}
          showImageDescriptions={true}
          imageMaxWidth={600}
          imageMaxHeight={400}
        />
      </div>
    </Card>
  );
};

export default UCCTestRenderer;