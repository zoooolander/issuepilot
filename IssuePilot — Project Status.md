# IssuePilot — Project Status

## Project Goal

Build a reusable AI Agent Skill that analyzes Issues across GitHub repositories, uses relevant source code and evidence to identify likely root causes, suggests fixes, and evaluates analysis results.

## Architecture

- `main.py` and `llm_client.py`: preserve Week 1 LLM API integration work with Gemini.
- `.agents/skills/issuepilot/SKILL.md`: main entry point for the Codex Agent Skill, invoked as `$issuepilot`.
- `.agents/skills/issuepilot/scripts/`: GitHub API retrieval and repository version checks; currently contains `github_fetcher.py`. PR/commit retrieval and repository inspection are planned.
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
- Day 7: PR / commit metadata retrieval.
- Day 8: Repository Inspector for pre-fix source code.
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
- Week 2 Day 6: Completed. Next: Day 7 — PR / commit metadata retrieval (Not Started).
- Implemented: Issue URL parsing, REST API retrieval, JSON output, missing/invalid URL handling, HTTP 404, rate-limit, and network-error handling.
- Manual verification reported by the user: invalid URL, HTTP 404, and a valid Issue behaved as expected.
- Automated verification: all 4 tests in `tests/test_github_fetcher.py` passed; mocked HTTP 403 rate limits and `URLError` cover exception propagation, CLI stderr, empty stdout, and exit code 1 without network access.
- Automated coverage gaps: success/JSON output, missing/invalid URLs, HTTP 404/429, other HTTP errors, and malformed responses. These are follow-up coverage improvements, not completed tests.
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

Read this file and the current project files before continuing. Resume from Day 7 — PR / commit metadata retrieval. Day 6 is complete within its current scope; retain the documented test coverage gaps for follow-up. Follow the roadmap without treating planned features as completed. Check dependency compatibility before installing packages; change Python versions only for a concrete compatibility issue.
