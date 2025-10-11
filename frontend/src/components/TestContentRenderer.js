import React from 'react';
import { Card } from 'antd';
import ContentRenderer from './ContentRenderer';

const TestContentRenderer = () => {
  const testContent = `# RVT 介紹
RVT 的全名是 Rapid Validation Testbed. 它是針對SSD產品進行自動化測試系統，核心由 Jenkins 與 Ansible 組成。


🖼️ [IMG:7] kisspng-jenkins-software-build-continuous-integration-plug-github-5ab8a49242f3c8.9678219615220501942742.png (📌 主要圖片, 標題: kisspng-jenkins-software-build-continuous-integration-plug-github-5ab8a49242f3c8.9678219615220501942742.png)`;

  return (
    <Card title="ContentRenderer 測試" style={{ margin: '20px' }}>
      <ContentRenderer 
        content={testContent}
        showImageTitles={true}
        showImageDescriptions={true}
        imageMaxWidth={400}
        imageMaxHeight={300}
      />
    </Card>
  );
};

export default TestContentRenderer;