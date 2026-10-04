---
name: parallel-review-fix-swarm
description: Finds and fixes codebase issues concurrently by running isolated reviewer and fixer subagent swarms in dedicated git worktrees under .worktrees/ and merging fixes linearly with rebase and fast-forward. Use when performing systematic multi-module code reviews and parallel bug fixing across a repository.
---

# Parallel Review-Fix Swarm (`parallel-review-fix-swarm`)

## Overview

Runs two concurrent subagent swarms across isolated git worktrees under `.worktrees/`:

1. **Reviewer swarm:** Inspects assigned modules and writes structured issue files to `tmp/issues/<7hex>-<slug>.md`.
2. **Fixer swarm:** Claims issue files, implements root-cause fixes with tests in dedicated `.worktrees/fix-<hex>` worktrees, and commits atomic fixes.
3. **Linear integration:** Rebases each fix branch onto `HEAD` and merges with `git merge --ff-only` (no merge commits).

---

## Execution Checklist

```text
Swarm Progress:
- [ ] Phase 0: Create tmp/issues/ directory and ensure .worktrees/ and tmp/ are ignored
- [ ] Phase 1: Launch Reviewer Swarm in parallel across module groups
- [ ] Phase 2: Launch Fixer Swarm in dedicated .worktrees/fix-<hex> worktrees
- [ ] Phase 3: Rebase, verify tests, and fast-forward merge each fix branch linearly
- [ ] Phase 4: Remove temporary worktrees, branches, and tmp/issues/ artifacts
```

---

## Setup

```bash
mkdir -p .worktrees tmp/issues
```

Ensure `.worktrees/` and `tmp/` are listed in `.gitignore` (or `.git/info/exclude`).

---

## Phase 1 - Reviewer Swarm

Create one read-only worktree per module group (or review directly from the target branch) and launch all reviewers concurrently in the background:

```bash
git worktree add .worktrees/review-<module> -b review/<module>
```

**Reviewer prompt template:**

```text
Review <file(s)> in the repository at <absolute-path>.
Do NOT invoke any Skill tool.

For each verified defect (bug, security vulnerability, missing error handling, or logic error):
1. Generate a 7-char hex ID: $(openssl rand -hex 4 | head -c 7)
2. Write tmp/issues/<hex>-<slug>.md using the template below
3. Write one issue per file

Skip style nits and speculative concerns.
Report: total issues filed and their IDs.

Issue file format:
# <hex>-<slug>
**Severity:** high|medium|low
**File:** path/to/file:line
**Type:** bug|security|error-handling|logic
## Description
## Suggested Fix
```

---

## Phase 2 - Fixer Swarm

For each filed issue in `tmp/issues/<hex>-<slug>.md`, create an isolated git worktree and launch fixers concurrently:

```bash
git worktree add .worktrees/fix-<hex> -b fix/<slug>
```

**Fixer prompt template:**

```text
Read tmp/issues/<hex>-<slug>.md and work inside the worktree at <absolute-worktree-path>.
Do NOT invoke any Skill tool.

Steps:
1. Read the issue and inspect the target file around the noted lines
2. Reproduce or verify the root cause and implement a minimal, robust fix
3. Run the relevant unit/lint tests and confirm they pass
4. Commit with Conventional Commits format (wrap body at 72 cols, no Co-authored-by, no em dashes):
   fix(<module>): <concise imperative summary>

Do NOT modify unrelated files or bundle unrelated fixes.
Report: what changed, why, and which tests passed.
```

---

## Phase 3 - Linear Merge & Validation Loop

**Never create merge commits.** Integrate each `fix/<slug>` branch sequentially (shortest diff first to minimize conflicts):

```bash
# 1. Rebase the fix branch onto the current target branch HEAD
git rebase <target-branch> fix/<slug>

# 2. Fast-forward the target branch
git merge --ff-only fix/<slug>
```

- **Conflict & Test Loop:** If two fixers touched the same file and a rebase conflict occurs, resolve the conflict, run `git rebase --continue`, and re-run the affected test suite before advancing to the next branch.

---

## Phase 4 - Cleanup

```bash
# Remove temporary issue files
rm -rf tmp/issues/

# Remove swarm worktrees
git worktree list --porcelain \
  | awk '/^worktree /{print $2}' \
  | grep -E "\.worktrees/(fix|review)-" \
  | xargs -r -I{} git worktree remove --force {}

# Delete temporary fix/* and review/* branches
git branch | grep -E "^\s+(fix|review)/" | xargs -r git branch -D
```

---

## Key Pitfalls

| Pitfall                             | Prevention                                                                                  |
| :---------------------------------- | :------------------------------------------------------------------------------------------ |
| `git merge` creates a merge commit  | Always run `git rebase <target-branch> fix/<slug>` followed by `git merge --ff-only`.       |
| Subagent recursively invokes skills | Include `"Do NOT invoke any Skill tool."` in reviewer and fixer prompts.                    |
| Two fixers edit the same file       | Merge shortest diffs first; resolve conflicts during `git rebase` before `--ff-only`.       |
| Pre-commit hook reformats files     | Re-stage formatted files and amend before completing the fixer step.                        |
| Reviewer files low-value style nits | Restrict prompt to verified bugs, security issues, missing error handling, and logic flaws. |
