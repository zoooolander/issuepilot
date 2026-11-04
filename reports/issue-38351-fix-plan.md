# Issue 38351：Day 11 領域理解與修復計畫驗收

## 1. Issue 摘要

- Repository：`langchain-ai/langchain`；本機 `C:\D\projects\langchain`。Repository 對應關係沿用 Day 10 已確認的 origin，並由本次套件 metadata 的 Repository URL 補強（E09）；本次未重新讀 remote。
- Issue URL：https://github.com/langchain-ai/langchain/issues/38351
- Issue Title：`create_agent: model_to_tools router can return "model" but path_map omits it -> KeyError('model')`
- Issue 狀態：`closed`，來源為本次 `github_fetcher.py`（E01）；不代表此 HEAD 已修復。
- Analysis Commit SHA：`5893459c4f2bfac6c8d3262cae1e3f2246d9287f`。
- 版本來源：本次 `version_selector.py` 取得目前 checkout HEAD，與 Engineer 指定 SHA 完全一致。
- 工作目錄：`worktree_status: clean`、`is_dirty: false`；dirty 確認不適用。檢查日期 2026-11-04，為 Agent 紀錄，工具未提供時間欄位。
- 分析範圍：固定上述 SHA，排除 staged、unstaged、untracked 內容；只補充 Day 11 所需證據，未重新進行完整 Day 10 RCA。
- RCA 起點：`C:\D\projects\issuepilot\reports\issue-38351-analysis.md` 第 1–7 節及 Day 10 後續驗收紀錄（E00）。原報告未覆寫；其工具測試通過紀錄不是 LangChain bug 重現證據。
- Problem Description：middleware 在模型節點補入工具結果後，router 允許返回迴圈入口，但特定建圖組態沒有登錄此目的地。
- 預期行為：無 `response_format`、無 `after_model`、一般非 `return_direct` 工具的情境，所有呼叫已有對應工具結果時，返回迴圈入口，讓模型消化結果並產生最終回答。來源為 Issue 的明示期望（E01），以及 router 的 artificial messages 註解（E04）；訊息追加契約另有文件與測試支持（E05–E06）。不可僅由修補建議推導此期望。
- 實際行為：Issue 作者回報 LangGraph `_branch.py` 的 `self.ends[r]` 拋出 `KeyError: 'model'`，聲稱在 `langchain==1.3.10` 驗證。這是回報，非 Agent 觀察。目前分析套件 metadata 為 `1.3.18`（E09），不能視為同一執行環境。
- Bug 重現狀態：**未驗證**；重現紀錄：**未執行**。未執行測試、安裝依賴或實作修補。
- 分析獨立性：Day 10 與本次均接觸 Issue 本文的診斷及建議修補；不宣稱盲測。未讀官方 Fix PR、修復 diff、修復 commit 或 Issue 內另一 SHA 的原始碼。Issue 留言未取得。

最小領域脈絡：`create_agent` 建立 agent graph；模型節點產生含 `tool_calls` 的 `AIMessage`。`ExtendedModelResponse.command` 可透過 reducers 追加 state 訊息；本案用 `ToolMessage.tool_call_id` 對應呼叫 ID。router 只取最後一個 AI 訊息及其後的工具訊息，排除已回覆及 structured-output 工具，再決定派送 `Send("tools", ...)`、結束或返回模型迴圈入口。入口可能是 `before_model`，而不是字面值 `"model"`；出口可能是 `after_agent` 或 END。上述為靜態實作及內嵌文件；預期契約的證據層級詳列 DR01–DR06。

## 2. 相關原始碼

以下路徑均相對 Repository root，版本均為第 1 節 SHA。行號來自 Inspector 成功讀取的完整文字，而非搜尋片段。E 編號是本報告命名空間，與 Day 10 的 E1 等分開。

| File | Function / Class | Relevant Lines | Analysis SHA | Reason / Evidence ID |
|---|---|---|---|---|
| `libs/langchain_v1/langchain/agents/factory.py` | `create_agent` | 1655–1673、1701–1722 | 第 1 節 SHA | 迴圈入口／出口、目的地登錄；E02–E03 |
| 同上 | `_fetch_last_ai_and_tool_messages`、`_make_model_to_tools_edge` | 1906–1978 | 同上 | ID 配對、pending 分派與返回入口；E04 |
| 同上 | `_build_commands` | 213–260 | 同上 | 模型訊息與 middleware commands、禁止 goto/resume/graph；E07 |
| `libs/langchain_v1/langchain/agents/middleware/types.py` | `ExtendedModelResponse`、`ModelCallResult`、`AgentState` | 291–324、349–354 | 同上 | 內嵌文件與 reducers；E05 |
| `libs/langchain_v1/tests/unit_tests/agents/middleware/core/test_wrap_model_call_state_update.py` | `TestBasicCommand`、`TestBackwardsCompatibility`、`TestAsyncExtendedModelResponse` | 30–56、199–249、252–281 | 同上 | 已存在的 additive、相容性與 async 測試斷言；E06 |
| `libs/langchain_v1/tests/unit_tests/agents/middleware/core/test_diagram.py` | `test_create_agent_diagram` | 13–194（斷言 95–194） | 同上 | Mermaid snapshot 相容性風險；E08 |
| `libs/langchain_v1/pyproject.toml` | project／dependency-groups | 24–30、64–84 | 同上 | 版本、Python、LangGraph 範圍及 test group；E09 |
| `libs/langchain_v1/Makefile` | `test`、`test_fast` | 40–47 | 同上 | 單元測試命令與 snapshot-update 風險；E10 |
| `libs/langchain_v1/langchain/agents/__init__.py` | exports | 3–9 | 同上 | `create_agent` 是公開介面；E11 |

檢索策略與實際限制：

1. 先依既有 RCA 的精確路徑讀 `factory.py`，再讀 middleware types；未做無限制 Repository 掃描。
2. 為補 Day 10 的測試缺口，在 `libs/langchain_v1/tests` 搜尋 literal `ExtendedModelResponse`，limit 30、max-output-chars 16000：exit 0，`complete=false`、`stop_reason=result_limit`、`truncated=true`、`scan_truncated=false`、`skipped_files=6`（non_text）；diagnostics：metadata_entries 57、candidate_files 57、bytes_read 376920。回傳片段的 `content_start_column=1`、`content_truncated=false`。這不是完整測試覆蓋率調查。
3. 在 `libs/langchain_v1/tests/unit_tests` 以 name `agent` 列檔、limit 80：exit 0，79 個候選；`complete=true`、`stop_reason=null`、兩種 truncated 均 false、skipped 0；metadata_entries 92、candidate_files 79、bytes_read 1240098。完整僅指該 scoped listing。
4. 依候選直接讀 state-update 測試（919 行）及 diagram 測試（194 行）。state-update 完整文字中 literal `ToolMessage` 與 `tool_calls` 均無匹配；只支持此檔缺少明示本案工具訊息案例，不能推論全 Repository 沒有回歸測試。`test_composition.py` 只有搜尋片段，不作完整檔案證據。
5. 首輪 PowerShell 未明示 UTF-8，中文顯示異常；模板與 RCA 以 UTF-8 重讀，未以亂碼判讀。首輪 Version Selector／Inspector 因沙箱 Git ownership 失敗，Issue Fetcher 因網路權限失敗；經核准於沙箱外唯讀重試成功。曾嘗試行程級 safe.directory 環境設定，仍遭 ownership 拒絕；未變更 Git config。
6. 批次完整輸出曾遇顯示截斷，後續以 Inspector 完整讀取後輸出選定行號／literal 核對補足；顯示截斷不等同 Inspector 搜尋截斷，未把未顯示內容當作已逐行檢閱。
7. 可取得文件採同 SHA 的內嵌 API 文件（E05），不混用未定版網頁。未查外部 LangGraph 原始碼、獨立 docs checkout 或 Issue 留言；沒有需要擴大範圍才能定義的產品選擇。

## 3. 根本原因假設

### H01：建圖目的地未涵蓋 router 的既有返回入口分支

- 延續 E00 的 H1，不重新執行完整 RCA。
- 已確認事實：E02 顯示入口可為 model 或 before_model；E03 只在 response_format 為真或 loop_exit_node 非 model 時追加入口；E04 在所有普通工具呼叫已有結果且沒有 structured_response 時返回 model_destination。
- 回報主張：E01 的 `KeyError('model')` 及作者環境重現聲明，未獨立驗證。
- 推測因果：middleware updates 經 reducer 形成預期 state，router 返回未登錄的 model，依 LangGraph 分派查表而失敗。state 形成及例外在本 SHA 的執行表現仍未驗證。
- Confidence：High，限於靜態目的地契約不一致；E02–E05 直接互相對照。執行期因果尚受 TU01 限制，非統計機率。
- 反證／限制：E06 支持追加訊息，但測的是 HumanMessage 與無工具回覆，不證明本案工具回覆分支已跑過。不同依賴版本的排程或分派可能改變症狀。structured_response 非空或仍有 pending calls 時不走最後返回分支（E04）。
- 驗證／推翻：CK01 在固定環境以完整 graph 重現；記錄 reducer 後的訊息順序、路由結果及例外。若 state 沒有形成，先追查 TU01，不宣稱所有 middleware 都必定觸發。

## 4. 支持證據

| Evidence ID | Evidence | Source | 行號 | 版本 | Observation |
|---|---|---|---|---|---|
| E00 | 既有 RCA 與後續工具驗收 | 第 1 節 RCA 檔案 | 第 1–7 節及後記 | 指定 SHA；Day 10 紀錄 | 既有分析起點，非本次 runtime 結果 |
| E01 | Issue body、title、state、labels | https://github.com/langchain-ai/langchain/issues/38351 | body 各標題 | 2026-11-04 取回；作者聲稱 1.3.10 | 回報、期望與建議；非獨立實測 |
| E02 | 入口可為 before_model，結束可經 after_agent | 第 2 節 factory.py | 1655–1673 | 第 1 節 SHA | 靜態事實及註解 |
| E03 | 條件登錄 loop_entry_node | 同上 | 1701–1722 | 同上 | 靜態事實 |
| E04 | 最後 AI 之後工具結果按 ID 排除；全數已答後返回入口 | 同上 | 1906–1978 | 同上 | 靜態事實，最後分支註解明示 artificial messages |
| E05 | command 與模型回覆共同更新、messages reducer、限制欄位 | 第 2 節 middleware/types.py | 291–324、349–354 | 同上 | 內嵌文件契約與型別 |
| E06 | 同步／非同步 additive 訊息斷言與舊回傳型別相容性 | 第 2 節 state-update 測試 | 30–56、199–281 | 同上 | 測試契約，未執行；非 ToolMessage 案例 |
| E07 | 模型 state command 在前、middleware command 追加；不支援 goto/resume/graph | 第 2 節 factory.py | 213–260 | 同上 | 靜態事實 |
| E08 | 多種 middleware graph 的 Mermaid snapshot 斷言 | 第 2 節 diagram 測試 | 95–194 | 同上 | 測試契約，未執行；snapshot 內容未讀 |
| E09 | langchain 1.3.18、Python >=3.10.0,<4.0.0、LangGraph >=1.2.11,<1.3.0 | 第 2 節 pyproject.toml | 24–30、64–84 | 同上 | 宣告依賴，非實際安裝版本 |
| E10 | test 帶 snapshot-update；test_fast 與 disable-socket | 第 2 節 Makefile | 40–47 | 同上 | 靜態命令，未執行 |
| E11 | 公開匯出 create_agent | 第 2 節 agents/__init__.py | 3–9 | 同上 | 靜態公開介面確認 |
| E12 | 本次 version selector | 第 1 節工具紀錄 | 不適用 | 第 1 節 SHA | exit 0、clean，非 Bug 重現 |

固定版本來源 URL 格式：`https://github.com/langchain-ai/langchain/blob/5893459c4f2bfac6c8d3262cae1e3f2246d9287f/<第2節路徑>#L<行號>`。上述所有成功 Inspector 呼叫 exit 0；GitHub fetcher 與 version selector 成功重試 exit 0。未執行任何 LangChain 測試或 Bug 重現；實測環境／命令／結果：無，**未驗證**。

### 領域規則（Domain Rules）

| Rule ID | 規則／預期行為 | 適用輸入、組態與條件 | 證據 ID | 性質與缺口 |
|---|---|---|---|---|
| DR01 | command 訊息與模型訊息經 reducer 共同保留 | wrap_model_call／awrap_model_call 回 ExtendedModelResponse，新增訊息使用不同 message IDs | E05–E07 | 文件及同步／非同步測試契約；非任意相同 ID 都只追加 |
| DR02 | 全部普通工具已有回覆時，返回迴圈入口處理結果 | 有 tools、最後 AI 有 tool_calls、ID 全數匹配、無 jump_to、無 structured_response；本案使用非 return_direct 工具 | E01、E04 | 明示期望及註解支持；完整 graph runtime 未驗證 |
| DR03 | 只派送尚未回覆的普通工具呼叫 | 最後 AI 之後的 ToolMessage 配對 tool_call_id；structured-output 工具另外處理 | E04 | 靜態實作推得之保留規則，不擴張為所有工具語義 |
| DR04 | 返回入口保留 before_model 執行順序；結束保留 after_agent | 有相應 hooks 時 | E02 | 內嵌設計註解與實作支持，不硬編碼 model 或 END |
| DR05 | 無 AI／無 tool_calls 結束；新 structured_response 且無 pending 時結束 | 無 explicit jump_to；分支優先序如 E04 | E04、E06 | 靜態規則及部分 no-tools 測試契約；非完整 structured-output 測試驗證 |
| DR06 | 修補不擴張 middleware command 的控制流程能力 | command.goto／resume／graph 仍不支援，保留既有回傳型別 | E05–E07、E11 | 文件與程式限制；不是新增產品政策 |

衝突處理：E03 的登錄條件與 E04 的最後分支不一致，兩者是同 SHA、同有工具 graph 的適用情境；不能以「未登錄」反推 artificial messages 不被允許。E05 與 E06 支持追加訊息，但不足以單獨證明工具回覆端到端成功；因此以 H01、TU01 保留執行期缺口。未發現必須由產品政策選擇才能化解的預期行為衝突。

## 5. 建議修復方式

### Fix Plan 草案

- Plan ID／revision：`IP-38351-D11`／`r1`（Agent 建立）。Repository／分析 SHA：完整基準見第 1 節。
- RCA 參照：E00 第 3–4 節；本報告 H01、E02–E07。
- 方案狀態：**草案，可供後續審核；runtime 與 snapshot 影響待驗證**。
- 核准狀態：**未核准（待 Day 12）**。此處只記錄狀態，不啟動 Day 12。
- 實作狀態：**未實作**。沒有修改目標 Repository；不代表修復授權。
- 修復目標：在 DR01–DR04 的合法工具結果狀態下，使建圖目的地包含 router 已支援的入口；保留 DR05–DR06。
- Proposed Change／Rationale：C01 只調整 create_agent 有 tool_node 分支的 model_to_tools_destinations，無條件包含既有 loop_entry_node，並更新附近過時註解。保留 router 分支、Send 內容、reducers 與終止優先序。既有合法路由已存在，因此修正登錄比改寫 routing 意義更小、更有證據支持。
- C02 在既有 state-update 測試模組補完整 graph 的合成 ToolMessage 回歸與保留行為測試；可沿用 fake model 模式，工具 binding fixture 細節由 TU02 驗證。C03 僅在 CK06 證實需要時，審閱並更新受影響 diagram snapshot；不預先指定快照差異。
- 公開 API：create_agent 已匯出（E11），方案不改公開簽章、參數、預設值或回傳型別；未提出任何簽章變更。
- 範圍外：Issue 額外提及的 `_resolve_jump` 稽核、LangGraph 通用分派設計、Command goto/resume/graph 新功能、工具授權／快取／HITL 政策、return_direct 合成結果的新語義、依賴升級與廣泛重構。
- 替代方案：硬編碼 `"model"` 雖小但會略過 before_model（DR04），不採；讓 router 在已有結果時結束會改變 DR02，不採；要求使用者補 after_model hook 是繞路而非修復現有契約；統一所有 router 與目的地生成可減少未來漂移，但超出局部 bug 範圍，暫不採。
- Potential Risks：新增圖邊可能影響 Mermaid 快照（TU03）；只測 router 不能抓到 path_map 缺陷；fake model 若沒有最終無工具回覆可能造成測試耗盡或持續迴圈（A01）；工具副作用若測試不計次會漏掉重複執行。新增目的地本身不應變更已工作的分支，但此為待 CK04–CK06 驗證的影響預期。
- 前提與阻礙：A01、TU01–TU03；Domain Decisions：**無**。沒有領域問題不等於方案已獲核准。

| Change ID／擬議修改 | 預期行為／Rule ID | 根因假設／證據 ID | Acceptance ID／觸發、可觀察結果及保留行為 | 建議 Check ID | 條件／阻礙 ID |
|---|---|---|---|---|---|
| C01 登錄 loop_entry_node 並校正註解；C02 graph 回歸 | DR01、DR02 | H01；E02–E07 | AC01：只有 wrap middleware、無 response_format／after_model，一個普通工具結果全數補齊時，invoke 與 ainvoke 均完成最終回答，模型兩輪，工具實體零次，訊息保留配對；不再因入口未登錄拋 KeyError | CK01、CK02 | A01、TU01、TU02 |
| C02 部分回覆與 hook 案例 | DR03、DR04 | H01；E02、E04 | AC02：兩個普通工具呼叫僅補其中一個，僅另一工具執行一次；AC03：全數補齊且有 before_model 時，每輪 hook 先於模型，before_agent 不重跑、after_agent 在完成時一次 | CK03、CK04 | TU01、TU02 |
| C01 保留原有分支；C02 相容性檢查 | DR05、DR06 | H01；E04–E07 | AC04：一般無注入工具循環、無工具呼叫終止、structured_response 結束及 after_model 順序維持；command 不支援欄位仍拒絕，舊 ModelResponse／AIMessage 回傳仍運作 | CK05 | TU01、TU02 |
| C03 有必要才更新受影響 snapshot | DR04、DR05（圖形呈現保留） | H01；E03、E08 | AC05：圖形正確呈現新增入口可能性；只接受可由 C01 解釋的邊差異，無不相關節點或路由變化 | CK06 | TU03 |

AC05 的具體快照差異尚未驗證，屬條件式提案。Day 11 僅產出草案，不要求本輪批准。未來具體方案未明確核准前不得修改；無回覆／拒絕均不授權，方案改變需重新核准。本次到此規劃階段停止。

## 6. 建議測試案例

所有 CK 均為**建議／未執行**，實際執行證據皆為「無（未執行）」；下列預期結果不是測試結果。

| Check ID／Acceptance | 情境與建議方法 | Expected Result | 依據 |
|---|---|---|---|
| CK01／AC01 | 在未修補固定 SHA，以可 bind_tools 的 fake model、普通工具、只含 wrap_model_call 的 middleware 執行 Issue 等價完整 graph；第一輪工具呼叫、第二輪最終回答 | 先記錄是否形成指定 state，以及是否發生回報錯誤；未重現也如實記錄，不預設此環境必然拋 KeyError | H01、E01–E07 |
| CK02／AC01 | 未來核准修補後，同步 invoke 及獨立 async wrapper 的 ainvoke；工具本體用計數／失敗哨兵，檢查完整訊息與兩次模型呼叫 | 最終回答、工具零執行、模型與合成訊息均保留；撤掉 C01 時回歸案例應失敗 | DR01–DR02、E05–E06 |
| CK03／AC02 | 兩個不同 call IDs，只補一個；另測未匹配 ID 仍保留 pending | 已回覆工具零次，未回覆工具一次；正常返回模型完成，不由錯誤 ID 吞掉呼叫 | DR03、E04 |
| CK04／AC03 | 加 before_model、before_agent、after_agent 記錄事件序列；另含 after_model 組態 | before_model 在兩輪模型之前，before_agent 一次、after_agent 完成一次；after_model 保持順序 | DR04、E02 |
| CK05／AC04 | 一般工具呼叫、無呼叫終止；router 的無 AI 邊界可單元測試；既有 state-update 相容性、structured-output 與 after_model 回歸 | 原終止優先序與舊回傳型別維持；禁止欄位依原例外拒絕。structured-output 不因新邊多跑模型 | DR05–DR06、E04、E06–E07 |
| CK06／AC05 | 執行既有 diagram 測試；人工檢查差異；必要時才逐筆核准 snapshot 變更 | 差異只對應合法入口邊；不可不看差異直接接受全部更新 | E08、E10 |

建議環境：從 `libs/langchain_v1` 使用 uv 管理 package 自己支援的 Python（E09），先經另行授權執行 `uv sync --group test`，再以 `uv run --no-sync --group test pytest --disable-socket tests/unit_tests/agents/middleware/core/test_wrap_model_call_state_update.py tests/unit_tests/agents/middleware/core/test_diagram.py` 作為已知檔案的定向命令。記錄實際 Python、langchain、langchain-core、LangGraph 版本及退出碼，停用 tracing，不接外部模型服務。`--no-sync` 避免隱性安裝。

新案例 node IDs、structured-output 具體既有測試選擇與 Windows fixture 相容性尚待 TU02；不虛構命令結果。必要時在後續授權範圍擴至 agents 的相關測試。E10 的 `make test` 會啟服務且帶 `--snapshot-update`，本案建議先用定向 pytest 審閱差異；本次未執行任何這些命令。

## 7. 未確認事項

- A01／未驗證前提：新增回歸使用一般非 return_direct 工具、合法唯一 call IDs／message IDs、wrapper 只為工具呼叫補結果、fake model 具有最終無工具回覆。依據 E01、E04–E06；CK01–CK04 確認。影響 C02／AC01–AC03；阻擋案例細節定案，不阻擋提出 C01。
- Missing Information：當前實際安裝依賴及 runtime state、完整測試覆蓋、snapshot 實際差異；不把 Issue closed 視為缺陷已不存在。
- Further Investigation：後續獲授權才做環境同步、重現與回歸；本輪已完成可在唯讀來源中取得的必要契約研究，不將執行授權缺口轉成產品決策。

### 技術未知（Technical Unknowns：Agent 應繼續研究）

| ID／問題 | 已查來源與剩餘缺口 | 下一個可行研究／驗證 | 限制／阻礙 | 影響範圍及是否阻擋定案 |
|---|---|---|---|---|
| TU01 本 SHA 的 reducer 排程及 LangGraph 分派是否確實產生同一例外 | E01、E04–E07、E09；已知依賴範圍，未知實際版本，未讀外部依賴或執行 | 後續授權環境中記錄版本，以 CK01 觀察 graph state／路由，再 CK02 對照 | 本輪僅唯讀研究，不安裝、不跑測試 | C01–C02／AC01–AC04；不阻擋草案，阻擋宣稱已重現／修復有效 |
| TU02 測試 fixture、完整現有覆蓋與新增案例精確位置 | E06 已支持 additive 與 async，該檔無 ToolMessage／tool_calls literal；搜尋 result_limit，非全測試已查 | 後續縮至 middleware/core、讀測試 model／conftest 並確認可 bind_tools fixture；再依 CK02–CK05 定向收集與執行 | 本輪未進一步檢閱所有鄰近測試；未驗證執行環境 | C02／AC01–AC04；需在實作前完成測試細節，不阻擋目前有界提案 |
| TU03 新增目的地造成哪些圖形差異 | E08 有 snapshot 斷言；未讀快照內容、未產生修補後 graph | CK06 產出並人工審閱 diff，確認是否需要 C03 | 未實作且未執行，差異未知 | C03／AC05；阻擋具體 snapshot 更新範圍定案，保留條件式 |
| TU04 Issue 討論／關閉原因未知 | 只有 E01 body／state，Fetcher 不含 comments | 如後續確有需求，取得不含修正內容的留言／關閉說明；避免 Fix PR | 本輪未取得，且不追 fix 連結 | 不阻擋 C01–C03／AC01–AC05；不影響依固定 SHA 建立草案 |

### 領域決策（Domain Decisions：需要 Engineer 確認）

**無。** E01 的期望、E04 的 artificial tool messages 分支、E05–E06 的 state-update 契約足以界定本案修復目標。未決項是 runtime 驗證、測試安排及圖形差異，屬 Technical Unknowns；沒有研究後仍需 Engineer 選擇的產品／相容性政策。範圍外的新語義不列為本次決策。

Day 11 完成判定：**符合本輪研究與規劃產出的完成標準**。已閱讀最新版 Skill／七節模板及既有 RCA、固定版本研究最小領域、分開事實／回報／推論、建立 E／DR／H／C／AC／CK／A／TU 追溯並記錄範圍、替代方案、風險與限制。此判定不是 Bug 重現或修復成功驗收；TU01–TU03 仍須後續獲授權的工作。未進入 Day 12，未實作 Bug Fix、未修改目標 Repository、未 Commit／Push。