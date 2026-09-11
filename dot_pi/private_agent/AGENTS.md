# Global Agent Operating Instructions

## Role Separation

- **Main Session (Planning Only)**:
  - Role: Architect, Planner, and Supervisor.
  - The main session does not perform direct implementation or write code/tests. It designs the plan, frames the requirements, evaluates trade-offs, and delegates work.
- **Subagents (Implementation & Work)**:
  - Role: Execution and Workers.
  - All file changes, coding, test execution, debugging, and mechanical tasks are carried out by worker subagents using `openai-codex/gpt-5.6-luna:high` until Luna reaches its usage limit; then use the configured `google/gemini-3.8-flash:high` fallback.

## Subagent Launch Policy

- Prefer async/background subagent execution.
- When a direct single-child async launch is unavailable or fails, wrap that one worker in an async workflow using `workflowScript` with one `runs.run` call, and launch the workflow with `async: true`; this preserves background execution even for one worker.
- Only fall back to foreground execution with fork context if both the direct async launch and the single-worker async workflow approach fail or are unavailable.

## Fallback Policy

- When GPT / OpenAI Codex models (Sol or Luna) are unavailable, hit rate limits, or exhaust usage quotas:
  - Fall back to `google/gemini-3.8-flash` with `high` thinking.
  - Subagents automatically fall back to `google/gemini-3.8-flash:high` to complete delegated work.
  - The main session switches to `gemini-3.8-flash:high` for continued planning.

## Git Worktree Policy

- **Dedicated Worktrees for Branches**:
  - All non-main / feature branches must reside in their own dedicated git worktree (typically under `.worktrees/<branch-name>`).
  - The primary repository directory must remain clean and checked out to the default branch (`main` or `master`).
  - Never switch branches or develop feature branches directly inside the primary repository checkout.
