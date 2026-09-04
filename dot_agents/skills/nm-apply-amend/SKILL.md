---
name: nm-apply-amend
description: Inspect diff against no-mistakes remote, fetch useful changes with git nm-apply, and cleanly amend them into earlier commits on the current branch that touched the same files. Use when syncing no-mistakes pipeline fixes or remote review changes into existing branch history.
user-invocable: true
---

# no-mistakes Apply & Amend (`nm-apply-amend`)

`nm-apply-amend` reviews changes produced by the `no-mistakes` validation pipeline on the remote `no-mistakes` tracking branch, applies them locally via `git nm-apply`, and intelligently **amends each change into earlier commits on the same branch that originally touched those files**, maintaining an atomic, bisectable, and clean Git history.

---

## Core Principles

1. **Same-Branch Scope Only**: Only commits on the active feature branch (between `merge-base` and `HEAD`) are candidates for amending. Upstream/base commits (`main`/`master`) must never be modified.
2. **File & Hunk Attribution**: Each file modified by `git nm-apply` is mapped back to the specific commit on the current branch that introduced or modified that file.
3. **Atomic History over Fixup Noise**: Rather than leaving trailing "fix linter", "fix review comments", or "pipeline auto-fix" commits on top of `HEAD`, changes are cleanly folded into their originating commits.
4. **Safety & Verification**: Always create a safety branch ref before rewriting history, and verify tree integrity after the rebase.

---

## Step-by-Step Execution Workflow

### Step 1: Fetch and Inspect the Remote Diff

1. **Identify Branch and Fetch Remote**:

   ```bash
   BRANCH=$(git branch --show-current)
   if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
     echo "Error: Must be on a feature branch, not $BRANCH."
     exit 1
   fi

   git fetch no-mistakes "$BRANCH" 2>/dev/null || git fetch no-mistakes
   ```

2. **Inspect Incoming Changes**:

   ```bash
   # Summary stat of changes on remote
   git diff --stat "$BRANCH" "no-mistakes/$BRANCH"

   # Full patch review
   git diff "$BRANCH" "no-mistakes/$BRANCH"
   ```

3. **Evaluate Utility**:
   - Assess whether the remote changes (e.g. linter fixes, typo corrections, test assertions, formatting, documentation fixes) are valid and desirable.
   - If the remote branch is identical (`git diff` is empty) or changes are not useful, notify the user and stop.

---

### Step 2: Create Safety Backup & Apply Changes Locally

1. **Ensure Clean Working Tree**:

   ```bash
   if [ -n "$(git status --porcelain)" ]; then
     echo "Error: Working directory is not clean. Commit or stash existing changes."
     exit 1
   fi
   ```

2. **Create Safety Backup Ref**:

   ```bash
   BACKUP_REF="backup/${BRANCH}-pre-nm-apply-$(date +%s)"
   git branch "$BACKUP_REF" HEAD
   echo "Created backup ref: $BACKUP_REF"
   ```

3. **Apply Remote Diff Locally**:

   ```bash
   git nm-apply
   ```

   _(Note: `git nm-apply` is an alias for `GIT_PAGER= git diff $(git branch --show-current) no-mistakes/$(git branch --show-current) | git apply`)_

4. **Verify Applied Changes**:

   ```bash
   git status --short
   ```

---

### Step 3: Attribute and Stage Fixups to Branch Commits

1. **Find Merge Base**:

   ```bash
   BASE=$(git merge-base origin/main HEAD 2>/dev/null || git merge-base main HEAD)
   ```

2. **Map Each Modified File to Its Originating Commit on the Branch**:
   For each file changed in the working tree:

   ```bash
   MODIFIED_FILES=$(git diff --name-only)
   ```

   For each file:
   - Query commits on the branch that touched this file:

     ```bash
     COMMITS=$(git log "$BASE..HEAD" --format="%h %s" -- "$FILE")
     ```

   - **Case A — Single commit touched the file**:
     The target is unambiguous. Stage the file and create a fixup commit:

     ```bash
     git add "$FILE"
     TARGET_HASH=$(git log "$BASE..HEAD" --format="%H" -- "$FILE" | head -n 1)
     git commit --fixup="$TARGET_HASH"
     ```

   - **Case B — Multiple commits on the branch touched the file**:
     Inspect which commit's changes are being modified:

     ```bash
     git log -p "$BASE..HEAD" -- "$FILE"
     ```

     Use patch staging (`git add -p "$FILE"`) to separate hunks if they belong to different commits, or target the latest commit that touched the relevant logic.

   - **Case C — File was not touched by any commit on this branch** (new file created by remote pipeline or pre-existing base file):
     Stage the file and either create a fixup targeting the main feature commit on the branch, or create a new logical commit (e.g. `test(...)` or `docs(...)`).

---

### Step 4: Automated Attribution Helper (Optional Script)

To automatically generate `--fixup` commits for all modified files where attribution on the branch is single-commit:

```bash
BASE=$(git merge-base origin/main HEAD 2>/dev/null || git merge-base main HEAD)

for file in $(git diff --name-only); do
  # Find all commit hashes on the current branch touching this file
  COMMITS=($(git log "$BASE..HEAD" --format="%H" -- "$file"))

  if [ ${#COMMITS[@]} -eq 1 ]; then
    TARGET="${COMMITS[0]}"
    echo "Attributing $file -> $TARGET"
    git add "$file"
    git commit --no-verify --fixup="$TARGET"
  elif [ ${#COMMITS[@]} -gt 1 ]; then
    # Default to latest commit touching the file on the branch
    TARGET="${COMMITS[0]}"
    echo "Attributing $file (latest of multiple) -> $TARGET"
    git add "$file"
    git commit --no-verify --fixup="$TARGET"
  else
    echo "Warning: $file was not modified in $BASE..HEAD; staging manually needed."
  fi
done
```

---

### Step 5: Autosquash Rebase & Clean History

1. **Execute Non-Interactive Autosquash Rebase**:

   ```bash
   GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash --autostash "$BASE"
   ```

2. **Handle Any Conflicts**:
   If a rebase conflict occurs:
   - Check `git status` to see conflicting files.
   - Resolve conflicts and stage resolved files (`git add <resolved-files>`).
   - Continue rebase: `git rebase --continue`.

3. **Verify Result**:
   - Check that working tree is clean:

     ```bash
     git status
     ```

   - Verify that the diff against `no-mistakes/$BRANCH` is now resolved (empty or only contains intentionally excluded changes):

     ```bash
     git diff "$BRANCH" "no-mistakes/$BRANCH"
     ```

   - Review clean commit history:

     ```bash
     git log "$BASE..HEAD" --oneline
     ```

4. **Run Verification / Tests**:
   Run project tests or linter to confirm everything compiles and passes cleanly.

---

## Quick Reference Summary

| Phase                 | Command                                                                           | Purpose                                         |
| --------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------- |
| **1. Inspect**        | `git fetch no-mistakes && git diff HEAD no-mistakes/$(git branch --show-current)` | Review remote pipeline changes                  |
| **2. Backup & Apply** | `git branch backup/... HEAD && git nm-apply`                                      | Save current HEAD and apply patch               |
| **3. Fixup**          | `git add <file> && git commit --fixup=<commit-hash>`                              | Create fixup commits targeted to branch commits |
| **4. Autosquash**     | `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash "$BASE"`                     | Fold all fixes into their parent commits        |
| **5. Verify**         | `git diff HEAD no-mistakes/$(git branch --show-current)`                          | Confirm zero drift against remote               |
