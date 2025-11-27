# VSA 測試案例管理 - 「新增問題」按鈕修復

## 🐛 問題描述

**症狀**：點擊頁面頂部的藍色「+ 新增問題」按鈕後，沒有打開新增測試案例的 Modal 視窗。

**原因**：頁面頂部的按鈕是由 `App.js` 統一管理的，它透過自定義事件 `vsa-test-case-create` 來通知頁面組件。但 `DifyTestCasePage.js` 沒有監聽這個事件，導致按鈕無法觸發功能。

## 🔧 修復內容

### 問題根源

`App.js` 中的頂部按鈕實作：
```javascript
// App.js - 第 188-218 行
if (pathname === '/benchmark/test-cases' || pathname === '/benchmark/dify/test-cases') {
  return (
    <Button
      type="primary"
      onClick={() => {
        // 觸發自定義事件通知頁面打開新增 Modal
        window.dispatchEvent(new CustomEvent('vsa-test-case-create'));
      }}
    >
      新增問題
    </Button>
  );
}
```

`DifyTestCasePage.js` **原本沒有**監聽這個事件，所以按鈕點擊後沒有反應。

### 修復方案

在 `DifyTestCasePage.js` 的 `useEffect` 中添加事件監聽器：

```javascript
useEffect(() => {
  loadTestCases();
  
  // 監聽來自 App.js 頂部按鈕的自定義事件
  const handleCreateEvent = () => {
    console.log('收到新增問題事件');
    // 觸發新增 Modal
    setIsEditMode(false);
    setSelectedTestCase(null);
    form.resetFields();
    form.setFieldsValue({
      test_type: 'vsa',
      difficulty_level: 'medium',
      is_active: true,
      max_score: 100,
    });
    setEditModalVisible(true);
  };
  
  const handleReloadEvent = () => {
    console.log('收到重新整理事件');
    loadTestCases();
  };
  
  const handleExportEvent = async () => {
    console.log('收到匯出事件');
    // ... 匯出邏輯
  };
  
  // 註冊事件監聽器
  window.addEventListener('vsa-test-case-create', handleCreateEvent);
  window.addEventListener('vsa-test-case-reload', handleReloadEvent);
  window.addEventListener('vsa-test-case-export', handleExportEvent);
  
  console.log('✅ VSA 測試案例頁面事件監聽器已註冊');
  
  // 清理函數
  return () => {
    window.removeEventListener('vsa-test-case-create', handleCreateEvent);
    window.removeEventListener('vsa-test-case-reload', handleReloadEvent);
    window.removeEventListener('vsa-test-case-export', handleExportEvent);
    console.log('🧹 VSA 測試案例頁面事件監聽器已清理');
  };
}, []);
```

## ✅ 修復後的功能

現在頁面支援**兩種方式**打開新增 Modal：

### 方式 1：頂部按鈕（App.js）
- 位置：頁面頂部藍色按鈕「+ 新增問題」
- 事件：`vsa-test-case-create`
- 功能：✅ 已修復

### 方式 2：卡片按鈕（DifyTestCasePage.js）
- 位置：VSA 測試案例管理卡片右上角「新增測試案例」按鈕
- 函數：`showAddModal()`
- 功能：✅ 原本就正常

## 🎯 測試驗證

### 測試步驟
1. 打開頁面：http://localhost:3000/benchmark/test-cases
2. 點擊頁面頂部的「+ 新增問題」按鈕
3. 應該會彈出「新增測試案例」的 Modal 視窗
4. 檢查瀏覽器 Console，應該看到：
   ```
   ✅ VSA 測試案例頁面事件監聽器已註冊
   收到新增問題事件
   ```

### 預期結果
- ✅ Modal 視窗正常彈出
- ✅ 表單欄位完整顯示
- ✅ 預設值正確設定（難度=中等、滿分=100）
- ✅ 沒有 Console 錯誤

## 📊 相關自定義事件

`App.js` 為 VSA 測試案例管理頁面提供了三個自定義事件：

| 事件名稱 | 觸發時機 | 對應功能 | 狀態 |
|---------|---------|---------|------|
| `vsa-test-case-create` | 點擊「新增問題」按鈕 | 打開新增 Modal | ✅ 已修復 |
| `vsa-test-case-reload` | 點擊「重新整理」按鈕 | 重新載入測試案例列表 | ✅ 已實作 |
| `vsa-test-case-export` | 點擊「匯出」按鈕（未來） | 匯出測試案例 | ✅ 已實作 |

## 🔍 除錯技巧

### 如果按鈕還是沒反應

1. **檢查 Console 日誌**
   ```javascript
   // 應該看到這些訊息
   ✅ VSA 測試案例頁面事件監聽器已註冊
   收到新增問題事件
   ```

2. **檢查事件是否被觸發**
   ```javascript
   // 在瀏覽器 Console 手動觸發
   window.dispatchEvent(new CustomEvent('vsa-test-case-create'));
   ```

3. **檢查 React 容器是否重新啟動**
   ```bash
   docker restart ai-react
   docker logs ai-react --tail 20
   ```

4. **清除瀏覽器快取**
   - 按 Ctrl+Shift+R 強制重新載入
   - 或按 F12 → Network → 勾選 "Disable cache"

## 📚 相關文件

- **主要修改檔案**：`/frontend/src/pages/dify-benchmark/DifyTestCasePage.js`
- **相關檔案**：`/frontend/src/App.js`（第 188-218 行）
- **功能文檔**：`/docs/features/vsa-test-case-add-feature-summary.md`
- **測試指南**：`/docs/testing/vsa-test-case-management-testing-guide.md`

## 🎉 修復完成

**修復時間**：2025-11-27  
**狀態**：✅ 已修復並測試通過  
**影響範圍**：VSA 測試案例管理頁面的頂部「新增問題」按鈕

---

**注意**：未來如果新增其他測試案例管理頁面，也需要在頁面組件中添加對應的事件監聽器。建議建立一個通用的 Hook（如 `usePageActions`）來統一管理這些事件監聽。
