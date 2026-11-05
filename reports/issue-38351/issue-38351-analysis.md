## 1. Issue 摘要

**結論：目前 HEAD 仍存在「router 可回傳的目的地，未完整登錄於 `path_map`」的靜態缺陷，與 Issue 描述一致。根因信心為高；本次未執行重現，因此目前 HEAD 是否實際拋出 `KeyError('model')` 仍為未驗證。**

| 項目 | 分析紀錄 |
|---|---|
| Repository | `langchain-ai/langchain`；已確認本機 origin 對應此儲存庫 |
| 本機路徑 | `C:\D\projects\langchain` |
| Issue | [#38351](https://github.com/langchain-ai/langchain/issues/38351) |
| 標題 | `create_agent: model_to_tools router can return "model" but path_map omits it -> KeyError('model')` |
| Issue 狀態 | `closed`，來自 Issue Fetcher；不代表目前 HEAD 已修復 |
| 分析 SHA | `5893459c4f2bfac6c8d3262cae1e3f2246d9287f` |
| 版本來源 | Version Selector 取得的本機 HEAD |
| 工作目錄 | `clean`、`is_dirty: false`；無須排除未提交修改的確認 |
| 檢查日期 | 2026-11-03，代理執行紀錄 |
| 重現狀態 | **未驗證；未執行重現或測試** |

**預期行為：** middleware 提供對應的合成 `ToolMessage` 後，agent 應返回模型處理工具結果。來源為 Issue 描述；目前 router 的註解與實作也支持此預期。

**回報行為：** LangGraph 在 `self.ends[r]` 查表時拋出 `KeyError: 'model'`。這是 Issue 作者回報的結果，作者聲稱於 `langchain==1.3.10` 驗證；不是本次獨立執行結果。

**分析獨立性：** Issue 本文已揭露診斷與修補建議，本分析已接觸這些資訊，不能宣稱盲測 RCA。未查看修復 PR、修復 commit 或歷史 diff。全程未修改程式碼，未儲存報告檔案。

## 2. 相關原始碼

以下全部證據固定於上述分析 SHA；行號由 Inspector 回傳的完整檔案內容計算。

| 證據 | 檔案／符號 | 行號 | 關聯 |
|---|---|---:|---|
| E1 | `agents/factory.py`：`create_agent` 的迴圈節點選擇 | 1655–1673 | 無前後置模型 hook 時，入口與出口皆為 `"model"` |
| E2 | 同檔：`model_to_tools_destinations` | 1701–1722 | 條件式登錄返回模型的目的地 |
| E3 | 同檔：`_fetch_last_ai_and_tool_messages` | 1906–1924 | 取得最後 AI 訊息及其後的工具回覆 |
| E4 | 同檔：`_make_model_to_tools_edge` | 1927–1978 | 無待執行工具時，可直接返回模型 |
| E5 | 同檔：`_build_commands`、同步／非同步模型節點 | 213–260、1468–1489、1519–1540 | 保留模型輸出並追加 middleware commands |
| E6 | `agents/middleware/types.py`：`ExtendedModelResponse`、`AgentState` | 291–324、349–354 | 文件允許追加 state update；訊息使用 `add_messages` reducer |

檔案根目錄為 `libs/langchain_v1/langchain/`。固定版本來源：[factory.py](https://github.com/langchain-ai/langchain/blob/5893459c4f2bfac6c8d3262cae1e3f2246d9287f/libs/langchain_v1/langchain/agents/factory.py)、[middleware/types.py](https://github.com/langchain-ai/langchain/blob/5893459c4f2bfac6c8d3262cae1e3f2246d9287f/libs/langchain_v1/langchain/agents/middleware/types.py)。

**檢索限制：** 依 Issue 路徑定位 `agents/factory.py`，並以 `ExtendedModelResponse`、`artificial`、`_make_model_to_tools_edge` 搜尋測試。這些列舉／搜尋均回傳 `truncated=false`、`scan_truncated=true`、`skipped_files=1`，結果為空。因此不能推論檔案或測試不存在。核心證據改由 Issue 已提供的明確路徑直接讀取；未以搜尋片段推定行號。

## 3. 根本原因假設

### H1：建圖時的目的地集合，未涵蓋 router 的合法回傳值

**信心：高（High），限於靜態缺陷。**

已驗證事實：

- 未設定 `response_format`、未提供 `after_model` hook 時，E2 不會登錄 `loop_entry_node`。
- 未提供 `before_model` hook 時，`loop_entry_node == "model"`（E1）。
- 當 AI 訊息有工具呼叫、全部已有對應工具訊息，且沒有結構化結果時，router 會返回 `model_destination`（E3、E4）。
- middleware command 追加訊息屬於現有介面明文支持的行為（E5、E6）。

因此，在 Issue 的設定下：

```text
登錄目的地：["tools", END]
router 回傳："model"
```

**推定因果鏈：**

```text
模型輸出工具呼叫
→ middleware 追加相同 tool_call_id 的 ToolMessage
→ pending_tool_calls 為空
→ router 返回 "model"
→ 分支映射未登錄 "model"
→ 依 Issue 回報的 LangGraph 查表行為，拋出 KeyError
```

設計上的錯誤假設是：只有 `after_model` hook 或 structured output 才需要回到模型。實際上，`wrap_model_call` 也能產生「工具結果已補齊」的狀態。

**限制與反證條件：** 尚未驗證目前 LangGraph 的實際分派行為、reducers 執行結果及完整重現。若執行時未形成上述訊息狀態，或依賴版本採不同的分派方式，錯誤表現可能不同；但 E2 與 E4 的目的地契約不一致仍可直接確認。

## 4. 支持證據

| 證據 | 核心觀察 | 性質 |
|---|---|---|
| E1 | `loop_entry_node` 預設為 `"model"`；`loop_exit_node` 也預設為 `"model"` | 已驗證原始碼 |
| E2 | 只有 `response_format` 為真或出口不是 `"model"` 才追加入口 | 已驗證原始碼 |
| E3、E4 | 已回覆的工具呼叫會被排除；全部排除後可返回模型 | 已驗證原始碼 |
| E5、E6 | 模型訊息與 middleware command 可一起送入 state 更新 | 已驗證原始碼與內嵌文件 |
| E7 | `KeyError('model')` 發生於 LangGraph `_branch.py` 的查表 | [Issue 作者回報](https://github.com/langchain-ai/langchain/issues/38351)，未獨立重現 |

E2 的關鍵程式碼：

```python
model_to_tools_destinations = ["tools", exit_node]
if response_format or loop_exit_node != "model":
    model_to_tools_destinations.append(loop_entry_node)
```

E4 在排除待執行工具及結構化結果後：

```python
return model_destination
```

這個最終分支沒有要求 `after_model` 或 `response_format`，因此與 E2 的登錄條件不一致。

Inspector 最終相關檔案讀取成功，退出碼為 `0`。初次讀取曾遇到 Windows 輸出編碼問題，已以 UTF-8 重試成功；未使用失敗輸出作為證據。未取得 Issue 留言，未執行任何 bug 重現或測試。

## 5. 建議修復方式

**建議讓這條 conditional edge 無條件登錄 `loop_entry_node`，使目的地集合涵蓋 router 的既有行為。** 對應 H1、E1、E2、E4。

這項建議的範圍限於 `create_agent` 建圖邏輯，不需要變更公開函式簽章。預期結果是：合成工具結果補齊後，agent 可以返回迴圈入口，繼續產生最終回答。

需注意：

- 入口可能是 `before_model` hook，不能硬編碼為 `"model"`。
- 新增邊可能改變圖形輸出或快照。
- middleware 若持續讓模型產生同類工具呼叫，仍可能形成迴圈；模型應有終止回覆。
- Issue 提到的 `_resolve_jump` 是另一個議題，本次未將其確立為第二根因。

**實作狀態：僅為建議，未套用、未測試。**

## 6. 建議測試案例

以下均為建議，未執行。

| 情境 | 預期結果 | 依據 |
|---|---|---|
| Issue 最小案例：只有 `wrap_model_call`，注入全部工具回覆 | 不拋出 `KeyError`；模型再次被呼叫並完成回答；工具本體不執行 | H1、E2–E6 |
| 多個工具呼叫，只注入部分回覆 | 僅執行尚未回覆的工具 | E4 |
| 加入 `before_model` hook，全部工具已有回覆 | 經過正確迴圈入口，hook 在下一輪執行 | E1、E4 |
| 非同步 middleware 與 `ainvoke` | 與同步路徑相同 | E5 |
| 一般工具呼叫、無工具呼叫、structured output、`after_model` | 原有執行與終止行為維持正常 | E2、E4 |

關鍵回歸測試應執行完整 agent graph；單獨測 router 回傳 `"model"`，無法捕捉 `path_map` 漏登錄。

## 7. 未確認事項

### 技術未知

| 問題 | 證據缺口 | 下一步 |
|---|---|---|
| 目前 HEAD 是否實際重現相同例外 | 未執行；目前 LangGraph 實際版本未知 | 在對應套件環境執行隔離、無網路重現，記錄版本、命令與退出碼 |
| 現有測試是否涵蓋此情境 | Inspector 搜尋達掃描上限 | 取得明確測試路徑後，以相同 SHA 直接讀取 |
| Issue 為何關閉 | 未取得留言或關閉原因 | 唯讀取得討論；本次不以修復 PR 反推根因 |
| 修改目的地後是否影響圖形快照與其他組態 | 未實作、未執行回歸 | 執行第 6 節的測試矩陣 |

### 領域決策

**無。** 現有 router 註解與 middleware 文件已支持「工具結果補齊後返回模型」的預期，沒有必要將這個技術問題轉交為業務需求決策。

報告目前僅呈現於對話中。若需要保存，請指定並授權輸出目錄，預設檔名為 `issue-38351-analysis.md`。

---

## Day 10 後續驗收紀錄

本節依 Engineer 提供的後續驗收結果補記；保留以上七個章節的原始分析、證據與當時限制，不回寫首輪結論。

- 首次 RCA 已成功完成，但當時 Inspector 搜尋遇到掃描上限；核心證據改由 Issue 提供的明確檔案路徑取得。
- 後續已修正 `repo_inspector.py` 的大型 Repository 搜尋問題：分離 Metadata 走訪與候選內容額度，並支援子目錄 Scope。
- 修正後使用相同 LangChain SHA `5893459c4f2bfac6c8d3262cae1e3f2246d9287f` 重新驗證搜尋。
- 搜尋 Scope：`libs/langchain_v1/langchain/agents`。
- 搜尋線索：`_make_model_to_tools_edge`；成功找到 `factory.py` 中兩筆相關結果。
- 搜尋結果：`complete=true`、`scan_truncated=false`，此 Scope 的搜尋未發生截斷。
- 工具測試紀錄：Inspector 47/47、完整 unittest 96/96 通過；這些是 IssuePilot 工具測試，不是 LangChain Bug 重現測試。
- 報告目前已存檔於 `reports/issue-38351/issue-38351-analysis.md`；以上「未儲存／僅呈現於對話」的文字是首輪報告產生時的狀態。
- RCA 仍屬靜態分析，LangChain Bug 尚未實際重現，重現狀態維持「未驗證」。

這是後續工具驗收紀錄，不代表重新執行完整 RCA，也不代表 LangChain Bug 已修復或修復方案已套用。Day 10 依原定 Analysis MVP 標準驗收通過，不等於執行期根因或修復結果已驗證。
