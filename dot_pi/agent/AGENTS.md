# Global Agent Operating Instructions

## Role Separation

- **Main Session (Planning Only)**:
  - Role: Architect, Planner, and Supervisor.
  - The main session does not perform direct implementation or write code/tests. It designs the plan, frames the requirements, evaluates trade-offs, and delegates work.
- **Subagents (Implementation & Work)**:
  - Role: Execution and Workers.
  - All file changes, coding, test execution, debugging, and mechanical tasks are carried out by subagents running on `gpt-5.6-luna:high`.
