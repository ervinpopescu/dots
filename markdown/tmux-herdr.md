# tmux to Herdr pilot

This importer appends a **new** Herdr workspace from one selected tmux session. It never sends tmux input, renames panes, sources config, detaches, kills, or restarts tmux. Keep Alacritty as the outer terminal; do not run Herdr nested inside tmux. The tmux server remains the rollback/authoritative runtime.

## Use

```sh
# Read-only query of one named session; writes only the requested mode-0600 artifact.
tmux-herdr --snapshot dots --output /tmp/dots-tmux.json
# Optional Linux-only targeted lookup for exact Pi session metadata:
tmux-herdr --snapshot dots --resolve-pi-sessions --output /tmp/dots-pi-resolved.json
# Default-safe planning: no Herdr connection and no state changes.
tmux-herdr --dry-run /tmp/dots-tmux.json
# Explicit opt-in, to an already-running named Herdr server only:
tmux-herdr --apply /tmp/dots-tmux.json --session pilot
```

The script may be run from this checkout as `./bin/executable_tmux-herdr`. Apply requires an available target server; it does not start one. It strictly parses `workspace list`, validates every returned workspace, and never alters existing workspaces. Unrelated and previously imported workspaces may remain while a new source is appended. The desired workspace label is `tmux:<exact-source-session-name>`; an existing label without its matching completed marker, duplicate labels, partial markers, or changed identities all fail closed. Each source reserves a private marker under `~/.local/state/tmux-herdr/`, atomically created at `<target>-<sha256(exact-source-name)>.json`; the source name is hashed rather than used as a path component. The marker binds the complete snapshot and `--allow-pi-continue` policy. Same-source concurrent applies are refused before creation, while different sources in one target use distinct markers. An identical completed repeat performs no Herdr mutation. The old target-wide `pilot.json` marker is recognized only for the already-applied `dots` import when its identity and exactly one `tmux:dots` label match; it is never migrated or deleted. If creation fails partway, inspect Herdr and remove any partial objects manually before retrying. No automatic cleanup is attempted.

## Fidelity and safety

The snapshot retains session/window/pane names and indices, attached and active flags, cwd, title, foreground command name, and cell geometry. By default no process environment is inspected. The explicit `--resolve-pi-sessions` snapshot option uses Linux `/proc` process-tree, foreground process-group, and TTY metadata to look only for a single matching foreground Pi process. It first checks that process's private beacon for the exact tmux pane and process-start identity, then falls back to the bounded approved `PI_SESSION_FILE`/`PI_SESSION_ID` environment lookup. It never returns other variables or reads Pi JSONL contents. A validated, owned regular session file under `~/.pi/agent/sessions/` is preferred; otherwise an ID is accepted only if it matches Pi's documented grammar: letters/digits with an alphanumeric first and last character, and only letters, digits, `.`, `_`, or `-` in between. Ambiguity, invalid paths/IDs, vanished/inaccessible processes, rejected beacons, or unsupported platforms leave the reference unset or use only the approved environment fallback, and add non-sensitive reason codes. Pane PID/TTY, pane ID, beacon contents, and raw process environment are not saved; only a validated `{kind,value}` session reference and status are persisted. The flag is snapshot-only; without it no automatic lookup occurs. All snapshots exclude other environment variables, command arguments, pane contents/scrollback, and Pi JSONL contents. Tmux's layout token is diagnostic only. Workspaces correspond to the selected tmux session and tabs to windows; the first tab and pane are explicitly renamed, other tabs use captured names, and panes use captured terminal title (falling back to command/index). Pane splits use `right`/`down` with an approximate ratio derived from cell extents; this is not a recursive reconstruction of arbitrary layouts. Active tab/pane focus is requested where the Herdr CLI supports it. Herdr cannot adopt live PTYs, process memory, shell jobs/history, scrollback, terminal modes, dev servers, or unsaved Pi requests. Cell geometry and exact layout are not portable.

Only a `pi` command with an explicit exact session reference in a snapshot is resumed. The importer uses its positional-only internal launcher so Pi's `--session` flag cannot be consumed as a Herdr global option, and revalidates the reference immediately before executing Pi. Normal tmux collection cannot infer it, so the default plan uses a shell and warns `pi_session_unknown`; opt-in `--allow-pi-continue` is a non-exact alternative that resumes the newest project session. The flag is passed through apply and included in local idempotency identity. `lazygit` restarts in the captured cwd. Shell panes start a fresh configured shell. Unknown/side-effectful commands (including npm and viewers) are never replayed and fall back to a plain shell with a warning. An unavailable cwd blocks apply rather than silently choosing another directory.

### Deploying the Pi beacon and resolving the current session

The global Pi extension is deployed at `~/.pi/agent/extensions/tmux-herdr-beacon.ts` by chezmoi. After updating this checkout, deploy it explicitly with `chezmoi apply ~/.pi/agent/extensions/tmux-herdr-beacon.ts` (or your approved wrapper) and review the proposed changes first. An already-running Pi process does not gain a newly deployed extension merely because its files changed: run Pi's `/reload`, then explicitly run `/herdr-beacon` in each tmux Pi pane to publish the current session reference. Do not assume `/reload` itself republishes the beacon. The extension also refreshes on documented session-start/tree lifecycle events.

Then collect a new snapshot, because older snapshots do not contain resolved references:

```sh
tmux-herdr --snapshot dots --resolve-pi-sessions --output /tmp/dots-pi-resolved.json
tmux-herdr --dry-run /tmp/dots-pi-resolved.json
```

Beacons contain only schema, Pi PID, tmux pane ID, Linux process-start token, and validated current session reference. They live in a private 0700 directory (`$XDG_RUNTIME_DIR/pi-herdr-sessions` only when `XDG_RUNTIME_DIR` is absolute; otherwise `$HOME/.cache/pi-herdr-sessions` only when `HOME` is absolute), with 0600 files. Both publisher and importer fail closed if neither absolute location is available. On Linux, directory components are opened without following symlinks and all beacon child reads/writes/renames are relative to a validated pinned directory handle; operations fail closed when those primitives are unavailable. The importer does not expose beacon contents or references in warnings; snapshots persist only validated session refs and non-sensitive resolution status. Remove the extension to roll back beacon publishing. Beacon files are intentionally not removed during Pi shutdown: stale files remain harmless because importer validation requires the live PID, matching process-start token and pane, owner, type, permissions, schema, and session reference. Existing Pi sessions and tmux remain untouched. Use apply only after reviewing the new dry-run and the separate opt-in safeguards above.

The shipped `dot_config/herdr/config.toml.tmpl` provides only basic shell, cwd and Herdr agent-restore preferences. It does not start Herdr or configure automatic migration.

## Fixture checks

`python3 -m unittest discover -s tests -p 'test_tmux_herdr.py'` tests planning, append/ownership/idempotency behavior, application classification, and mocked Pi process metadata without tmux or Herdr control. `node --experimental-strip-types --test tests/tmux-herdr-beacon.test.mjs` exercises the actual extension registration, publication, atomic replacement, pinned-directory semantics, and notifications without loading Pi. To validate local CLI/config syntax, use `herdr --help` and `herdr config check`; do not use migration `--apply` on a live server during validation.
