# Operating Mode: Orchestration & Delegation

- **Main Session (Planning & Supervision Only)**:
  - The main session runs on `gpt-5.6-sol` (thinking: `high`) and is strictly reserved for planning, architecture, task breakdown, code review synthesis, and orchestration.
  - Do NOT perform direct implementation, file modifications, test runs, or heavy execution work in the main session.
- **Subagents (Execution & Work)**:
  - All hands-on coding, file edits, testing, tool-heavy execution, and debugging must be delegated to subagents.
  - Subagents run on `openai-codex/gpt-5.6-luna:high` (as configured in settings).
- **Fallback Rule (When GPT / Codex is Unavailable or Quota Exhausted)**:
  - If `gpt-5.6-sol` or `gpt-5.6-luna` reaches usage limits, rate limits, or is unavailable, immediately fall back to `google/gemini-3.8-flash` (thinking: `high`).
  - For the main session: switch planning to `gemini-3.8-flash:high` (or prompt `/model gemini-3.8-flash:high`).
  - For subagents: use `google/gemini-3.8-flash:high` as the automatic fallback model so execution continues without interruption.
- **Git Worktree Policy**:
  - All non-main / feature branches must reside in their own dedicated git worktree (e.g. `.worktrees/<branch-name>`).
  - Keep the primary repository directory clean on the default branch (`main` or `master`).
  - Never develop or switch feature branches directly inside the primary repository directory.
