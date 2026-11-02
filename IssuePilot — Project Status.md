# IssuePilot — Project Status

## Project Goal

Build a reusable AI Agent Skill that analyzes Issues across GitHub repositories, uses relevant source code and evidence to identify likely root causes, suggests fixes, and evaluates analysis results.

Extend this analysis foundation into an AI Bug Fixing Agent within the existing four-week, 20-day schedule. Target workflow: GitHub Issue → source-code analysis and RCA → clarify user requirements → user approves the fix plan → modify code → execute tests → report results. Fixing capabilities remain planned until implemented and verified.

## Architecture

- `main.py` and `llm_client.py`: preserve Week 1 LLM API integration work with Gemini.
- `.agents/skills/issuepilot/SKILL.md`: main entry point for the Codex Agent Skill, invoked as `$issuepilot`.
- `.agents/skills/issuepilot/scripts/`: three fetchers retrieve Issue, PR, and commit metadata; `repo_inspector.py` reads regular UTF-8 files at explicit local commits. Skill tool integration is planned.
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

### Week 2 — Data Retrieval & Reliability (In Progress)

- Day 6: GitHub Issue Fetcher (Completed).
  Output: `github_fetcher.py` and tests. Done when Issue JSON retrieval and documented CLI error handling pass the recorded manual and automated checks.
- Day 7: PR / commit metadata retrieval (Completed).
  Output: PR/commit fetchers and tests. Done when metadata-only output, URL parsing, and CLI success/error scenarios pass mocked tests.
- Day 8: Repository Inspector for explicit source-code versions (Completed; bug reproduction is not verified).
  Output: read-only `repo_inspector.py` and tests. Done when file/commit validation, text retrieval, CLI errors, and repository-preservation checks pass.
- Day 9: Skill Integration + Source Retrieval + Version Selection. Output: integrated read-only workflow and recorded repository/commit selection. Done when the Skill retrieves Issue data and relevant source at an explicit SHA, records selection evidence and uncertainty, and excludes actual fix PR content from initial RCA.
- Day 10: RCA End-to-End Testing + Analysis MVP. Output: reproducible Issue-to-RCA run and report. Done when the integrated workflow produces a Traditional Chinese report with source paths, line numbers, SHA, hypotheses, and limitations, without modifying the target repository or reading the actual fix PR.

### Week 3 — Bug Fixing Workflow & Evaluation (Not Started)

- Day 11: Fix Planning + Requirement Gap Detection. Output: proposed fix scope, acceptance criteria, risks, and open questions. Done when unsupported assumptions and unclear requirements are explicitly identified before implementation.
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
- Days 1–8: Completed. Next: Day 9 — Skill Integration + Source Retrieval + Version Selection (Not Started). Analysis MVP targets Day 10; Bug Fixing MVP targets Day 14.
- Implemented: generic Issue, PR, and commit URL parsing, REST API retrieval, JSON output, missing/invalid URL handling, HTTP 404, rate-limit, and network-error handling.
- PR output: owner, repo, pr_number, title, state, merged, base_sha, head_sha. A PR base_sha is metadata, not a verified bug-reproduction version.
- Commit output: sha, message, parent SHA list, author metadata; accepts full 40-character SHAs and uses `/git/commits/{sha}` without retrieving file diffs.
- Repository Inspector: read-only Git argument arrays validate repository, full SHA-1/SHA-256 commit IDs, root-relative POSIX paths, regular-file modes, and UTF-8 text; no checkout/reset/fetch. The selected commit is not a verified bug version.
- Automated verification: all 52 tests passed (4 Day 6, 26 Day 7, 22 Day 8). Fetchers use mocks; Inspector uses an isolated Git fixture plus mocked execution failures, checking repository content remains unchanged after every test.
- Coverage gaps: Day 6 success/URL/404/429 automation; malformed API responses, authentication/retries, live API integration, bare/worktree/SHA-256 repositories, partial clones, and large files. An existing Day 6 mock HTTPError can emit a ResourceWarning.
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

Read this file and the current project files before continuing. Days 1–8 are Completed; Day 9 — Skill Integration + Source Retrieval + Version Selection is Not Started. Begin with read-only integration and explicit version selection; retain all existing deliverables, the 52-test record, and documented coverage gaps. Keep the initial RCA free of actual-fix PR content. Later fixing stages must clarify requirements, obtain explicit approval before target-repository edits, and preserve user changes. Follow the 20-day roadmap without treating planned features as completed. Check dependency compatibility before installing packages; change Python versions only for a concrete compatibility issue.
