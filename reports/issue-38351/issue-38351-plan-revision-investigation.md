# Issue #38351 — Fix Plan v3 → v4 → v5 Read-only Root Cause Investigation

調查日期：2026-11-05（Asia/Taipei）  
範圍：IssuePilot 的規則、報告、Codex Session／Tool Logs；本次調查未執行 Implementation、安裝套件或修改環境。本文由先前對話中的調查結果保存而來，不改寫歷史 Fix Plan。

### A. Execution Timeline

**調查結論：兩次升版的直接觸發點，都是 Codex 選擇改變已核准的執行條件，而非 LangChain 修復策略改變。**  
但兩次改變的性質不同：v4 改變驗證語意；v5 擴大測試的 socket 權限，不能一概認定不必要。

本次已找到原始 Session／Tool Logs，並非僅根據報告推測：

- **S**：[實際執行 session](C:/Users/chris/.codex/sessions/2026/11/04/rollout-2026-11-04T23-19-51-01a1a725-23c8-7be2-a4d7-b3d1a463b99c.jsonl)，以下 `S:行號` 均指此檔。
- **H**：[history.jsonl](C:/Users/chris/.codex/history.jsonl:98)，第 98、108、109 行分別佐證 v3、v4、v5 的 Engineer Approval。
- 已讀取專案內及實際使用的安裝版 Skill／模板；兩份 `SKILL.md` 雜湊相同，兩份 `report_template.md` 也相同。
- 已比對 v3、v4、v5：**Change01、Change02 與 AC01–AC07 完全相同。**

以下時間依 session 的 UTC timestamp 轉為臺灣時間：

| 時間 | 實際事件 | 證據 |
|---|---|---|
| 11/04 23:43:10 | Engineer 核准 v3。 | S:109；H:98 |
| 23:43–23:44 | Git ownership 檢查造成 sandbox 阻擋；使用正式提權完成唯讀檢查後，又發現 `uv` 不在 PATH。Codex 停在 BLOCKED，沒有升版。 | S:125、130、144 |
| 23:48:03 | Engineer 提供既有 `uv.exe` 路徑，要求符合方案就沿用，不重新安裝。 | S:151 |
| 23:48:57 | Codex 明確表示沿用先前 v3 Approval 繼續。 | S:176 |
| 23:51:19 | `sync --frozen --all-groups` 成功，退出碼 0；建立 package `.venv`，安裝 85 個鎖定套件。 | S:192 |
| 23:51:31–23:51:40 | 先遭 cache lock 存取拒絕；正式提權重試後，Python 版本成功讀取，但 `tree --locked --offline` 解析失敗。 | S:198、202、205 |
| 23:52:31–23:53:11 | Codex 決定改成 frozen tree 加鎖檔雜湊，認定改變驗證命令，建立 v4。 | S:231、232、235、240 |
| 23:53:37 | Engineer 核准 v4。 | S:247；H:108 |
| 23:54:19–23:55:12 | frozen tree 成功；新增 20 個回歸案例。尚未修改正式修復邏輯。 | S:270、278、281 |
| 23:55:31 | 20 個案例全部在 asyncio setup 發生 `SocketBlockedError`，測試命令退出碼 1。 | S:285、288 |
| 23:56–23:58:02 | Codex 讀取本機 socket／pytest-socket 原始碼，判定 Windows asyncio 需要 loopback；認定放寬 socket 限制屬權限擴張，建立 v5。 | S:296、299、306、317、320 |
| 23:58:39 | Engineer 核准 v5。 | S:332；H:109 |
| 11/05 00:00–00:03 | 修正測試草稿後，修復前為 4 failed／16 passed；套用修復後 20 passed；兩份相容性測試合計 91 passed，完成交付。 | S:366、375、383、392、415 |

這個時間線也修正一項背景細節：**v3 核准後完成了環境建立，但正式原始碼修復直到 v5 核准後才套用。**

### B. v3 → v4 Root Cause

**直接原因：離線依賴紀錄命令失敗後，Codex 選擇替換命令及其驗證語意，再套用版本綁定規則。**

1. **最後成功步驟**  
   `uv sync --frozen --all-groups` 成功；接著 `uv run --no-sync python --version` 成功，得到 Python 3.14.10。

2. **首次阻礙與真正升版觸發點不同**  
   最早遇到的是 Git ownership、找不到 uv、cache lock 權限問題。這些問題都沒有直接造成升版。真正緊接升版決策的錯誤是：

   ```text
   No solution found when resolving dependencies ...
   python_full_version >= '3.15' ... PyPy
   Because langgraph was not found in the cache ...
   Packages were unavailable because the network was disabled.
   ```

   這是 `tree --locked --offline` 的輸出，**不能解讀成已同步的 CPython 3.14 環境不可用，也不能據此證明 lockfile 已失效**。〔S:205〕

3. **Codex 當時的判斷**  
   Codex 正確辨識 frozen sync 已成功，隨後自行選擇：

   ```text
   tree --locked --offline
             ↓
   tree --frozen --offline ＋ lockfile 前後 SHA256
   ```

   它公開說明「改用 `--frozen` 會改變 v3 的驗證命令」，因此依 Skill 建立 v4。〔S:231、240〕

4. **觸發停止的規則**  
   [SKILL.md:63](../../.agents/skills/issuepilot/SKILL.md#report-structure-and-approval-binding) 要求，對 commands、tests、acceptance、permissions 等內容的 **material changes** 必須升版並重新核准。另有一條更直接的方案限制：

   > 「既有鎖定環境無法解析或 collection 失敗時，停止並提出新版方案」

   這句是 **Codex 寫入 v3 的規則**，位於 [v3:55](issue-38351-fix-plan-v3.md#3-testing--verification)，不是所有環境錯誤天然必須遵循的 Skill 定義。

5. **新版本實際改變了什麼**  
   LangChain 修復策略、兩檔 allowlist、AC01–AC07 均未改變；但驗證保障有變：
   - `--locked` 會檢查鎖檔是否需要改變。
   - `--frozen` 直接使用既有鎖檔。
   - 前後雜湊只能證明檔案未變，**不能替代鎖檔與專案需求的一致性檢查**。

   v4 也將上述「解析失敗就提出新版方案」改成可在預算內調查的處理方式。〔[v4:55、65](issue-38351-fix-plan-v4.md#3-testing--verification)〕

**必要性判斷**

- **錯誤本身沒有必然要求建立 v4。** 可以先保留 v3 Approval，停在 BLOCKED，等待原有環境條件恢復。
- **一旦選擇上述替代驗證方案，重新核准有依據。** 它改變的不是單純執行檔路徑，而是驗證語意。
- 紀錄沒有證明「補齊 cache 後原命令一定成功」，也沒有證明不能恢復。Codex 當時沒有走完這條恢復路徑，而是選擇改方案。

因此，v4 是**可避免的方案選擇所導致的升版**，不是環境錯誤自動要求的升版；但不能將其簡化為毫無實質差異的重新 Approval。

### C. v4 → v5 Root Cause

**直接原因：原定「禁止所有 sockets」與 Windows asyncio 的初始化需求衝突；Codex 選擇允許 loopback，因而改變權限邊界。**

1. **最後成功步驟**  
   Python／frozen tree 記錄成功，20 個回歸案例已加入並成功 collection。〔S:270、281、288〕

2. **首次錯誤**  
   原定命令保留 `--disable-socket`。traceback 顯示：

   ```text
   ProactorEventLoop
   → _make_self_pipe()
   → socket.socketpair()
   → _fallback_socketpair()
   → pytest_socket.SocketBlockedError
   ```

   20 個案例都在 setup 階段失敗，尚未執行目標行為。〔S:288〕

3. **Codex 當時的判斷與停止原因**  
   讀取安裝的 pytest-socket 與 CPython `socket.py` 後，Codex 判定 Windows 使用 loopback TCP 建立 socket pair。它沒有直接停用保護，而是提出增加：

   ```text
   --allow-hosts=127.0.0.1,::1
   ```

   Codex 明確將此歸類為超出 v4 的 socket 權限，引用 Skill 的 environment permissions 變更規則，建立 v5。〔S:299、306、325〕

4. **新版本實際改變了什麼**  
   修復策略、原始碼範圍、依賴與 AC01–AC07 未變；但測試權限確實改變：
   - v4：全面阻止建立 socket。
   - v5：存在 allow-hosts 時，pytest-socket 改以連線白名單限制一般 socket connect，允許 loopback。

   即使命令保留 `--disable-socket`，實際保護語意也不同。[v5:69](issue-38351-fix-plan-v5.md#3-testing--verification) 已揭露此點。

**必要性判斷**

- **暫停是必要的**：Codex 不能自行放寬已明定的 socket 限制。
- **就選定的 loopback 解法而言，取得新權限核准是必要的**；依目前把環境權限綁定報告版本的 Skill，升版有明確依據。
- **整份 Fix Plan 重生不是技術上的必然要求**。若 Workflow 支援針對既有計畫追加環境權限核准，可避免完整方案升版；但目前規則沒有明確提供這條路。
- 後續 v5 實際解除初始化阻礙，提供了對診斷的執行佐證。〔S:356、375〕

### D. Skill / Workflow Gap Analysis

| 類別 | 有證據支持的發現 |
|---|---|
| **Skill 規則** | 已區分 BLOCKED 與 material change，但區分還不夠可操作。Phase 5 明定一般技術選擇不需重複核准，並說阻礙解除後、具備「任何必要的新核准」即可恢復；並非所有 BLOCKED 都使原核准失效。另一方面，第 63 行把 commands、tests、permissions 等廣泛綁定版本，沒有具體的 material 判準。 |
| **Template** | report_template.md 第 41 行同時允許範圍內自主診斷重測、要求實質變更升版；沒有提供環境恢復與局部權限追加的判定程序。模板沒有單獨要求這次 v4、v5。 |
| **Agent 判斷** | v3 自行加入「解析或 collection 失敗就提出新版方案」，比單純 BLOCKED 更強。v4 前，Agent 選擇替換驗證方式，沒有先把「恢復原命令」作為主要待解事項。這是升版鏈的重要促成因素。 |
| **環境問題** | uv 路徑、sandbox 身分／cache lock、離線 registry cache、Windows asyncio loopback 需求，是不同問題；不能統稱為需要重規劃的依賴失敗。 |
| **Engineer 指令** | Engineer 提供 uv 路徑時明確要求符合方案就繼續。Codex 確實依此沿用 v3。沒有找到 Engineer 在 v4、v5 建立前要求重做 Fix Plan 的指令；升版提議來自 Agent，Engineer 之後才核准。 |

規則來源：[SKILL.md](../../.agents/skills/issuepilot/SKILL.md)，尤其第 63、129、131、139–149 行；[report_template.md](../../.agents/skills/issuepilot/references/report_template.md)，尤其第 41 行。行號為調查時讀取的版本。

關鍵對照是：

- **uv 路徑補齊、正式提權處理 ownership／cache lock：沿用原計畫恢復。**
- **替換鎖檔驗證語意、放寬 socket 權限：Agent 將其視為 material change。**
- **v5 後修正測試草稿的阻塞呼叫與錯誤預期：在原核准內修正，沒有再升版。**

所以問題不是「Skill 規定每次錯誤都要新 Fix Plan」，而是**恢復措施與方案變更的界線不夠明確，加上 Agent 選擇了會改變執行合約的解法**。

**證據限制**

核心核准、升版決策、建立報告的工具呼叫、錯誤與最終測試結果均已找到。部分當時儲存的長篇工具輸出本身有截斷；未取得原命令恢復後的試跑證據，因此不能聲稱 v3 一定可直接完成。未重新執行任何命令來驗證這些反事實情境。

### E. Recommended Changes

**有證據支持的最小改善**

1. **明文保留 BLOCKED 前的核准。**  
   加入規則：執行檔定位、既有權限取得、原定環境修復若不改方案語意，僅記錄 blocker／解除證據，重新 preflight 後沿用原版本。

2. **刪除「解析／collection 失敗就提出新版方案」這種一律升版條件。**  
   改為先分類、診斷；只有解法真的改變行為、範圍、驗證保障或權限才進入 revision gate。

3. **以語意判斷 material change，而非命令字串是否改變。**  
   完整執行檔路徑通常是工具定位；`--locked` 改成 `--frozen` 則改變驗證保障。本次兩者應分開處理。

4. **支援局部環境權限追加核准。**  
   若修復策略、allowlist、AC 不變，可對 loopback 等具體權限做明確追加核准，保留原 Fix Plan；不得因此讓 Agent 自行放寬保護。

5. **規劃階段核對平台與驗證命令。**  
   至少確認 Windows 非同步測試的本機通訊需求，以及依賴紀錄究竟要「讀取鎖檔」還是「驗證鎖檔一致性」，避免把兩種目的混在同一條命令。

**尚待驗證**

- 補齊離線 cache 後，原 v3 `tree --locked --offline` 是否能成功。
- 只追加環境核准、不升整份 Fix Plan 的規則，是否能讓實際 Agent 穩定遵循。
- 新分類規則是否能同時避免不必要升版，並保留對驗證降級／權限擴張的有效控制。

本次調查僅讀取與比對資料，未修改 Skill、模板、Fix Plan、Target Repository 或環境。調查完成後，依 Engineer 後續指示單獨保存本報告；不代表已授權或執行上述建議。
