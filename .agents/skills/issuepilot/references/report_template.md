
# IssuePilot Analysis Report

## 1. Issue 摘要

- Repository:
- 本機 Repository 路徑：
- Issue URL:
- Issue Title:
- Issue 狀態與來源：
- Analysis Commit SHA：
- 版本來源：Engineer 目前 checkout 的 HEAD；記錄 `version_selector.py` 結果與檢查時間。
- 工作目錄狀態：clean / dirty / 未知；記錄 `is_dirty`。
- 若為 dirty，Engineer 是否明確同意以 HEAD 分析：已確認 / 未確認 / 不適用；附確認內容。未確認時停止原始碼檢索，僅回報阻礙。
- 分析範圍：固定上述 SHA；不包含 staged、unstaged、untracked 修改。
- Problem Description:
- 預期行為（Expected Behavior）：
- 預期行為的資訊來源：Issue／討論連結、文件或測試路徑與 SHA；無依據時標示未知。
- 實際行為（Actual Behavior）：
- 實際行為的資訊來源：區分 Issue 回報、Engineer 描述與 Agent 親自觀察。
- Bug 重現狀態：未驗證 / 已執行但未重現 / 已重現；未執行重現必須填「未驗證」。
- 重現紀錄：若有執行，記錄環境、實際執行版本、命令、結果與證據 ID；否則填「未執行」。Issue 的 stack trace 不等於 Agent 已重現。
- 分析獨立性：是否曾接觸修復答案；初次 RCA 不得主動查看真正的 Fix PR。

## 2. 相關原始碼

| File | Function / Class | Relevant Lines | Analysis SHA | Reason / Evidence ID |
|------|------------------|----------------|--------------|----------------------|

- 搜尋線索與候選檔案選擇理由：記錄檔名、函式或錯誤片段及對應查詢。
- 檢索限制：記錄 `truncated`、`scan_truncated`、`skipped_files`；片段截斷時記錄 `content_start_column`、`content_truncated`，不得將片段當完整程式碼。
- 版本與範圍限制：例如外部依賴不在本 Repository；未知的路徑或行號填「未知」，不得猜測。

## 3. 根本原因假設

每個假設分別填寫；尚未確定根因時明確保留為假設。

- Hypothesis:
- 已驗證事實：附證據 ID；Issue 作者的主張須標示為回報內容，不可直接當作獨立驗證。
- 推測與尚未驗證的因果關係：
- Confidence: High / Medium / Low
- 信心判斷理由：說明證據直接性、完整性、相反證據及未重現等限制；此等級是定性判斷，不是統計機率。
- Explanation:
- 支持／反對的證據 ID：
- 驗證或推翻此假設所需的研究／測試：

## 4. 支持證據

| Evidence ID | Evidence | Source（路徑／URL） | 行號 | Analysis SHA／實際執行版本 | Observation（事實／回報／推測） |
|-------------|----------|--------------------|------|----------------------------|--------------------------------|

- 相關程式碼片段：盡可能附上對應證據 ID、路徑、SHA 與行號；保留原始 identifiers，不放入敏感資訊。
- 文件／Issue 討論：附可追溯來源；沒有取得的討論不得宣稱已閱讀。
- 測試／重現結果：只記錄確實執行的命令、環境、版本、Exit Code 與重要輸出；未執行填「未驗證」。讀到測試程式碼不代表測試通過。

## 5. 建議修復方式

- Proposed Change:
- Rationale:
- Potential Risks:
- 對應假設與證據 ID：
- 預計影響範圍、預期行為與待驗證條件：
- 方案前提與仍待決定事項：連結第 7 節，不代替 Engineer 做業務決策。
- 實作狀態：僅為建議，未修改程式碼；本報告不代表修復授權。

## 6. 建議測試案例

- Test Scenario:
- Expected Result:
- 測試依據與對應假設／證據 ID：
- 建議的重現、回歸與相容性檢查：
- 執行狀態：建議／未執行；若確實執行，結果放入第 4 節，不得把預期結果寫成實際結果。

## 7. 未確認事項

- Unverified Assumptions:
- Missing Information:
- Further Investigation:

### 技術未知（Technical Unknowns：Agent 應繼續研究）

| 問題 | 已查證的來源與證據缺口 | 下一個可行的研究／驗證步驟 | 限制或阻礙 |
|------|------------------------|----------------------------|------------|

### 領域決策（Domain Decisions：需要 Engineer 確認）

| 具體問題與上下文 | 已研究的文件／程式碼／測試／Issue 討論 | 仍無法確定的預期行為／業務決策 | 可選方案及影響 |
|----------------|-----------------------------------------|--------------------------------|----------------|

先研究現有證據，只有證據不足且涉及需求／業務決策時才列為 Domain Decisions。可自行查證的技術問題不轉交 Engineer。無此類問題時填「無」；未取得資訊填「未知／未驗證」。本節記錄問題，不實作後續釐清或修改授權流程。
