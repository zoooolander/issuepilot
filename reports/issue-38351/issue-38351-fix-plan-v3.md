# Issue #38351

## 1. Problem & Root Cause

- Issue／Repository：[create_agent: model_to_tools router can return "model" but path_map omits it](https://github.com/langchain-ai/langchain/issues/38351)，langchain-ai/langchain，擷取時為 closed；關閉狀態不證明本機版本已修復。
- 本機路徑：`C:\D\projects\langchain`；分析 SHA：`5893459c4f2bfac6c8d3262cae1e3f2246d9287f`。Version Selector 於本次工作階段（2026-11-04）回傳 `is_dirty=false`、`worktree_status=clean`；origin 的安全識別為 github.com/langchain-ai/langchain。
- 本次審閱入口為 `issue-38351-fix-plan-v3.md`，修訂識別 v3。歷史參考：[初始分析](issue-38351-analysis.md)、[舊方案](issue-38351-fix-plan.md)、[v2](issue-38351-fix-plan-v2.md)；僅確認檔名存在，未將歷史內容當成本次證據，亦未覆寫。
- 證據來自安裝於 `C:\Users\chris\.agents\skills\issuepilot` 的 Skill、其 Fetcher／固定 SHA Inspector。本次已接觸 Issue 本文的診斷與建議 diff，不宣稱盲測；未取得實際修復 PR／commit。

### Problem

- E01（Issue 回報）：在有一般工具、無 response_format、無 after_model 的配置，wrap_model_call 透過 ExtendedModelResponse 的 Command 注入與所有 tool_call_id 相符的 ToolMessage。預期應再次呼叫模型處理結果；回報實際在 LangGraph branch dispatcher 發生 `KeyError('model')`。作者宣稱於 langchain 1.3.10 重現，這不是本次 Agent 的執行結果。
- 本機選定版本為 langchain 1.3.18；其依賴宣告 langgraph >=1.2.11,<1.3.0。不可將作者版本、Issue 連結 SHA 或目前 HEAD 的執行結果混用。

### Root Cause

下列路徑及行號均來自上述完整 SHA 的 Inspector 讀取：

- E02／DR01：`libs/langchain_v1/langchain/agents/middleware/types.py:290–324` 定義 ExtendedModelResponse，明定 Command 作為額外更新經 reducer 套用，messages 與模型訊息並存；goto/resume/graph 不受支援。`factory.py:237–260` 確實先建立模型更新，再附加 middleware commands。這是合法的狀態更新機制，並不等同 middleware 可任意指定路由。
- E03／DR02：`libs/langchain_v1/langchain/agents/factory.py:1644–1667` 定義 loop entry／exit；有 before_model 時入口為該 hook，否則是 model；無 after_model 時出口是 model。`1701–1722` 僅在 response_format 為真或 loop_exit_node 不為 model 時，把 loop_entry_node 加入 model_to_tools_destinations。
- E04／DR03：同檔 `1944–1976`，router 依最後 AIMessage 與其後 ToolMessage 的 tool_call_id 排除已回覆呼叫。有未完成一般工具呼叫時回傳 Send；沒有 AIMessage 或沒有 tool_calls 時離開；有 structured_response 時離開；其餘有 tool_calls 而無 pending 呼叫時回傳 model_destination。這個回返條件沒有 E03 的配置限制。
- E05：`libs/langchain_v1/tests/unit_tests/agents/middleware/core/test_wrap_model_call_state_update.py:30–56` 的 assertions 要求模型與 Command 訊息並存；同檔有非同步、composition 與不支援 Command 欄位的測試。這支持 DR01 的測試契約，不代表測試已在本次通過，也不證明 synthetic ToolMessage 路由已有完整覆蓋。
- E06：`libs/langchain_v1/langchain/agents/__init__.py:3–9` 匯出 create_agent；方案不改其公開 signature、參數或回傳型別。

H01：DR01 可產生 DR03 的「所有呼叫均已回覆」狀態，DR03 回傳的 loop_entry_node 卻不在 DR02 的目的地清單。對「回傳集合與目的地清單不一致」的靜態判斷信心為 **High**；對目前環境實際拋出同一 KeyError 的判斷仍屬未驗證。直接證據支持回返模型的意圖；不能僅因 Issue 有建議修法就視為已驗證修復。

重現：**未驗證**。本次只執行唯讀證據擷取，未安裝依賴、匯入目標套件或執行 Issue 範例／pytest。沒有本次 runtime traceback、測試退出碼或修復結果。

技術限制與下一步：
- 未取得 Issue comments、LangGraph dispatcher 的版本對應原始碼；其 KeyError 機制目前依 E01 回報，待後續獲授權以鎖定環境重現確認。
- 搜尋僅擴及 agents 單元測試與 package lockfile；已完成的搜尋 complete=true、stop_reason=null，不能推論整個 repository 無其他契約。人工訊息搜尋還命中 tool_call_limit 及 response_format 測試，未讀完整內容，故不據此新增行為承諾。
- 首次完整 factory 輸出被顯示層截斷，已透過同 SHA 的重讀取得關鍵完整行段。猜測的 tests/conftest.py 不存在，後以限定範圍列檔找到並讀取 unit_tests/conftest.py 及 agents/conftest.py。
- 測試環境尚未建立或驗證；unit_tests/conftest.py 會匯入 vcr，故僅同步 test group 不足以保證 collection，規劃使用鎖定的全部 groups。無法 collection 時須記錄實際缺件，不得擅自新增或升級依賴。

### Proposed Fix

以下是待 Engineer 審閱的方案，並未授權實作：

- Change01：只修改 `libs/langchain_v1/langchain/agents/factory.py`，將 model_to_tools_destinations 建構為包含 tools、exit_node、loop_entry_node 的清單，刪除原條件式並更新相鄰註解，讓 DR03 的既有可達回返路徑被登記。不改 router 的判斷優先順序。
- Change02：只修改 `libs/langchain_v1/tests/unit_tests/agents/middleware/core/test_wrap_model_call_state_update.py`，新增有型別提示的 fake-model regression，涵蓋同步與非同步、全部／部分／零工具回覆、before_model 回返入口、既有 after_model／結構輸出配置。新測試命名以 `test_synthetic_tool_messages_` 為前綴，集中於 `TestSyntheticToolMessagesRouting`。
- 以兩次模型輸出構成有限流程：第一次提出呼叫，第二次回傳終止文字。全部已回覆時真實工具執行次數為 0；部分已回覆時只執行其餘呼叫；驗證 messages 順序、call ID、最終內容、模型次數與 hooks 次數，而非只檢查不拋錯。
- 風險：新增圖上的回返邊可能改變圖形呈現；before_model 必須重跑正確入口，避免直接跳過 hook。middleware 若持續製造 tool_calls 可能形成迴圈；測試使用有限輸出與明確 recursion_limit，方案不變更正式 recursion_limit。
- 排除：不處理 Issue 提及的獨立 _resolve_jump 稽核、不變更公開 API／signature、LangGraph／core／其他 middleware、版本／lockfile、文件及歷史報告；不執行 commit、push、PR、fetch、checkout、reset 或外部發布。
- 未來修改 allowlist 僅上述兩個檔案；環境寫入及驗證範圍見第 3 節。本次授權仍只有分析與新報告輸出。
- 未來獲准批次預算：每個技術阻礙最多 3 次 Diagnose → Fix → Retest、30 分鐘主動調查；整批最多 60 分鐘；每個命令最多 10 分鐘，先達者停止。連續兩次同樣失敗且無新增證據即停止，不以換工具或續跑重設預算。
- 停止條件：新 Domain Decision、HEAD／使用者變更衝突、超出 allowlist、依賴／Python 或驗收條件需改動、缺少工具權限、預算／無進展限制。不得刪弱測試、忽略相關失敗或降低驗收。

## 2. Open Questions & Engineer Decisions

**None**。目前證據足以支持登記既有回返路徑，未發現需要 Engineer 選擇產品政策的分歧；環境可用性與實際重現是技術驗證事項，不是假造的 Domain Questions。

## 3. Testing & Verification

- 以下全部為未執行的後續驗證規劃，需要獨立修復及環境授權。依據 `libs/langchain_v1/pyproject.toml:24–30,63–103`、兩份 conftest 及現存 uv.lock，使用 uv 管理 package 內 .venv；不沿用 IssuePilot 的 Python 作為測試環境。
- cwd 固定 `C:\D\projects\langchain\libs\langchain_v1`。Python 遵守 requires-python >=3.10,<4，不自行指定全域版本；同步後需記錄實際 Python、依賴與 uv 版本。既有鎖定環境無法解析或 collection 失敗時，停止並提出新版方案，不臨時升級或替換。
- 預計允許環境寫入僅 package 的 .venv、`C:\D\projects\issuepilot\reports\.uv-cache-38351-v3`、`C:\D\projects\issuepilot\reports\.tmp-38351-v3`；設定 UV_CACHE_DIR、TEMP、TMP 指向後兩者，PYTHONDONTWRITEBYTECODE=1。安裝可下載鎖定依賴與 uv 所需資產，仍須工具權限；測試禁止 sockets，LANGGRAPH_TEST_FAST=true，只用記憶體 fixtures。
- 在測試子程序明確設定 LANGSMITH_TRACING=false、LANGCHAIN_TRACING_V2=false，清除追蹤 API key 的環境繼承但不讀取其值；不讀取 .env。pytest 停用 cacheprovider，logs 留本次 session；不寫 repository 報告、不啟用 coverage 或外部追蹤。editable 本地依賴可能有 build 副作用；若實際需在上述環境與兩檔 allowlist 外寫入，停止，不自動擴權。
- 後續精確命令（規劃）：先從 repo 根目錄執行 Version Selector、`git diff --name-only`、`git diff --cached --name-only` 與 `git ls-files --others --exclude-standard`，確認基線與無重疊變更；從 package cwd 執行 `uv sync --frozen --all-groups`。成功後使用 `uv run --no-sync python --version` 與 `uv tree --locked --offline` 記錄環境。所有 uv run 都不得隱式安裝。
- 修復前先只新增 Change02 regression，執行 `uv run --no-sync pytest -o addopts= -p no:cacheprovider --disable-socket tests/unit_tests/agents/middleware/core/test_wrap_model_call_state_update.py::TestSyntheticToolMessagesRouting`；要求至少核心全部回覆案例因目標路由錯誤失敗，而非 collection／fake model 寫錯。其後才套用 Change01 並以同命令重跑。
- 相容性命令：`uv run --no-sync pytest -o addopts= -p no:cacheprovider --disable-socket tests/unit_tests/agents/middleware/core/test_wrap_model_call_state_update.py tests/unit_tests/agents/middleware/core/test_wrap_model_call.py`。修復後所有新增及這兩份既有測試均須通過；相關 skip 不計為通過。每個命令超過 10 分鐘即停止並記錄未完成。
- 結束重跑 Version Selector 及上述 diff／untracked 清單，確認只有授權 patch；禁止清除任何既有使用者檔案。正式修復前仍需重新確認本節環境授權，工具批准不能代替 Engineer 的修復批准。

### Tests & Acceptance Criteria

| 情境 | 預期結果 |
|---|---|
| AC01／DR01–03：無 response_format、無 after_model，所有呼叫由同步 wrapper 回覆 | 修復前命中目標錯誤；修復後呼叫第二次模型並正常結束，工具執行 0 次，保留正確訊息與 ID。 |
| AC02：同條件的 awrap_model_call／ainvoke | 與 AC01 同樣可觀察結果，沒有 KeyError。 |
| AC03：兩個呼叫只回覆一個，另有零回覆對照 | 部分情境僅執行未回覆工具一次；零回覆走原有工具流程，不重跑已回覆工具。 |
| AC04：加入 before_model 或 after_model | 回返 loop_entry_node，hook 次數與順序正確，不跳過 before_model、不無限循環。 |
| AC05：結構輸出已完成／仍待產生 | 保留 DR03 的 structured_response 出口優先順序與原有重試，不以新增目的地改變判斷。 |
| AC06：模型無 tool_calls；無 middleware；既有 Command 更新及不支援欄位 | 正常結束，既有測試契約不退化；不支援 goto/resume/graph 仍拒絕。 |
| AC07：範圍與基線 | 僅兩個允許原始碼／測試檔有預期 patch；未更動 API、版本、鎖檔及使用者變更。 |

實際結果：Fetcher、Version Selector 及上述成功 Inspector 擷取為靜態證據；部分 sandbox 呼叫遭 Git ownership 拒絕，改以工具要求的原使用者權限執行唯讀 Inspector，未修改 safe.directory。未執行安裝、Bug reproduction、regression、相容性或修復後檢查，沒有任何通過宣稱。

驗收結論：**待驗證**。本次交付為 v3 分析與條件完整的待審方案，非已修復成果。尚待獲授權後確認鎖定環境、目標失敗與修復後結果；缺少該證據時不得宣稱 Bug 修復或整套 Skill 行為驗收通過。
