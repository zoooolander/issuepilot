# Issue #38351

## 1. Problem & Root Cause

- Issue：[LangChain #38351](https://github.com/langchain-ai/langchain/issues/38351)；Repository：`langchain-ai/langchain`。
- 本機路徑：`C:\D\projects\langchain`；分析 SHA：`5893459c4f2bfac6c8d3262cae1e3f2246d9287f`。
- 最後已記錄的 HEAD 與上述 SHA 相同、工作目錄 clean；執行前須重新確認並保護 staged／unstaged／untracked 使用者變更。

### Problem

- **預期行為**：Middleware 補齊普通工具結果後，Agent 返回模型迴圈入口，處理工具結果並完成回答。Issue 描述及 router 的 artificial tool messages 分支支持此預期。
- **實際行為**：真實 `agent.invoke()` 在 Graph 分派時拋出 `KeyError('model')`。Issue 作者回報版本為 1.3.10；本次獨立重現使用 1.3.18，兩者不是相同環境。

### Root Cause

- `create_agent` 只在部分組態登錄 `loop_entry_node`，但 router 在所有工具呼叫已有對應結果、沒有 structured response 時仍會返回該入口。本案回傳 `model`，已登錄目的地卻只有 `tools`、`__end__`。
- 必要來源（均為上述 SHA）：`libs/langchain_v1/langchain/agents/factory.py:1655–1673,1701–1722,1906–1978`；訊息追加契約見 `libs/langchain_v1/langchain/agents/middleware/types.py:291–324`。
- **CK01 已重現**：真實 `agent.invoke()` 在 LangGraph `_branch.py:203` 自然拋出 `KeyError('model')`，Python exit 1，支持上述因果；不代表修復後已通過。環境、命令與結果見[重現紀錄](../../reproductions/38351/CK01-result.md)，完整證據由該紀錄連結；原始程式及 logs 保留，不重跑或改寫。
- 限制：這只驗證該環境的同步修復前案例，不代表修復成功、async／回歸測試通過。Python 3.14 有 Pydantic V1 相容性警告；pytest／BlockBuster／Windows async 及 snapshot 影響仍待實測。Issue 本文已揭露診斷，不能宣稱盲測；官方 Fix PR #38355 尚未讀取。

### Proposed Fix

| 項目 | 預計修改的檔案與內容 |
|---|---|
| C01 | `libs/langchain_v1/langchain/agents/factory.py`：目的地無條件包含既有 `loop_entry_node`，更新相關註解；保留正確 before_model 入口，不硬編碼 model，不改 router／reducer／公開 API。 |
| C02 | `libs/langchain_v1/tests/unit_tests/agents/middleware/core/test_wrap_model_call_state_update.py`：新增完整 Graph sync／async、部分回覆、hook、終止及相容性測試，另檢查有工具 Graph 的合法入口邊；不修改既有斷言。 |
| C03 | **排除 snapshot 修改**；若實測證明需要，先回報具體差異並升版重新核准。 |

**風險與停止條件**：LangChain 寫入僅限 C01／C02 兩檔；不改 core、LangGraph、設定、lockfile、其他測試、snapshot 或需求。環境／測試未執行不視為通過，失敗或 skip 逐項回報。缺權限、使用者變更重疊、換 SHA／Python／依賴、越界／高風險、新 Domain Decision、需要 C03 或降低驗收時停止相關操作並重新核准，不刪弱測試、不停用必要 fixture、不繞過限制。每阻礙最多 3 循環／30 分鐘、每批 60 分鐘、單命令 10 分鐘，先到即停；連續 2 次同錯無新證據即停，保留證據與工作並回報具體協助。禁止提前讀 #38355、Commit／Push／PR 或自動清理。

## 2. Open Questions & Engineer Decisions

| AI Agent Question | Engineer Decision |
|---|---|

**None**

目前沒有需要 Engineer 決定的 Domain／需求／行為選項。新問題新增 Q ID 並再次提問，未答填 Pending；第二欄只記錄 Engineer 的明確回答與來源，可多輪或修訂舊回答，保留被取代紀錄。技術問題由 Agent 優先調查，不把建議當成 Engineer 決策；回答問題不等於修復核准。

## 3. Testing & Verification

- 必要測試條件：規劃使用 Python 3.14.10／uv 0.13.7，測試依賴依指定 checkout 的 lock 固定，不更新 lock 或改用 registry 的 LangChain／core；須確認載入 checkout 來源。forbiddenfruit 的 build-only 例外維持 setuptools 80.9.0／wheel 0.45.1、FFRUIT_EXTENSION=false，不隱性新增建置依賴。
- 安裝與測試寫入僅限 `C:\D\projects\issuepilot\reproductions\38351\verification-r4` 的新環境、cache／temp／logs，不覆寫既有目錄或 CK01 紀錄；只有套件下載可連 PyPI／files.pythonhosted.org。測試禁止外部連線、LLM、Docker／DB、coverage 與 snapshot-update，保留必要 plugins／fixtures；工具與 Sandbox 權限仍須遵守。環境建置及測試尚未執行，相容性風險見下方。

### Tests & Acceptance Criteria

先完成環境／來源檢查與兩個既有測試模組的基線，再新增 C02 取得真實 red 失敗，套用 C01 後重測 green，最後完整執行 state-update 與 `tests/unit_tests/agents/middleware/core/test_diagram.py`。不能只測 router 回傳值。

| 情境 | 預期結果 |
|---|---|
| CK01：修復前最小案例 | 真實 Graph 在指定觸發條件下產生目標例外，建立比較基線；未重現也如實記錄。 |
| CK02／AC01：全部工具結果已補齊，執行 invoke／ainvoke | 完成回答、模型兩輪、工具零次，訊息配對保留，沒有入口 KeyError。 |
| CK03／AC02：只補部分結果，或結果的 call ID 不匹配 | 只執行未回覆工具一次，不匹配的 call ID 不吞掉待執行呼叫。 |
| CK04／AC03：配置 before_model、before_agent、after_agent 或 after_model hooks | before_model 每輪先於模型；before_agent 一次、after_agent 完成一次；after_model 順序保留。 |
| CK05／AC04：一般工具、無呼叫、structured output、舊回傳型別及禁止 Command 欄位 | 既有執行與終止行為、舊回傳型別維持；禁止欄位仍拒絕。 |
| CK06／AC05：既有 diagram 與有工具 Graph 的入口邊 | 只出現合法入口差異，沒有無關節點／路由變化；需要 C03 時停止並另行核准。 |

- 實際狀態：CK01 已重現；CK02–CK06 均未執行，C01–C03 尚未實作。表格描述的是預期，不是測試通過結果。
- 驗收結論：**待驗證**；修補後須記錄基準 SHA 加工作目錄 patch，不能與修復前結果混用。未執行、失敗或 skip 不算通過。
- 剩餘風險與未完成事項：環境安裝／pytest collection、Windows／Python 3.14 相容性、async／hook／部分工具回歸及 snapshot 影響仍待核准後驗證；若受阻，依第 1 節的預算及停止條件處理。
