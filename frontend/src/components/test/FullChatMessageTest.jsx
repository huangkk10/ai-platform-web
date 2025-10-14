import React from 'react';
import MessageFormatter from '../chat/MessageFormatter';

/**
 * 完整聊天消息測試
 * 模擬真實的 RVT Assistant 聊天回應，包含完整的圖片數據
 */
const FullChatMessageTest = () => {
  
  // 模擬真實的聊天回應數據
  const mockChatMessage = {
    content: `以下是 UART 相關功能說明：

| 功能 | 主要說明 | 相關圖片 |
|------|----------|----------|
| UART 板數重置 | 顯示目前板數統計的 UART 板數重置各區域狀況是否異常，以免與痛板卡的接觸器異常。 | [IMG:14] |
| UART Log Folder | 一鍵啟動 UART 日誌所在資料夾（預設 C:\\\\UART_Server ），方便檢視已記錄的日誌檔。 | [IMG:15] |
| All Scan (全部掃描) | 檢查所有連接的電腦的 UART 裝置並正確識別裝置與優先權值，請務必與白名單。\\n1) UART TX 連至 SSD UART RX\\n2) force ROM ping 連至 SSD strap ping\\n3) J7 PC_PWR_SW 連接器最高目 | |

希望以上說明對您有幫助！如果需要更詳細的操作步驟，請隨時告訴我。`,
    
    metadata: {
      images: [
        { 
          id: 14, 
          filename: 'board_count.png',
          description: 'UART 板數重置界面截圖'
        },
        { 
          id: 15, 
          filename: 'uart_log_folder.png',
          description: 'UART Log Folder 界面截圖' 
        }
      ]
    }
  };

  // 沒有圖片數據的版本，測試對比
  const mockChatMessageNoImages = {
    content: mockChatMessage.content,
    metadata: null
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>💬 完整聊天消息測試</h1>
      <p style={{ color: '#666', marginBottom: '30px' }}>
        模擬真實的 RVT Assistant 聊天回應，測試表格+圖片的完整渲染
      </p>

      {/* 測試 1: 包含圖片數據的完整消息 */}
      <div style={{ marginBottom: '50px' }}>
        <h2>📱 測試 1: 完整聊天消息（包含圖片數據）</h2>
        
        <div style={{ 
          border: '2px solid #1890ff', 
          borderRadius: '8px',
          backgroundColor: '#fff',
          overflow: 'hidden'
        }}>
          {/* 消息頭部 */}
          <div style={{ 
            backgroundColor: '#1890ff', 
            color: 'white', 
            padding: '10px 15px',
            fontSize: '14px',
            fontWeight: 'bold'
          }}>
            🤖 RVT Assistant 回應
          </div>
          
          {/* 消息內容 */}
          <div style={{ padding: '15px' }}>
            <MessageFormatter 
              content={mockChatMessage.content}
              metadata={mockChatMessage.metadata}
            />
          </div>
        </div>
        
        <div style={{ 
          marginTop: '10px',
          padding: '12px', 
          backgroundColor: '#e6f7ff', 
          border: '1px solid #91d5ff', 
          borderRadius: '6px',
          fontSize: '13px'
        }}>
          <strong>📋 包含的圖片數據：</strong>
          <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
            <li>IMG:14 - board_count.png (UART 板數重置界面截圖)</li>
            <li>IMG:15 - uart_log_folder.png (UART Log Folder 界面截圖)</li>
          </ul>
        </div>
      </div>

      {/* 測試 2: 沒有圖片數據的消息 */}
      <div style={{ marginBottom: '50px' }}>
        <h2>📱 測試 2: 沒有圖片數據的消息（對比測試）</h2>
        
        <div style={{ 
          border: '2px solid #ff7875', 
          borderRadius: '8px',
          backgroundColor: '#fff',
          overflow: 'hidden'
        }}>
          {/* 消息頭部 */}
          <div style={{ 
            backgroundColor: '#ff7875', 
            color: 'white', 
            padding: '10px 15px',
            fontSize: '14px',
            fontWeight: 'bold'
          }}>
            🤖 RVT Assistant 回應（無圖片數據）
          </div>
          
          {/* 消息內容 */}
          <div style={{ padding: '15px' }}>
            <MessageFormatter 
              content={mockChatMessageNoImages.content}
              metadata={mockChatMessageNoImages.metadata}
            />
          </div>
        </div>
        
        <div style={{ 
          marginTop: '10px',
          padding: '12px', 
          backgroundColor: '#fff1f0', 
          border: '1px solid #ffccc7', 
          borderRadius: '6px',
          fontSize: '13px'
        }}>
          <strong>⚠️ 沒有圖片數據：</strong> 這個版本沒有提供 metadata.images，所以 [IMG:14] 和 [IMG:15] 會顯示為佔位符
        </div>
      </div>

      {/* 觀察重點 */}
      <div style={{ 
        padding: '20px', 
        backgroundColor: '#fff7e6', 
        border: '1px solid #ffd666',
        borderRadius: '8px'
      }}>
        <h3>🔍 關鍵觀察重點：</h3>
        <div style={{ display: 'grid', gap: '15px', gridTemplateColumns: '1fr 1fr' }}>
          <div>
            <h4>✅ 正常情況應該看到：</h4>
            <ul style={{ lineHeight: '1.6' }}>
              <li>表格正確分為三欄</li>
              <li>每欄內容在正確位置</li>
              <li>圖片在表格下方顯示</li>
              <li>表格結構不受圖片影響</li>
            </ul>
          </div>
          <div>
            <h4>❌ 問題症狀：</h4>
            <ul style={{ lineHeight: '1.6' }}>
              <li>表格內容全部擠在第一欄</li>
              <li>表格變成單列顯示</li>
              <li>圖片佔位符影響表格佈局</li>
              <li>[IMG:14] 沒有對應到實際圖片</li>
            </ul>
          </div>
        </div>
        
        <div style={{ 
          marginTop: '15px', 
          padding: '12px', 
          backgroundColor: '#f0f8ff', 
          border: '1px solid #d6e4ff', 
          borderRadius: '4px' 
        }}>
          <strong>🎯 這個測試的價值：</strong> 使用真實的 MessageFormatter 和完整的圖片數據，
          完全重現 RVT Assistant 的實際使用場景，能夠準確診斷問題所在。
        </div>
      </div>
    </div>
  );
};

export default FullChatMessageTest;