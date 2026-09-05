# Global Agent Operating Instructions

## Role Separation

- **Main Session (Planning Only)**:
  - Role: Architect, Planner, and Supervisor.
  - The main session does not perform direct implementation or write code/tests. It designs the plan, frames the requirements, evaluates trade-offs, and delegates work.
- **Subagents (Implementation & Work)**:
  - Role: Execution and Workers.
  - All file changes, coding, test execution, debugging, and mechanical tasks are carried out by subagents running on `gpt-5.6-luna:high`.

## Fallback Policy

- When GPT / OpenAI Codex models (Sol or Luna) are unavailable, hit rate limits, or exhaust usage quotas:
  - Fall back to `google/gemini-3.8-flash` with `high` thinking.
  - Subagents automatically fall back to `google/gemini-3.8-flash:high` to complete delegated work.
  - The main session switches to `gemini-3.8-flash:high` for continued planning.
