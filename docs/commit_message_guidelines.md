## Commit Message 規則與給 AI 的 Prompt 範例

以下內容為團隊建議的 commit message 規則（Conventional Commits 為基礎），以及可直接給 AI 的 prompt 範例與 JSON 回傳 schema，方便自動化工具或 AI 產生符合規範的 commit message。

類型清單（type）
- feat: 新增/修改功能 (feature)
- fix: 修補 bug (bug fix)
- docs: 文件 (documentation)
- style: 格式 (不影響程式碼功能)
- refactor: 重構 (既不是新增功能，也不是修補 bug 的程式碼變動)
- perf: 改善效能
- test: 增加測試
- chore: 建構程序或輔助工具的變動
- revert: 撤銷先前的 commit
- vert: 版本相關變更

System prompt（給 AI）範例：
```
你是一個負責產生符合團隊規範的 commit message 的助手。
必須使用以下 type：feat, fix, docs, style, refactor, perf, test, chore, revert, vert。
格式：<type>(optional-scope): <subject>
- subject 最多 72 字元。
若需要詳細說明，請在下一段 body 撰寫；若為 breaking change，請在 footer 加上 `BREAKING CHANGE: 描述`。
不要在 commit message 中包含任何密碼、憑證或敏感資訊。
回傳時請輸出 JSON（如下 schema），並在 JSON 之外提供每個候選的完整 commit message。
```

User prompt（給 AI 的範例）：
```
根據下列變更檔案與描述，請產生兩個候選的 commit message（包含 subject 與必要的 body/footer），並以 JSON schema 回傳：
- 變更檔案：src/models/user.js, migrations/20250908_add_email.js, tests/user.test.js
- 變更摘要：新增 user.email 欄位、建立遷移並新增測試
```

JSON schema 範例：
```
{
  "candidates": [
    {"type":"feat","scope":"models","subject":"新增 user.email 欄位並更新遷移","body":"新增 user.email 欄位並建立相對應的資料庫遷移。已更新相關模型與單元測試。","footer":"Closes #123"},
    {"type":"test","scope":"tests","subject":"為 user model 新增 email 欄位的測試","body":"新增測試 cover 新 email 欄位的驗證與遷移行為。","footer":""}
  ],
  "explanation":"第一個候選視為功能新增；第二個候選為測試補充。"
}
```

Commitlint / Husky 快速使用指南：
1. 安裝（Node.js 專案）
   npm install --save-dev @commitlint/config-conventional @commitlint/cli husky
2. 把 `commitlint.config.js` 放在 repo 根目錄（範例已提供）。
3. 啟用 Husky 並建立 hook：
   npx husky install
   npx husky add .husky/commit-msg 'npx --no-install commitlint --edit "$1"'

使用建議：建議在本地安裝並啟用 Husky，避免未經審查的 commit 被推上遠端。
