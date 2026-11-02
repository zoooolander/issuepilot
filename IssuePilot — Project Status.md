# IssuePilot — Project Status

## Project Goal

Build a reusable AI Agent Skill that analyzes Issues across GitHub repositories, uses relevant source code and evidence to identify likely root causes, suggests fixes, and evaluates analysis results.

## Architecture

- `main.py` and `llm_client.py`: preserve Week 1 LLM API integration work with Gemini.
- `.agents/skills/issuepilot/SKILL.md`: main entry point for the Codex Agent Skill, invoked as `$issuepilot`.
- `.agents/skills/issuepilot/scripts/`: `github_fetcher.py`, `pr_fetcher.py`, and `commit_fetcher.py` retrieve Issue, PR, and commit metadata. repo_inspector.py reads regular UTF-8 files at explicit local commits. Skill tool integration is planned.
- `.agents/skills/issuepilot/references/report_template.md`: Traditional Chinese RCA report template.
- Codex: source-code analysis, RCA, and report generation; Python scripts provide supporting tools.

## Environment

- OS / shell: Windows / PowerShell; editor: VS Code.
- Project path: `C:\D\projects\issuepilot`.
- Recorded Python version: 3.14.10; pip: 26.2.2.
- Virtual environment: `.venv`; interpreter: `C:\D\projects\issuepilot\.venv\Scripts\python.exe`.
- Agent runtime: Codex CLI; reusable project Skill: `$issuepilot`.
- Direct virtual-environment Python execution works; activation previously encountered a PowerShell execution-policy restriction.

## Development Roadmap

### Week 1 — LLM Integration & Skill Prototype (Completed)

- Day 1: Python environment setup.
- Day 2: Gemini API integration.
- Day 3: Codex CLI and repository exploration.
- Day 4: Create and test the reusable `$issuepilot` Skill.
- Day 5: Traditional Chinese RCA report with code evidence.

### Week 2 — Data Retrieval & Reliability (In Progress)

- Day 6: GitHub Issue Fetcher (Completed).
- Day 7: PR / commit metadata retrieval (Completed).
- Day 8: Repository Inspector for explicit source-code versions (Completed; bug reproduction is not verified).
- Day 9: Integrate Python tools into the Skill workflow.
- Day 10: End-to-end integration test.

### Week 3 — Agent Workflow & Evaluation (Not Started)

- Day 11: Improve workflow and source-code retrieval.
- Day 12: Error recovery, branching, retries, and insufficient evidence.
- Day 13: Compare RCA against the actual fix PR.
- Day 14: Define evaluation criteria and test cases.
- Day 15: Failure analysis and limitations.

### Week 4 — Packaging & Demo (Not Started)

- Day 16: Refine Skill packaging and installation.
- Day 17: Automated tests and error scenarios.
- Day 18: Cross-repository validation.
- Day 19: README, architecture, and evaluation documentation.
- Day 20: Demo and interview presentation.

## Current Progress

- Week 1: Completed.
- Week 2 Days 6–8: Completed. Next: Day 9 — Skill Integration (Not Started).
- Implemented: generic Issue, PR, and commit URL parsing, REST API retrieval, JSON output, missing/invalid URL handling, HTTP 404, rate-limit, and network-error handling.
- PR output: owner, repo, pr_number, title, state, merged, base_sha, head_sha. A PR base_sha is metadata, not a verified bug-reproduction version.
- Commit output: sha, message, parent SHA list, author metadata; accepts full 40-character SHAs and uses `/git/commits/{sha}` without retrieving file diffs.
- Repository Inspector: read-only Git argument arrays validate repository, full SHA-1/SHA-256 commit IDs, root-relative POSIX paths, regular-file modes, and UTF-8 text; no checkout/reset/fetch. The selected commit is not a verified bug version.
- Automated verification: all 52 tests passed (4 Day 6, 26 Day 7, 22 Day 8). Fetchers use mocks; Inspector uses an isolated Git fixture plus mocked execution failures, checking repository content remains unchanged after every test.
- Coverage gaps: Day 6 success/URL/404/429 automation; malformed API responses, authentication/retries, live API integration, bare/worktree/SHA-256 repositories, partial clones, and large files. An existing Day 6 mock HTTPError can emit a ResourceWarning; those tests remain unchanged.
- Test command: `.venv\Scripts\python.exe -m unittest discover -s tests -v`. Planned roadmap features remain unimplemented unless explicitly marked completed.

## Engineering Principles

- Develop incrementally and verify each step.
- Keep reports in Traditional Chinese while preserving code identifiers.
- Separate verified evidence from hypotheses; never invent evidence or evaluation results.
- Do not inspect the actual fix PR before completing the initial RCA.
- Keep API keys out of Git; never read or expose `.env` contents.
- Preserve both LLM API integration and Agent Skill development work.
- Keep IssuePilot generic; do not hard-code a specific repository, Issue, fix PR, or commit as a dependency.

## How to Resume

Read this file and the current project files before continuing. Resume from Day 9 — Skill Integration. Days 6–8 are complete within their current scope; retain the documented coverage gaps for follow-up. Tool integration remains scheduled for Day 9. Follow the roadmap without treating planned features as completed. Check dependency compatibility before installing packages; change Python versions only for a concrete compatibility issue.
