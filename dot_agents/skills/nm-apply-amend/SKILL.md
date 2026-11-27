---
name: nm-apply-amend
description: Inspects diffs against the no-mistakes remote tracking branch, applies useful pipeline changes locally via git nm-apply, strips all screenshots and screenshot-capturing code (in tests and across the codebase), and amends each remaining change into the originating commit on the current feature branch using git commit --fixup and autosquash rebase. Use when syncing no-mistakes pipeline fixes or remote review changes into existing branch history.
user-invocable: true
---

# no-mistakes Apply & Amend (`nm-apply-amend`)

Reviews changes produced by the `no-mistakes` validation pipeline on the remote `no-mistakes/<branch>` tracking ref, applies them locally via `git nm-apply`, strips all screenshot artifacts and code that captures screenshots (in tests and anywhere else in the codebase), and folds each remaining change into the earlier commit on the active feature branch that originally touched those files.

---

## Core Principles

1. **Same-Branch Scope Only:** Only commits on the active feature branch (`$BASE..HEAD`) are candidates for amending. Never modify upstream `main`/`master` commits.
2. **No Screenshots or Screenshot-Taking Code:** Always remove any screenshot files (`.png`, `.jpg`, `.jpeg`, `.webp`, etc.) and any code that takes screenshots (`page.screenshot(...)`, `<locator>.screenshot(...)`, screenshot helpers like `_screenshot` / `_save_screenshot` / `_shoot`, `SCREENSHOT_DIR`, screenshot-only `evidence_dir` fixtures/arguments, and docstrings/comments describing screenshot capture) across both test files and non-test code before amending commits.
3. **File & Hunk Attribution:** Map each remaining file modified by `git nm-apply` back to the specific branch commit that introduced or modified that file.
4. **Atomic History Over Fixup Noise:** Fold linter, review, test, and docs fixes directly into their originating commits rather than leaving trailing fixup commits at `HEAD`.
5. **Safety & Verification:** Always create a backup branch ref before rewriting history, and verify tree equivalence (minus stripped screenshot artifacts/code) after rebasing.

---

## Execution Workflow

Copy this checklist and track progress:

```text
nm-apply-amend Progress:
- [ ] Step 1: Fetch no-mistakes remote and inspect incoming diff
- [ ] Step 2: Verify clean working tree, create backup ref, and run git nm-apply
- [ ] Step 3: Strip all screenshots and screenshot-taking code across tests and non-test files
- [ ] Step 4: Attribute modified files/hunks to originating branch commits with --fixup
- [ ] Step 5: Run non-interactive autosquash rebase onto merge-base and verify clean state
- [ ] Step 6: Push amended branch (and optionally anchor/retrigger no-mistakes if requested)
```

### Step 1: Fetch and Inspect the Remote Diff

#### 1. Verify Feature Branch and Fetch Remote

```bash
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "Error: Must be on a feature branch, not $BRANCH."
  exit 1
fi

git fetch no-mistakes "$BRANCH" 2>/dev/null || git fetch no-mistakes
```

#### 2. Inspect Incoming Changes

```bash
git diff --stat "$BRANCH" "no-mistakes/$BRANCH"
git diff "$BRANCH" "no-mistakes/$BRANCH"
```

If the diff is empty or the remote changes are not desirable, report to the user and stop.

---

### Step 2: Create Safety Backup & Apply Changes Locally

#### 1. Verify Clean Working Tree

```bash
if [ -n "$(git status --porcelain)" ]; then
  echo "Error: Working directory is not clean. Commit or stash existing changes."
  exit 1
fi
```

#### 2. Create Backup Ref & Apply Remote Diff

```bash
BACKUP_REF="backup/${BRANCH}-pre-nm-apply-$(date +%s)"
git branch "$BACKUP_REF" HEAD
echo "Created backup ref: $BACKUP_REF"

git nm-apply
git status --short
```

_(Note: `git nm-apply` runs `GIT_PAGER= git diff --binary $(git branch --show-current) no-mistakes/$(git branch --show-current) | git apply`. `--binary` matters: without it, a binary file on `no-mistakes/<branch>` (such as a screenshot that Step 3 deletes) makes `git apply` reject the whole patch. If your alias lacks `--binary`, run that pipeline directly or update the alias. `git apply` writes files that `no-mistakes` created as untracked files; Step 4 attributes them too.)_

---

### Step 3: Strip All Screenshots and Screenshot-Taking Code

The `no-mistakes` `test` step frequently adds screenshot files or screenshot-capturing code in tests and elsewhere in the repository. Before staging or attributing any changes, strip all screenshots and screenshot-taking code across the entire branch (`$BASE..HEAD` and the unstaged `git nm-apply` working tree):

#### 1. Delete Any Screenshot Files

Remove any untracked, staged, or branch-committed screenshot image files (`.png`, `.jpg`, `.jpeg`, `.webp`, or files under `screenshots/`, `tmp/screenshots/`, `evidence/`):

```bash
BASE=$(git merge-base origin/main HEAD 2>/dev/null || git merge-base main HEAD)

# Check for any image/screenshot files added in $BASE..HEAD or working tree
git status --porcelain | grep -iE '\.(png|jpg|jpeg|webp|gif|bmp)$|screenshot' || true
git diff --name-only "$BASE" | grep -iE '\.(png|jpg|jpeg|webp|gif|bmp)$|screenshot' || true
```

Delete any such files from the working tree with `rm -f -- <file>` (do not run `git rm`, so tracked deletions stay unstaged until Step 4 attributes each file).

#### 2. Remove Screenshot-Taking Code (Tests and Non-Test Code)

Scan all files modified in `$BASE..HEAD` and in the working tree for screenshot-capturing logic:

```bash
git diff "$BASE" | grep -n -iE 'screenshot|evidence_dir|_shoot|shot\(' || true
```

In every affected file (E2E tests, staging tests, unit tests, scripts, helpers, or docs):

- Remove all calls to `page.screenshot(...)`, `<locator>.screenshot(...)`, `take_screenshot(...)`, and custom screenshot wrappers (`_screenshot`, `_save_screenshot`, `_shoot`, `_screenshot_themes`, `shot`, `_screenshot_dir`, `SCREENSHOT_DIR`).
- Remove `evidence_dir` fixtures, parameters, and `os.makedirs(evidence_dir, ...)` blocks when used to write screenshots.
- Remove comments and docstrings that describe saving screenshots to `tmp/` or `EVIDENCE_DIR`.
- Keep all real functional assertions (`expect(...)`, `assert ...`) intact.

---

### Step 4: Attribute and Stage Fixups to Branch Commits

Find the branch merge-base and unstage the index so every modification and deletion is attributed per file:

```bash
BASE=$(git merge-base origin/main HEAD 2>/dev/null || git merge-base main HEAD)
git reset
```

For each changed file, inspect commits on `$BASE..HEAD` that touched it. Changed files are the modified or deleted tracked files (`git diff --name-only`) plus the new files that `git apply` left untracked (`git ls-files --others --exclude-standard`); new files have no history on the branch, so they always fall under Case C:

```bash
git log "$BASE..HEAD" --format="%h %s" -- "$FILE"
```

#### Case A - Single commit touched the file

Stage the file and create a targeted fixup commit:

```bash
git add -- "$FILE"
TARGET_HASH=$(git log "$BASE..HEAD" --format="%H" -- "$FILE" | head -n 1)
git commit --no-verify --fixup="$TARGET_HASH"
```

#### Case B - Multiple commits on the branch touched the file

Inspect `git log -p "$BASE..HEAD" -- "$FILE"`. Use `git add -p "$FILE"` if hunks belong to different commits, or target the latest commit that modified the relevant logic.

#### Case C - File was not touched by any commit on `$BASE..HEAD`

Stage the file and either `--fixup` the primary feature commit on the branch or create an atomic Conventional Commit (`test(...)` or `docs(...)`).

#### Automated Single/Latest Attribution Snippet

```bash
BASE=$(git merge-base origin/main HEAD 2>/dev/null || git merge-base main HEAD)
git reset

# Modified or deleted tracked files plus new untracked files, one path per
# line (paths may contain spaces, so never word-split them).
mapfile -t FILES < <({ git diff --name-only; git ls-files --others --exclude-standard; } | sort -u)

for file in "${FILES[@]}"; do
  mapfile -t COMMITS < <(git log "$BASE..HEAD" --format="%H" -- "$file")
  if [ "${#COMMITS[@]}" -ge 1 ]; then
    TARGET="${COMMITS[0]}"
    echo "Attributing $file -> $TARGET"
    git add -- "$file"
    git commit --no-verify --fixup="$TARGET"
  else
    echo "Manual attribution needed for $file (new, or not modified in $BASE..HEAD; see Case C)"
  fi
done

# Nothing may be left behind before the rebase.
git status --porcelain
```

---

### Step 5: Autosquash Rebase & Verification Loop

#### 1. Run Non-Interactive Autosquash Rebase

```bash
GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash --autostash "$BASE"
```

If a conflict occurs, resolve the conflicting files, `git add <resolved-files>`, and run `git rebase --continue`.

#### 2. Verify Clean State and No Remaining Screenshot Code

```bash
git status
# Diff against no-mistakes/$BRANCH should only show removed screenshot code/files (if any)
git diff "$BRANCH" "no-mistakes/$BRANCH"
git log "$BASE..HEAD" --oneline
# Run the repository's configured lint check (for example: just lint)
git branch -D "$BACKUP_REF"
```

If any expected non-screenshot remote change was dropped during conflict resolution, re-apply and amend before running project tests.

---

### Step 6: Push Amended Branch (and Optionally Anchor & Retrigger `no-mistakes`)

Push the amended branch to `origin`:

```bash
git push --force-with-lease origin "$BRANCH"
```

> **Important:** If the only difference from `no-mistakes/$BRANCH` is stripped screenshot code or if the user instructed not to re-run `no-mistakes` (since re-running `no-mistakes` may re-introduce screenshot code during `step test`), **stop here** after pushing to `origin` and running local lint/tests.

When a full `no-mistakes` re-run is required (for example, after rebasing onto a newer `origin/main` or folding substantive code changes), anchor the superseded pipeline head in the `no-mistakes` private mirror **both before and after** `no-mistakes axi sync --recover` (which moves `refs/no-mistakes/recover/<RUN_ID>` to `refs/no-mistakes/recover-rewritten/<RUN_ID>/1`):

```bash
export PATH="$HOME/.local/bin:$PATH"
OLD_RUN_ID=$(no-mistakes axi status 2>&1 | awk '/^run:/{f=1} f && /^  id:/{gsub(/"/, "", $2); print $2; exit}')
OLD_NM_HEAD=$(git rev-parse "no-mistakes/$BRANCH")
MIRROR=$(git remote get-url no-mistakes)

# If the previous run is still in post-push CI monitoring, abort it first
no-mistakes axi abort 2>/dev/null || true

if [ -n "$OLD_RUN_ID" ] && [ -n "$OLD_NM_HEAD" ] && [ -d "$MIRROR" ]; then
  git update-ref "refs/no-mistakes/recover/$OLD_RUN_ID" "$OLD_NM_HEAD"
  git --git-dir="$MIRROR" update-ref "refs/no-mistakes/recover/$OLD_RUN_ID" "$OLD_NM_HEAD"
fi

git push --force-with-lease origin "$BRANCH"
no-mistakes axi sync --recover 2>/dev/null || true

if [ -n "$OLD_RUN_ID" ] && [ -n "$OLD_NM_HEAD" ] && [ -d "$MIRROR" ]; then
  git update-ref "refs/no-mistakes/recover/$OLD_RUN_ID" "$OLD_NM_HEAD"
  git --git-dir="$MIRROR" update-ref "refs/no-mistakes/recover/$OLD_RUN_ID" "$OLD_NM_HEAD"
fi

no-mistakes axi run -y --intent "<concise description of the branch goal>"
```
