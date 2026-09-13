# Global Agent Instructions

## Runtime

- Use Pi as the primary agent runtime. Pi may use Codex or Gemini; keep
  guidance provider-neutral and mention provider-specific behavior only when
  essential.

## Engineering

- Never use em dash characters; use plain hyphens.
- Never add an agent as a commit co-author.
- Never manually edit generated files, including `CHANGELOG.md`.
- Prefer quality, simplicity, robustness, scalability, and maintainability over
  development cost.
- For bug fixes, first reproduce the problem in an end-user-aligned E2E
  setting.
- During product E2E tests, inspect the UI carefully and fix obvious pixel or
  UI defects, even when unrelated. Apply the same high standard to lint
  failures, test failures, and flakiness.

## Workflow

- Use project-local `tmp/` for intermediate and comparison artifacts, not
  `/tmp`.
- Record concise notes about deferred, non-blocking bugs or oddities in
  `SESSION.md`; do not record accomplishments there.
- Use semantic commits, explain non-obvious trade-offs in the body, and wrap
  commit prose at 72 columns.

## Git workflow

- Keep every non-main or feature branch in its own dedicated git worktree,
  typically under `.worktrees/<branch-name>`.
- Keep the primary repository checkout clean and on `main` or `master`.
- Never switch branches or develop feature branches directly in the primary
  checkout.
