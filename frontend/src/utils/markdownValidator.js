/**
 * Markdown 格式驗證工具
 * 檢查內容是否符合 Section 向量生成的最低要求
 * 
 * 使用範例：
 * import { validateMarkdownStructure, formatValidationMessage } from './markdownValidator';
 * 
 * const result = validateMarkdownStructure(content);
 * if (!result.valid) {
 *   Modal.error({ content: formatValidationMessage(result) });
 * }
 */

/**
 * 驗證 Markdown 內容格式
 * @param {string} content - Markdown 內容
 * @returns {Object} 驗證結果
 * {
 *   valid: boolean,           // 是否通過驗證
 *   errors: string[],         // 阻擋性錯誤（必須修正）
 *   warnings: string[],       // 警告（建議修正，但不阻擋）
 *   stats: {                  // 內容統計
 *     length: number,         // 內容長度
 *     h1Count: number,        // 一級標題數量
 *     h2Count: number,        // 二級標題數量
 *     h3Count: number,        // 三級標題數量
 *     totalHeadings: number   // 總標題數量
 *   }
 * }
 */
export const validateMarkdownStructure = (content) => {
  const result = {
    valid: false,
    errors: [],      // 阻擋性錯誤（必須修正）
    warnings: [],    // 警告（建議修正，但不阻擋）
    stats: {
      length: 0,
      h1Count: 0,
      h2Count: 0,
      h3Count: 0,
      totalHeadings: 0
    }
  };

  // 檢查 1：內容不能為空
  if (!content || content.trim().length === 0) {
    result.errors.push('內容不能為空');
    return result;
  }

  const trimmedContent = content.trim();
  result.stats.length = trimmedContent.length;

  // 檢查 2：內容長度必須 >= 20 字元
  if (trimmedContent.length < 20) {
    result.errors.push(`內容過短（${trimmedContent.length} 字元），至少需要 20 字元`);
    // 繼續檢查其他問題，給出完整的錯誤報告
  }

  // 檢查 3：統計標題數量
  // 使用正則表達式匹配 Markdown 標題
  const h1Matches = trimmedContent.match(/^#\s+.+$/gm);   // # 標題（開頭必須是 #，後面有空格和內容）
  const h2Matches = trimmedContent.match(/^##\s+.+$/gm);  // ## 標題
  const h3Matches = trimmedContent.match(/^###\s+.+$/gm); // ### 標題

  result.stats.h1Count = h1Matches ? h1Matches.length : 0;
  result.stats.h2Count = h2Matches ? h2Matches.length : 0;
  result.stats.h3Count = h3Matches ? h3Matches.length : 0;
  result.stats.totalHeadings = result.stats.h1Count + result.stats.h2Count + result.stats.h3Count;

  // 檢查 4：必須至少有 1 個一級標題
  if (result.stats.h1Count === 0) {
    result.errors.push('必須包含至少 1 個一級標題（# 標題）');
  }

  // 檢查 5：建議至少有 1 個二級標題（警告級別，不阻擋儲存）
  if (result.stats.h2Count === 0 && result.stats.h1Count > 0) {
    result.warnings.push('建議添加二級標題（## 標題）來組織內容結構，這有助於 AI 更好地理解您的內容');
  }

  // 檢查 6：檢查標題是否有內容（檢查空標題）
  if (result.stats.totalHeadings > 0) {
    const allHeadings = [
      ...(h1Matches || []),
      ...(h2Matches || []),
      ...(h3Matches || [])
    ];

    const emptyHeadings = allHeadings.filter(heading => {
      // 移除 # 符號和空格後，檢查是否還有內容
      const text = heading.replace(/^#+\s+/, '').trim();
      return text.length === 0;
    });

    if (emptyHeadings.length > 0) {
      result.errors.push(`發現 ${emptyHeadings.length} 個空標題（標題後面沒有文字）`);
    }
  }

  // 檢查 7：如果內容長度足夠但沒有任何標題，給出更明確的提示
  if (result.stats.totalHeadings === 0 && trimmedContent.length >= 20) {
    result.errors.push(
      '內容中沒有找到任何 Markdown 標題結構。' +
      '請使用 # 開頭來創建標題，例如：\n' +
      '# 一級標題\n' +
      '## 二級標題'
    );
  }

  // 判斷是否通過驗證（只有沒有錯誤時才通過，警告不影響）
  result.valid = result.errors.length === 0;

  return result;
};

/**
 * 格式化驗證錯誤訊息（用於 Modal 顯示）
 * @param {Object} validationResult - validateMarkdownStructure 的返回值
 * @returns {JSX} React 元素（HTML 格式的錯誤訊息）
 */
export const formatValidationMessage = (validationResult) => {
  const { stats, errors, warnings } = validationResult;

  return (
    <div style={{ textAlign: 'left' }}>
      {/* 內容統計 */}
      <div style={{ marginBottom: '16px' }}>
        <p style={{ fontWeight: 'bold', marginBottom: '8px' }}>📊 內容統計：</p>
        <ul style={{ marginLeft: '20px', lineHeight: '1.8' }}>
          <li>內容長度：<strong>{stats.length}</strong> 字元</li>
          <li>一級標題（#）：<strong>{stats.h1Count}</strong> 個 {stats.h1Count > 0 ? '✅' : '❌'}</li>
          <li>二級標題（##）：<strong>{stats.h2Count}</strong> 個 {stats.h2Count > 0 ? '✅' : '⚠️'}</li>
          <li>三級標題（###）：<strong>{stats.h3Count}</strong> 個</li>
        </ul>
      </div>

      {/* 顯示錯誤 */}
      {errors.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <p style={{ color: '#ff4d4f', fontWeight: 'bold', marginBottom: '8px' }}>
            ❌ 必須修正的問題：
          </p>
          <ul style={{ marginLeft: '20px', lineHeight: '1.8', color: '#ff4d4f' }}>
            {errors.map((error, index) => (
              <li key={index} style={{ whiteSpace: 'pre-wrap' }}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 顯示警告 */}
      {warnings.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <p style={{ color: '#fa8c16', fontWeight: 'bold', marginBottom: '8px' }}>
            ⚠️ 建議改進：
          </p>
          <ul style={{ marginLeft: '20px', lineHeight: '1.8', color: '#fa8c16' }}>
            {warnings.map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 顯示標準範例 */}
      <div>
        <p style={{ fontWeight: 'bold', marginBottom: '8px' }}>✅ 標準格式範例：</p>
        <pre style={{
          background: '#f5f5f5',
          padding: '12px',
          borderRadius: '4px',
          overflowX: 'auto',
          fontSize: '13px',
          lineHeight: '1.6',
          border: '1px solid #d9d9d9'
        }}>
{`# Protocol 測試指南

## 測試目的
說明測試的目標和範圍...

## 測試步驟
1. 步驟一：準備測試環境
2. 步驟二：執行測試
3. 步驟三：記錄結果

## 預期結果
描述預期的測試結果...

## 注意事項
列出需要注意的事項...`}
        </pre>
      </div>
    </div>
  );
};

/**
 * 獲取內容建議（提供快速修正方案）
 * @param {string} content - 原始內容
 * @param {Object} validationResult - 驗證結果
 * @returns {string} 修正後的內容建議
 */
export const getSuggestedContent = (content, validationResult) => {
  let suggested = content;

  // 如果沒有一級標題，在開頭添加預設標題
  if (validationResult.stats.h1Count === 0) {
    suggested = '# Protocol Guide 標題\n\n' + suggested;
  }

  // 如果沒有二級標題但有一級標題，在第一個一級標題後添加二級標題
  if (validationResult.stats.h2Count === 0 && validationResult.stats.h1Count > 0) {
    const firstH1Index = suggested.search(/^#\s+.+$/m);
    if (firstH1Index !== -1) {
      const endOfLine = suggested.indexOf('\n', firstH1Index);
      if (endOfLine !== -1) {
        suggested = 
          suggested.slice(0, endOfLine + 1) +
          '\n## 說明\n\n' +
          suggested.slice(endOfLine + 1);
      }
    }
  }

  // 如果內容太短，添加提示文字
  if (validationResult.stats.length < 20) {
    suggested += '\n\n（請在此添加更多內容說明...）';
  }

  return suggested;
};

/**
 * 快速驗證（只檢查是否通過，不返回詳細資訊）
 * @param {string} content - Markdown 內容
 * @returns {boolean} 是否通過驗證
 */
export const isValidMarkdown = (content) => {
  const result = validateMarkdownStructure(content);
  return result.valid;
};

/**
 * 獲取驗證錯誤的簡短描述（用於 message 提示）
 * @param {Object} validationResult - 驗證結果
 * @returns {string} 簡短錯誤描述
 */
export const getShortErrorMessage = (validationResult) => {
  if (validationResult.valid) {
    return '';
  }
  
  if (validationResult.errors.length === 1) {
    return validationResult.errors[0];
  }
  
  return `發現 ${validationResult.errors.length} 個問題需要修正`;
};
