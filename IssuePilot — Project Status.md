# IssuePilot — Project Status

## 1. Project Goal

Build an AI-powered issue analysis assistant that accepts a real GitHub Issue, retrieves relevant pre-fix source code, analyzes the likely root cause with code evidence, and compares its diagnosis against the actual fix PR.

Final goal: package the working analysis workflow as an AI Agent Skill or CLI command so a user can trigger the workflow with one command.

## 2. Target Users and Career Goal

- Target roles: AI Application Engineer / AI Agent Engineer.
- Purpose: demonstrate practical LLM integration, code retrieval, tool use, workflow orchestration, and evaluation.
- Prior background: 2+ years of backend development, mainly Java and Spring Boot.
- Project language: Python.

## 3. Selected Case Study

- Repository: `langchain-ai/langchain`
- Issue: https://github.com/langchain-ai/langchain/issues/38351
- Related PR: https://github.com/langchain-ai/langchain/pull/38355
- Important: verify issue details, repository versions, and the actual fix before implementation.

## 4. Development Roadmap

### Week 1 — LLM and Basic Analysis
- Day 1: Set up Python, virtual environment, and VS Code.
- Day 2: Make a successful LLM API call.
- Day 3: Retrieve the GitHub Issue and pre-fix source code.
- Day 4: Generate a root-cause analysis.
- Day 5: Include code evidence and uncertainty in the output.

### Week 2 — Code Retrieval and Reliability
- Day 6: Implement basic source-code search.
- Day 7: Improve retrieval relevance.
- Day 8: Define structured analysis output.
- Day 9: Handle failures and insufficient evidence.
- Day 10: Complete an end-to-end analysis.

### Week 3 — Workflow, Agent, and Evaluation
- Day 11: Structure the analysis workflow.
- Day 12: Add controlled tool use, branching, and retries where useful.
- Day 13: Compare the diagnosis with the actual fix PR.
- Day 14: Define evaluation criteria.
- Day 15: Review failures and limitations.

### Week 4 — Skill and Demo
- Day 16: Choose a compatible Agent CLI and Skill format.
- Day 17: Package the workflow as a Skill.
- Day 18: Run the workflow through one command.
- Day 19: Prepare README, architecture, tests, and evaluation results.
- Day 20: Complete the demo and interview presentation.

The schedule is flexible. Prioritize a working, evaluated core over completing every optional feature.

## 5. Current Environment

- OS: Windows
- Project directory: `C:\D\projects\issuepilot`
- Python: 3.14.10
- pip: 26.2.2
- Virtual environment: `C:\D\projects\issuepilot\.venv`
- Editor: VS Code
- Python extension: installed
- `main.py`: created and successfully executed
- Verified interpreter: `C:\D\projects\issuepilot\.venv\Scripts\python.exe`
- PowerShell activation initially encountered an execution-policy restriction; direct virtual-environment Python execution works.

Note: check package compatibility before installing dependencies. Do not change Python versions unless a concrete compatibility issue requires it.

## 6. Current Progress

- [x] Day 1: Environment setup and `hello world` test.
- [ ] Day 2: LLM API call.
- [ ] Day 3: Retrieve Issue and source code.
- [ ] Day 4: Root-cause analysis.
- [ ] Day 5: Evidence-backed output.

Current stopping point: Day 1 is complete. Day 2 has not started. The next task is to choose an LLM API provider and make the first API call.

## 7. Engineering Principles

- Build incrementally; do not implement the entire system at once.
- Prefer concrete code and verifiable results.
- Keep API keys out of source code and Git.
- Avoid unnecessary frameworks until they solve a real problem.
- Do not invent evaluation metrics or claim unverified accuracy.
- Treat the Skill as the entry point; Python scripts and APIs can provide the underlying capabilities.
- Verify real repository and PR content before drawing conclusions.

## 8. How to Resume

At the beginning of a new chat, provide this file and ask the assistant to continue IssuePilot from the current progress. Update this document when the roadmap, architecture, environment, or current milestone changes.