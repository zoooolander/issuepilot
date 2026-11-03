# IssuePilot — Project Status

## Project Goal

Build a reusable AI Agent Skill that analyzes Issues across GitHub repositories, uses relevant source code and evidence to identify likely root causes, suggests fixes, and evaluates analysis results.

Extend this analysis foundation into an AI Bug Fixing Agent within the existing four-week, 20-day schedule. Target workflow: GitHub Issue → source-code analysis and RCA → clarify user requirements → user approves the fix plan → modify code → execute tests → report results. Fixing capabilities remain planned until implemented and verified.

## Architecture

- `main.py` and `llm_client.py`: preserve Week 1 LLM API integration work with Gemini.
- `.agents/skills/issuepilot/SKILL.md`: main entry point for the Codex Agent Skill, invoked as `$issuepilot`.
- `.agents/skills/issuepilot/scripts/`: three fetchers retrieve Issue, PR, and commit metadata; `version_selector.py` checks current HEAD and dirty state; `repo_inspector.py` reads/searches fixed-commit UTF-8 files with directory scope and bounded budgets. Skill tool integration is complete.
- `.agents/skills/issuepilot/references/report_template.md`: Traditional Chinese RCA report template.
- Codex: source-code analysis, RCA, and report generation; Python scripts provide supporting tools.
- Planned extension: requirement-gap detection, user clarification, an explicit approval gate, scoped code changes, test execution, and fix verification. Human approval is required before modifying the target repository.

## Environment

- OS / shell: Windows / PowerShell; editor: VS Code.
- Project path: `C:\D\projects\issuepilot`.
- Recorded Python version: 3.14.10; pip: 26.2.2.
- Virtual environment: `.venv`; interpreter: `C:\D\projects\issuepilot\.venv\Scripts\python.exe`.
- Agent runtime: Codex CLI; reusable project Skill: `$issuepilot`.
- Direct virtual-environment Python execution works; activation previously encountered a PowerShell execution-policy restriction.

## Development Roadmap

Keep all Day 1–8 deliverables. Increase daily scope where needed without adding development days. Each day lists its output and completion criteria; planned criteria are not evidence of completion.

### Week 1 — LLM Integration & Skill Prototype (Completed)

- Day 1: Python environment setup.
  Output: Python environment and starter program. Done when the virtual-environment interpreter runs the program successfully.
- Day 2: Gemini API integration.
  Output: `main.py` and `llm_client.py` integration prototype. Done when a prompt returns a Gemini response; preserve this work alongside the Skill.
- Day 3: Codex CLI and repository exploration.
  Output: working Codex CLI setup and repository exploration. Done when Codex can inspect project files and identify relevant source locations.
- Day 4: Create and test the reusable `$issuepilot` Skill.
  Output: reusable Skill prototype. Done when `$issuepilot` can invoke the documented analysis workflow.
- Day 5: Traditional Chinese RCA report with code evidence.
  Output: structured Traditional Chinese RCA report. Done when it follows the template, references code evidence, and distinguishes uncertainty.

### Week 2 — Data Retrieval & Reliability (Completed)

- Day 6: GitHub Issue Fetcher (Completed).
  Output: `github_fetcher.py` and tests. Done when Issue JSON retrieval and documented CLI error handling pass the recorded manual and automated checks.
- Day 7: PR / commit metadata retrieval (Completed).
  Output: PR/commit fetchers and tests. Done when metadata-only output, URL parsing, and CLI success/error scenarios pass mocked tests.
- Day 8: Repository Inspector for explicit source-code versions (Completed; bug reproduction is not verified).
  Output: read-only `repo_inspector.py` and tests. Done when file/commit validation, text retrieval, CLI errors, and repository-preservation checks pass.
- Day 9: Skill Integration + Source Retrieval + Version Selection (Completed). Output: integrated read-only workflow and recorded repository/commit selection. Done when the Skill retrieves Issue data and relevant source at an explicit SHA, records selection evidence and uncertainty, and excludes actual fix PR content from initial RCA.
- Day 10: RCA End-to-End Testing + Analysis MVP (Completed). Output: reproducible Issue-to-RCA run and report. Done when the integrated workflow produces a Traditional Chinese report with source paths, line numbers, SHA, hypotheses, and limitations, without modifying the target repository or reading the actual fix PR.

### Week 3 — Bug Fixing Workflow & Evaluation (Not Started)

- Day 11: Fix Planning + Domain Understanding + Requirement Gap Detection. Output: proposed fix scope, acceptance criteria, risks, and open questions. Done when unsupported assumptions and unclear requirements are explicitly identified before implementation.
  First independently research repository documentation, source code, tests, and Issue discussions to understand the domain and expected behavior. Ask the Engineer only about gaps that remain unsupported by evidence or require a business decision; do not delegate researchable questions to the Engineer.
- Day 12: User Clarification + Approval Gate. Output: clarification dialogue and explicit approval of a concrete fix plan. Done when ambiguous requirements trigger questions, absent/denied approval blocks target-repository changes, and a changed plan requires renewed approval.
  Implement human-in-the-loop with specific, contextual domain questions that explain the evidence, unresolved ambiguity, and impact on the fix. Update the plan using the Engineer's answers and obtain explicit authorization for that plan before modifying code.
- Day 13: Bug Fix Implementation + Safety Controls. Output: minimal patch within the approved scope. Done when user changes are identified and preserved, only approved target changes are made, and no commit, push, or PR creation occurs without separate explicit permission.
- Day 14: Test Execution + Fix Verification (Bug Fixing MVP). Output: test results and fix-verification report. Done when the approved reproduction/regression checks and relevant existing tests pass, or failures/blockers are reported accurately; the successful MVP requires demonstrated bug resolution and preserved user changes.
- Day 15: Fix PR Comparison + Evaluation. Output: evaluation criteria, actual-fix comparison, and limitations. Done when the saved initial RCA and implemented fix are assessed against the actual fix PR without rewriting the original analysis or claiming unsupported accuracy.

### Week 4 — Hardening, Packaging & Demo (Not Started)

- Day 16: Workflow Hardening + Error Recovery. Output: recovery paths for API/Git/tool failures, insufficient evidence, and interrupted workflows. Done when bounded retries and safe stopping preserve user changes and never bypass approval.
- Day 17: Automated Integration Testing. Output: repeatable workflow integration suite. Done when success, clarification, denied/missing approval, execution failure, and repository-preservation scenarios pass without relying on live API calls.
- Day 18: Cross-Repository Bug Fixing Validation. Output: recorded runs across at least two distinct repositories. Done when each run selects its version explicitly, obtains approval before edits, verifies the fix with tests, and records limitations without repository-specific dependencies.
  Validate against real open-source repositories. The product uses one IssuePilot session. A tester unfamiliar with a repository may optionally use a separate, independent session to study already-fixed code or the fix PR and help answer domain questions. This is a testing aid, not a product feature; keep fix content out of the IssuePilot session before its initial RCA, record assistance and answer provenance, and report assisted runs separately from independent blind evaluations.
- Day 19: Documentation + Packaging. Output: README, architecture/evaluation documentation, and installable Skill package. Done when setup, tool usage, approval boundaries, known limitations, and reproduction instructions are consistent and verified from a fresh installation.
- Day 20: Final Demo + Interview Preparation. Output: end-to-end demo and interview materials. Done when the demo shows Issue retrieval, RCA, clarification, approval, scoped changes, tests, and results, and the presentation explains evidence, evaluation, and limitations.

## Current Progress

- Week 1: Completed.
- Days 1–8: Completed; all existing deliverables retained. Days 9–10: Completed; Analysis MVP accepted. Next: Day 11 — Fix Planning + Domain Understanding + Requirement Gap Detection (Not Started). Bug Fixing MVP remains scheduled for Day 14.
- Implemented: generic Issue, PR, and commit URL parsing, REST API retrieval, JSON output, missing/invalid URL handling, HTTP 404, rate-limit, and network-error handling.
- PR output: owner, repo, pr_number, title, state, merged, base_sha, head_sha. A PR base_sha is metadata, not a verified bug-reproduction version.
- Commit output: sha, message, parent SHA list, author metadata; accepts full 40-character SHAs and uses `/git/commits/{sha}` without retrieving file diffs.
- Repository Inspector: read-only Git argument arrays validate repository, full SHA-1/SHA-256 commit IDs, root-relative POSIX paths, regular-file modes, and UTF-8 text; no checkout/reset/fetch. The selected commit is not a verified bug version.
- Automated verification: all 52 tests passed (4 Day 6, 26 Day 7, 22 Day 8). Fetchers use mocks; Inspector uses an isolated Git fixture plus mocked execution failures, checking repository content remains unchanged after every test.
- Day 9 Step 1 — Skill Integration: documented real tool CLI inputs/outputs, read-only analysis, disclosure limits, and authorized report destinations.
- Day 9 Step 2 — Source Retrieval: fixed-SHA listing, filename/text search, line evidence, sensitive-file exclusions, and bounded results; exact-path reads remain available.
- Day 9 Step 3 — Version Selection: default to the Engineer's current HEAD; report staged/unstaged/untracked changes and require confirmation before analyzing HEAD when dirty. HEAD is not a verified bug version.
- Day 9 Step 4 — Structured RCA Output: preserved seven Traditional Chinese sections with version/workspace provenance, expected/actual behavior, evidence, confidence, reproduction status, Technical Unknowns, and Domain Decisions.
- Day 9 integration acceptance: all four steps exercised in the real Issue-to-RCA workflow; initial analysis did not inspect the actual fix PR or modify target source code.
- Day 10 acceptance: real Issue RCA completed and saved at `reports/issue-38351-analysis.md`; the report retains its original analysis and adds a separate follow-up acceptance record. The case is validation evidence, not a hard-coded tool dependency.
- Day 10 retrieval fix: unrelated filenames no longer consume candidate-content budget; directory scope, separate metadata/content limits, completion state, stop reasons, and regression tests are implemented.
- Follow-up search acceptance (Engineer-reported): same LangChain SHA `5893459c4f2bfac6c8d3262cae1e3f2246d9287f`, scope `libs/langchain_v1/langchain/agents`; two `_make_model_to_tools_edge` matches in `factory.py`, `complete=true`, `scan_truncated=false`. This was tool revalidation, not a complete RCA rerun.
- Latest automated verification: Inspector 47/47 and full unittest 96/96 passed (4 Issue, 13 PR, 13 commit, 47 Inspector, 19 Version Selector), without warning suppression. The Day 6 mock HTTPError resource-cleanup issue was fixed.
- Limitation: the LangChain Bug has not been reproduced; RCA remains static analysis, with runtime reproduction marked unverified. The Issue itself disclosed diagnosis/fix suggestions, so this case is not an independent blind evaluation; no actual fix PR was inspected.
- Remaining coverage/operational limits: Day 6 success/URL/404/429 automation; malformed API responses, authentication/retries, generalized live API integration, linked-worktree/SHA-256 repositories, partial clones, and very large files. Metadata is captured for the selected scope before its processing cap; scoped search is not unrestricted whole-repository coverage. Bare working-tree selection is intentionally rejected.
- Test command: `.venv\Scripts\python.exe -m unittest discover -s tests -v`. Planned roadmap features remain unimplemented unless explicitly marked completed.

## Engineering Principles

- Develop incrementally and verify each step.
- Keep reports in Traditional Chinese while preserving code identifiers.
- Separate verified evidence from hypotheses; never invent evidence or evaluation results.
- Do not inspect the actual fix PR before completing the initial RCA.
- Keep API keys out of Git; never read or expose `.env` contents.
- Preserve both LLM API integration and Agent Skill development work.
- Keep IssuePilot generic; do not hard-code a specific repository, Issue, fix PR, or commit as a dependency.
- Human-in-the-loop: ask when requirements are unclear; obtain explicit user approval of the concrete fix plan before any target-repository modification. No response is not approval; pause dependent work until clarification/approval arrives.
- Preserve users' existing staged, unstaged, and untracked changes. Stop and clarify overlapping edits; never discard or overwrite user work. Require renewed approval for scope changes and separate explicit permission for commits, pushes, or PR creation.
- Keep initial RCA separate from actual-fix comparison: do not auto-discover or inspect the actual fix PR during initial analysis. Run tests within the approved scope and report commands, outcomes, unresolved failures, and uncertainty.

## How to Resume

Read this file, the current project files, and the saved RCA with its follow-up acceptance record before continuing. Days 1–10 are Completed; resume at Day 11 — Fix Planning + Domain Understanding + Requirement Gap Detection (Not Started). Research domain behavior through documents, source, tests, and Issue discussion before raising Engineer decisions. Preserve all prior deliverables, the historical 52-test record, and the latest Inspector 47/47 and full-suite 96/96 results. LangChain Bug reproduction remains unverified; do not turn static analysis or tool acceptance into runtime/fix claims. Keep initial RCA independent of the actual fix PR. Later target-repository edits require an explicitly authorized concrete plan and protection of user changes. Follow the unchanged four-week, 20-day schedule. Check dependency compatibility before installing packages; change Python versions only for a concrete compatibility issue.
