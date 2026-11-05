# Issue #38351

本文件為目前工作報告；[初始分析](issue-38351-analysis.md) 與[舊 Fix Plan](issue-38351-fix-plan.md) 保留為歷史參照，不作為本次執行授權。

## 1. Problem & Root Cause

- Issue：[create_agent: model_to_tools router can return "model" but path_map omits it](https://github.com/langchain-ai/langchain/issues/38351)，記錄狀態 closed；Repository：`langchain-ai/langchain`。
- 本機路徑：`C:\D\projects\langchain`；固定分析 SHA：`5893459c4f2bfac6c8d3262cae1e3f2246d9287f`。
- 工作目錄與分析範圍：2026-11-04 的既有檢查記錄為 `is_dirty=false / worktree_status=clean`；結論針對上述 SHA，不代表目前狀態已重查。修改前須重新確認 HEAD，保護 staged／unstaged／untracked 使用者變更。

### Problem

- **預期行為及依據**：Issue 作者主張，僅有 wrap_model_call middleware、普通工具、沒有 response_format／after_model 時，middleware 補齊全部 ToolMessage 後，Agent 應回到迴圈入口，讓模型處理結果並完成回答；下述 router 靜態分支支持此方向。
- **實際行為及來源**：Issue 作者在 LangChain 1.3.10／Linux／Python 3.12.11 回報 Graph 分派 `self.ends[r]` 時拋出 `KeyError('model')`。本地基準宣告版本為 1.3.18，與作者環境不同；本次文件調整沒有執行重現。

### Root Cause

- **根因假設，High（定性信心）**：有工具時，建圖只在 response_format 為真或 loop exit 非 model 時登錄 loop entry，但 router 在工具呼叫全部已回覆、無 structured response 時仍可返回該入口。這個靜態不一致與歷史重現相符；已有 response_format／after_model 的組態不能概括為同樣故障，LangChain 靜態原始碼也不能證明外部 LangGraph 的全部 runtime 行為。
- **必要證據（均為上述 SHA）**：`libs/langchain_v1/langchain/agents/factory.py:1655–1673,1701–1722,1906–1978` 定義 loop entry、目的地集合及 router 分支；`factory.py:237–260`、`libs/langchain_v1/langchain/agents/middleware/types.py:291–323` 說明額外消息更新並拒絕 Command 的 goto／resume／graph。`libs/langchain_v1/tests/unit_tests/agents/middleware/core/test_wrap_model_call_state_update.py:30–56,58–83,85–114` 的既有斷言支持消息並存及 structured_response 衝突契約，是靜態證據，非測試通過結果。
- **須保留的行為**：全部結果已補齊時經正確 loop entry（含 before_model）；部分未回覆仍交給工具，保留既有終止分支與消息更新契約，不以刪除 ToolMessage 或硬編碼 model 修復。
- **重現證據**：歷史 [CK01](../../reproductions/38351/CK01-result.md) 的真實 invoke 在 LangGraph `_branch.py:203` 自然產生 `KeyError('model')`，exit 1；router=model，目的地僅 tools／__end__。這支持根因，但不是本次新跑、修復成功或 async／回歸通過。完整環境、命令及輸出見該紀錄與其[執行 metadata](../../reproductions/38351/ck01-run2.execution.json)、[stderr](../../reproductions/38351/ck01-run2.stderr.txt)。
- **尚存限制**：既有搜尋有 result_limit 截斷，後續已完整讀取找到的 state-update 測試，不能宣稱涵蓋所有測試；Issue comments／外部版本文件未取得。Issue 本文已揭露診斷，不能宣稱盲分析；既有 rerun 記錄稱未讀官方修復 PR／diff，本次未重新查證歷史曝露。runtime／async／snapshot 與 Python 3.14 相容性仍待驗證；鎖定環境、命令及寫入位置尚未完整確認，須先研究 lock／pytest 設定與來源載入方式，再呈交具體執行範圍，不能直接開工。

### Proposed Fix

| 變更 | 預計修改的檔案與內容 |
|---|---|
| C01 | `libs/langchain_v1/langchain/agents/factory.py`：有工具的 model-to-tools conditional edge 無條件登錄既有 loop_entry_node，更新相關條件註解；保留 tools／exit 目的地與 router 分支。 |
| C02 | `libs/langchain_v1/tests/unit_tests/agents/middleware/core/test_wrap_model_call_state_update.py`：新增真實 Graph sync／async、部分結果、hooks、終止與相容性測試及下述驗收；使用 fake model／本機工具計數，新增函式具型別。 |

- **範圍與權限**：兩檔是未來修復 allowlist，目前沒有目標寫入授權。保持 create_agent 公開簽章、參數位置、預設值與 reducer；排除 LangGraph、core、lock／設定、其他測試、snapshot、既有重現檔案及另案 _resolve_jump/tools audit。環境副作用見第 3 節；圖形差異若需 snapshot 修改，先呈現差異、修訂方案並重新核准，不批次更新。
- **主要風險**：新增合法圖邊可能改變 graph rendering；before_model 必須每輪正確執行；sync 成功不能證明 async，相容性及完整環境仍待確認。
- **停止條件**：HEAD／使用者工作變動、重疊修改、缺權限、越界或變更 Python／依賴／需求／驗收、新 Domain Decision、需改 snapshot、任何高風險操作均停止相關操作。不得刪弱測試、隱藏警告／失敗、停用必要 fixture、提前讀官方修復、Commit／Push／PR 或清理歷史成果；實質變更須重新核准。
- **執行預算**：有效核准後，每阻礙最多 3 次 Diagnose → Fix → Retest／30 分鐘、每批 60 分鐘、單命令 10 分鐘，先到即停；連續兩次同錯且無新證據即停。每次修正須有新證據支持的假設與結果，不因換工具、改名阻礙或續跑重置計數；等待 Engineer 不計入。受阻時保留工作與證據，回報已完成內容、原因／未知、嘗試與預算及具體協助。

## 2. Open Questions & Engineer Decisions

**None**。目前沒有研究後仍需 Engineer 決定的 Domain／需求／行為選項。環境與驗證準備屬技術問題，由 Agent 在授權範圍內調查；沒有問題不等於已核准修復。

## 3. Testing & Verification

- **必要測試條件與權限**：環境規劃使用 uv，依 requires-python／固定 lock 顯式準備並以不隱性安裝方式執行，不新增依賴或跨環境；須確認 checkout 來源載入。具體 Python／套件版本、命令、下載來源及 cache／temp／bytecode／pytest／editable 建置寫入位置尚未完整確認，不能宣稱只有 venv 有副作用。須補齊並明確授權後才可安裝或測試；目前不授權套件下載、LLM、tracing、Docker／DB、外部測試連線、coverage 或 snapshot 更新。歷史 CK01 的安裝紀錄不是未來安裝授權。

### Tests & Acceptance Criteria

先核對 baseline／workspace／來源與 tracing 隔離，再新增 C02 取得真實 red，套用 C01 後 green，最後跑相關既有 state-update 與 diagram 回歸。精確命令及權限未確認前不執行；不能僅斷言私有 router 回傳值，新增測試須能辨識移除 C01 後的故障。

| 情境 | 預期結果 |
|---|---|
| CK01：修復前完整 Graph，全部工具消息已補齊 | 自然產生目標 `KeyError('model')`，作為比較基線。 |
| CK02／AC01：sync invoke／async ainvoke，無 response_format／after_model，middleware 補齊全部工具結果 | 完成第二輪回答，工具執行零次，ToolMessage 與 call ID 保留，沒有入口 KeyError。 |
| CK03／AC02：多個呼叫只補部分結果，或結果 ID 不匹配 | 只執行尚未配對的工具，各一次；不吞掉 pending 呼叫。 |
| CK04／AC03：配置 before_model、after_model、before_agent／after_agent hooks | 第二輪仍先經 before_model；after_model 順序保留；before_agent／after_agent 只在整體進出執行一次。 |
| CK05／AC04：普通未補齊工具、無工具呼叫、structured response 終止、舊 ModelResponse／AIMessage、非法 Command 欄位 | 既有處理／終止／拒絕行為不變。 |
| CK06／AC05：有工具 Graph 的目的地與既有 diagram 回歸 | 包含合法 loop entry，無無關圖形變動；需要 snapshot 修改即停並重新核准。 |

- **實際狀態**：CK01 僅引用歷史證據，未重跑；C01／C02 未實作，CK02–CK06 未執行。既有 `tests/unit_tests/agents/middleware/core/test_diagram.py` 只曾列舉確認存在，內容未讀，執行前須核對配置與斷言。
- **驗收結論：待驗證。** 沒有本次 red／green、async、回歸或修復後結果。未執行、skip 與失敗不能算通過；未來結果須標記 baseline SHA 加實際 patch、環境／命令／exit code／原始輸出，不能混用修復前紀錄。
- **剩餘風險與未完成事項**：先補齊環境、命令、下載與寫入範圍，再依明確核准的範圍驗證 runtime／async／hooks／部分工具、環境相容性及圖形影響；受阻按第 1 節預算與停止條件處理。這些技術限制尚未解除，不代表修改預期行為。
