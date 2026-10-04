---
name: nm-apply-amend
description: Inspects diffs against the no-mistakes remote tracking branch, applies useful pipeline changes locally via git nm-apply, and amends each change into the originating commit on the current feature branch using git commit --fixup and autosquash rebase. Use when syncing no-mistakes pipeline fixes or remote review changes into existing branch history.
user-invocable: true
---

# no-mistakes Apply & Amend (`nm-apply-amend`)

Reviews changes produced by the `no-mistakes` validation pipeline on the remote `no-mistakes/<branch>` tracking ref, applies them locally via `git nm-apply`, and folds each change into the earlier commit on the active feature branch that originally touched those files.

---

## Core Principles

1. **Same-Branch Scope Only:** Only commits on the active feature branch (`$BASE..HEAD`) are candidates for amending. Never modify upstream `main`/`master` commits.
2. **File & Hunk Attribution:** Map each file modified by `git nm-apply` back to the specific branch commit that introduced or modified that file.
3. **Atomic History Over Fixup Noise:** Fold linter, review, test, and docs fixes directly into their originating commits rather than leaving trailing fixup commits at `HEAD`.
4. **Safety & Verification:** Always create a backup branch ref before rewriting history, and verify tree equivalence after rebasing.

---

## Execution Workflow

Copy this checklist and track progress:

```text
nm-apply-amend Progress:
- [ ] Step 1: Fetch no-mistakes remote and inspect incoming diff
- [ ] Step 2: Verify clean working tree, create backup ref, and run git nm-apply
- [ ] Step 3: Attribute modified files/hunks to originating branch commits with --fixup
- [ ] Step 4: Run non-interactive autosquash rebase onto merge-base
- [ ] Step 5: Verify zero unintended diff against no-mistakes/<branch> and run tests
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

_(Note: `git nm-apply` runs `GIT_PAGER= git diff $(git branch --show-current) no-mistakes/$(git branch --show-current) | git apply`.)_

---

### Step 3: Attribute and Stage Fixups to Branch Commits

Find the branch merge-base:

```bash
BASE=$(git merge-base origin/main HEAD 2>/dev/null || git merge-base main HEAD)
```

For each modified file (`git diff --name-only`), inspect commits on `$BASE..HEAD` that touched it:

```bash
git log "$BASE..HEAD" --format="%h %s" -- "$FILE"
```

#### Case A - Single commit touched the file

Stage the file and create a targeted fixup commit:

```bash
git add "$FILE"
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

for file in $(git diff --name-only); do
  mapfile -t COMMITS < <(git log "$BASE..HEAD" --format="%H" -- "$file")
  if [ "${#COMMITS[@]}" -ge 1 ]; then
    TARGET="${COMMITS[0]}"
    echo "Attributing $file -> $TARGET"
    git add "$file"
    git commit --no-verify --fixup="$TARGET"
  else
    echo "Manual attribution needed for $file (not modified in $BASE..HEAD)"
  fi
done
```

---

### Step 4: Autosquash Rebase & Verification Loop

#### 1. Run Non-Interactive Autosquash Rebase

```bash
GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash --autostash "$BASE"
```

If a conflict occurs, resolve the conflicting files, `git add <resolved-files>`, and run `git rebase --continue`.

#### 2. Verify Clean State and Zero Diff Against Remote

```bash
git status
git diff "$BRANCH" "no-mistakes/$BRANCH"
git log "$BASE..HEAD" --oneline
```

If any expected remote change was dropped during conflict resolution, re-apply and amend before running project tests.
