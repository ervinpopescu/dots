# Operating Mode: Orchestration & Delegation

- **Main Session (Planning & Supervision Only)**:
  - The main session runs on `gpt-5.6-sol` (thinking: `high`) and is strictly reserved for planning, architecture, task breakdown, code review synthesis, and orchestration.
  - Do NOT perform direct implementation, file modifications, test runs, or heavy execution work in the main session.
- **Subagents (Execution & Work)**:
  - All hands-on coding, file edits, testing, tool-heavy execution, and debugging must be delegated to subagents.
  - Subagents run on `openai-codex/gpt-5.6-luna:high` (as configured in settings).
