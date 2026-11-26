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

- At session start (and when working on any repository or `.worktrees/<branch>`
  checkout), check whether `SESSION.md` exists at the primary repository
  checkout root; if it exists, read it before starting work for local session
  context, personal workflow overrides, and deferred notes.
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
- Never run `no-mistakes` on `main`/`master`, never pass `--no-verify` (use
  `SKIP=...`), and keep `@google.com` emails/names out of public OSS commits
  (`ervinpopescu`).
- **Release-scope merge gate:** Only merge PRs/branches that belong to the
  **active/current release milestone** onto `main`/`master`. Hold future-release
  or backlog PRs open on their feature branches even when CI is green and the
  user has already pre-approved / given `LGTM`, unless the user explicitly asks
  to pull that specific PR into the current release.

## Cloudtop, Auth & Harness Traps

- Refresh `tmux` SSH agent + `gcert` before `ssh`/`scp`/`rcmd000-gce` calls:
  `unset SSH_AUTH_SOCK && eval "$(tmux show-environment -s)" && gcertstatus -quiet || /usr/bin/gcert`.
  Never run `gcert -lifetime=168h` (destination restriction breaks Moma, Code
  Search, OneSupport, and Stubby). On `tmux` `KeyRevoked`, use `keyctl session`
  or `XCURL_NO_KEYRING=1`.
- On `RPC_RESTRICTIONS_VIOLATION` from built-in `moma_search`, `code_search`,
  `skill_search`, or `search_marketplace`, switch immediately to `moma` MCP
  (`internal_search`), `yaqs` MCP (`yaqs_search`), or `duckie` `ask_duckie`
  (argument `question`, not `query`). Use `rg` / `git grep` in local git
  checkouts (`cs --corpus=local` works only inside CitC `/google/src/cloud/...`;
  use `cs --corpus=google3` for Google3 lookups).
- Keep shell syntax simple (`agcis_rule_denied: ast_parse_failure`) and use
  `python3 - <<'PY'` heredocs instead of `python3 -c "..."` with escaped
  quotes; never run inline Python TCP sockets (`bind()`/`connect()`),
  `curl -k`/`--insecure`, or `gcloud deploy rollouts approve` (hard security
  stop hook). Skip `~/memory/` writes on `permission denied` / transport
  errors.
- Tool & file traps: pass absolute paths and `StartLine <= EndLine` to
  `read_file`/`edit_file`; never call `read_file` on >100 MB logs (such as
  `transcript_full.jsonl` in long sessions) - stream via Python instead.
- Orchestration tools: check `swarm status` is `waiting` before `swarm model`;
  never call `subagent` in bash; keep at most one active `schedule`
  `TimerCondition="any"` (current-session task IDs only); check `manage_task`
  `list` before `kill` (never `kill` already-`DONE` tasks); transcode
  `video/webm` before `read_file`.
- Prefix `nvm` Node 24 (`npm >= 12.0.0`) / `~/.local/bin` / `~/.no-mistakes/bin`
  in non-interactive shells (use `/usr/bin/go` if `/usr/local/go/bin/go` is
  absent); set `CGO_ENABLED=1` for `go test -race`; `unset GIT_DIR
  GIT_WORK_TREE` across worktrees; never set `TMPDIR` inside a git worktree.
- `gcloud`, `gws` & OneSupport: never run `gcloud projects list`; pass Project
  **ID** (not number) to `gcloud builds describe --project`; use
  `--impersonate-service-account` for `print-identity-token --audiences`; set
  `CLOUDSDK_CONTEXT_AWARE_USE_CLIENT_CERTIFICATE=false` for `gcloud app`; pass
  file paths or Python `stdin` instead of shell pipes to `secrets versions add
  --data-file=-` and `api-keys create`. On `gws` `"insufficient scopes"` after
  re-consent, run `gws auth logout && gws auth login`. OneSupport requires
  unrestricted `gcert` on Cloudtop (Google Admin UI -> `consult-handler gcp
  import` is the `gcert`-free fallback).
- Browser & shell safety: never kill `tmux`; **never** run `chrome-devtools-axi
  stop` on the `consult-handler` session or automate `:20` (use
  `CHROME_DEVTOOLS_AXI_SESSION=<name>` + `AUTO_CONNECT=1` / `Xvfb :100+`, no
  `flock`); never run recursive `find /` or `grep -r ~` / `/tmp` / `/google/`.

## Responses & Docs

- Always respond concisely in English; ask before acting on unfamiliar terms
  or suspected STT typos; whenever presenting decisions, proposed next actions,
  or multi-item confirmations to the user, **always surface them via the native
  interactive question UI tool** (`ask_question` in Jetski, or
  `ask_user_question` / harness equivalent) instead of plain-text-only bullet
  lists (reserve plain text strictly for status updates with no pending choice,
  or fall back only when the runtime has no question tool). Restate full
  context if an earlier decision went unanswered.
- Surface availability/auth failure modes explicitly before removing fallback or
  break-glass paths; provide full clickable URLs; escape `<details>` tags.
- Use Graphviz `.dot` -> `.svg`/`.png` instead of Mermaid; never generate
  AI-slop Google Docs (blank lines between paragraphs, `**Label:**` line
  prefixes, multi-page exec summaries).
