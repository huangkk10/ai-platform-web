# 📝 VSA 批量測試並行線程數預設值調整

## 📅 修改日期
2025-11-25

## 🎯 修改內容

**檔案位置**：`frontend/src/pages/dify-benchmark/DifyVersionManagementPage.js`

### 修改項目：並行線程數預設值

```javascript
// ❌ 修改前
batchTestForm.setFieldsValue({
  batch_name: `批量測試 ${new Date().toLocaleString('zh-TW')}`,
  notes: '',
  force_retest: false,
  use_parallel: true,
  max_workers: 10  // 舊預設值
});

// ✅ 修改後
batchTestForm.setFieldsValue({
  batch_name: `批量測試 ${new Date().toLocaleString('zh-TW')}`,
  notes: '',
  force_retest: false,
  use_parallel: true,
  max_workers: 5  // 新預設值
});
```

## 📊 修改原因

| 項目 | 預設值 10 | 預設值 5 | 優勢 |
|------|-----------|----------|------|
| **系統負載** | 高 ⚠️ | 中等 ✅ | 減少系統壓力 |
| **測試速度** | 快 | 中等 | 仍然保持合理速度 |
| **穩定性** | 可能不穩定 | 更穩定 ✅ | 減少錯誤發生 |
| **資源消耗** | 高 | 適中 ✅ | 更經濟 |

## 🎯 效果

### 使用者體驗
- ✅ 開啟批量測試 Modal 時，「並行線程數」欄位預設顯示 **5**
- ✅ 使用者仍可手動調整（範圍 1-20）
- ✅ 系統負載更合理，減少測試失敗機率

### 測試時間估算
```
假設測試 3 個版本：
- 10 線程：約 5 秒
- 5 線程：約 9 秒
差異：僅增加 4 秒，但穩定性大幅提升
```

## ✅ 驗證步驟

1. 刷新 VSA 配置版本管理頁面
2. 選擇多個版本
3. 點擊「批量測試」按鈕
4. 確認「並行線程數」欄位預設值為 **5**

## 📝 相關配置

**Tooltip 說明**（未修改）：
```
建議設定為 5-10，數值越大測試越快，但會增加系統負載
```

**允許範圍**（未修改）：
- 最小值：1
- 最大值：20
- 預設值：5 ⬅️ **已修改**

---

**📅 更新日期**: 2025-11-25  
**📝 版本**: v1.0  
**✍️ 作者**: AI Platform Team  
**🎯 用途**: 記錄批量測試並行線程數預設值調整
