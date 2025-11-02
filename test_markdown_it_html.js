// 測試 markdown-it 的 HTML 支援
const MarkdownIt = require('markdown-it');

// 測試 1：基本配置（無 HTML 支援）
console.log('=== 測試 1：html: false ===');
const md1 = new MarkdownIt({ html: false });
const result1 = md1.render('第一行<br>第二行');
console.log('輸入:', '第一行<br>第二行');
console.log('輸出:', result1);
console.log('包含 <br>?', result1.includes('<br>'));
console.log('包含 &lt;br&gt;?', result1.includes('&lt;br&gt;'));
console.log('');

// 測試 2：啟用 HTML 支援
console.log('=== 測試 2：html: true ===');
const md2 = new MarkdownIt({ html: true, breaks: true });
const result2 = md2.render('第一行<br>第二行');
console.log('輸入:', '第一行<br>第二行');
console.log('輸出:', result2);
console.log('包含 <br>?', result2.includes('<br>'));
console.log('包含 &lt;br&gt;?', result2.includes('&lt;br&gt;'));
console.log('');

// 測試 3：混合 Markdown 和 HTML
console.log('=== 測試 3：混合內容 ===');
const md3 = new MarkdownIt({ html: true, breaks: true });
const result3 = md3.render('## 標題\n\n第一行<br>第二行\n\n**粗體**');
console.log('輸入:', '## 標題\\n\\n第一行<br>第二行\\n\\n**粗體**');
console.log('輸出:', result3);
console.log('');

// 測試 4：純 HTML 區塊
console.log('=== 測試 4：純 HTML 區塊 ===');
const md4 = new MarkdownIt({ html: true });
const result4 = md4.render('<div>第一行<br>第二行</div>');
console.log('輸入:', '<div>第一行<br>第二行</div>');
console.log('輸出:', result4);
