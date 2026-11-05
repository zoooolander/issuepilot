# CK01 — LangChain #38351 修復前重現

## 判定

**成功重現**。兩次執行相同程式、相同環境與觸發條件，均由真實 LangGraph 分派自然產生 `KeyError('model')`，Python 程式退出碼均為 1。第二次僅為取得未經 PowerShell 格式化的 UTF-8 原始 stdout/stderr；首輪檔案保留。

本結果只證明以下 SHA／依賴／案例已重現，不代表完成修復、非同步驗證或完整回歸測試。Fix Plan 未因此獲得修復授權。

## 基準與環境

- Repository：`C:\D\projects\langchain`
- SHA：`5893459c4f2bfac6c8d3262cae1e3f2246d9287f`
- 執行前後 HEAD 相同，工作目錄 clean。
- Python：3.14.10，Windows AMD64；`reproductions/38351/.venv/Scripts/python.exe`。
- LangChain：1.3.18；langchain-core：1.6.1，均從指定 checkout 的來源直接載入，沒有安裝同名 distribution。
- LangGraph：1.2.11；Pydantic：2.12.5；uv：0.13.7。
- 所有已安裝 distribution 版本記錄在 `ck01-run2.stdout.jsonl` 的 `installed_distributions`。
- 原 lockfile 以 SHA 內容核對；已載入的 Repository Python 模組在 invoke 前逐檔與 commit 比較（換行正規化），路徑、SHA-256 及結果記錄在 `source_manifest`。Fake Model 來源另行核對。

來源位置：

- create_agent：`C:\D\projects\langchain\libs\langchain_v1\langchain\agents\factory.py`
- Middleware：`C:\D\projects\langchain\libs\langchain_v1\langchain\agents\middleware\types.py`
- core：`C:\D\projects\langchain\libs\core\langchain_core\__init__.py`
- Fake Model：`C:\D\projects\langchain\libs\langchain_v1\tests\unit_tests\agents\model.py`
- 分派：獨立環境 `Lib/site-packages/langgraph/graph/_branch.py`。

## 安裝紀錄

工作目錄：`C:\D\projects\issuepilot`。先確認 uv 不在命令搜尋結果內，建立獨立 venv 後才安裝 uv。首次沙箱下載因 WinError 10013 被拒；核准沙箱外重試成功。未接受 pip 的升級提示。

```powershell
& '.\.venv\Scripts\python.exe' -B -m venv 'reproductions/38351/.venv'
& '.\reproductions\38351\.venv\Scripts\python.exe' -B -m pip --log 'reproductions/38351/install-uv.log' install --cache-dir 'reproductions/38351/.pip-cache' uv
& '.\reproductions\38351\.venv\Scripts\uv.exe' export --project 'C:\D\projects\langchain\libs\langchain_v1' --frozen --no-dev --no-default-groups --no-emit-local --offline --no-python-downloads --cache-dir 'C:\D\projects\issuepilot\reproductions\38351\.uv-cache' --output-file 'C:\D\projects\issuepilot\reproductions\38351\requirements-locked.txt' --quiet
& '.\reproductions\38351\.venv\Scripts\python.exe' -B -m pip --log 'reproductions/38351/install-runtime.log' install --no-deps --require-hashes --only-binary=:all: --cache-dir 'reproductions/38351/.pip-cache' -r 'reproductions/38351/requirements-locked.txt'
```

使用 frozen lockfile 匯出帶 hashes 的 runtime requirements，排除本機 path packages，保留其 runtime 相依套件。`--no-deps` 防止 pip 額外解析或安裝 registry 的 LangChain/core；以 `sys.path` 直接載入本機兩個來源目錄，避免在 LangChain Repository 做 editable/build 安裝。這是 source-loaded 環境，不能將 distribution metadata 缺少 LangChain/core 解讀成未載入其來源。未安裝 pytest test group，也未執行既有 LangChain 測試。

## 重現程式與實際觀察

`reproduce_38351.py` 使用既有 FakeToolCallingModel，工具呼叫為第一輪、無工具呼叫為第二輪。普通 `@tool` 僅計數並回傳本機固定結果。只有 wrap_model_call Middleware；沒有 response_format、before_model 或 after_model。Middleware 透過真實 `handler(request)` 取得模型結果，再回傳 ExtendedModelResponse 與 Command(update=messages)。

沒有 Mock、monkeypatch、替換 Graph／Router／Reducer，沒有手動拋出 KeyError。例外捕捉只讀取 traceback frame 白名單欄位並重新拋出原例外，不影響原始執行。

- 模型執行次數：1。
- handler 呼叫次數：1。
- 工具本體執行次數：0。
- Middleware 追加 ToolMessage：1，`tool_call_id=call-38351`，匹配模型 tool call ID。
- 真實 branch `_route` frame 的 reducer 後訊息依序為 HumanMessage、AIMessage（含該 call）、匹配 ToolMessage。
- 真實 Router 結果：`model`。
- 真實 branch 登錄目的地：`{"tools": "tools", "__end__": "__end__"}`。
- `_finish` 查詢 `self.ends[r]` 時自然拋出 `KeyError: 'model'`；尚未到第二輪模型。

執行命令：

```powershell
& 'C:\D\projects\issuepilot\reproductions\38351\.venv\Scripts\python.exe' -B 'C:\D\projects\issuepilot\reproductions\38351\reproduce_38351.py'
```

程式自行停用 tracing，沒有外部 LLM 呼叫。第二次擷取使用 subprocess capture_output 與 `PYTHONIOENCODING=utf-8`、`PYTHONDONTWRITEBYTECODE=1`，原始 bytes 寫入新檔。完整執行 command、cwd 與退出碼見 `ck01-run2.execution.json`。

## 原始證據與限制

- `ck01-run2.stdout.jsonl`：版本、來源驗證、Middleware、state、路由、計數、前後 Git 狀態。
- `ck01-run2.stderr.txt`：完整原始 warning 與 traceback；呼叫鏈為 agent.invoke → Pregel stream/tick → runnable → branch._route → branch._finish → KeyError。
- `ck01-run2.execution.json`：執行命令及退出碼 1。
- 首輪 `ck01.stdout.jsonl`、`ck01.stderr.txt`、`ck01-exit-code.txt` 保留；PowerShell 中文編碼與 stderr 包裝問題使 run2 更適合作為正式證據。
- Python 3.14 觸發 Pydantic V1 相容性 UserWarning（完整保留、未抑制）；此輪仍完成指定 graph 路由並重現目標錯誤，不宣稱環境全面相容。
- 未讀官方 Fix PR #38355 或修復程式碼；未修補 LangChain、未改 source/tests/lockfile、未 Commit／Push。未覆寫既有報告或更新 Project Status。
