---
name: parallel-review-fix-swarm
description: Use when you want to systematically find and fix issues across a codebase by running reviewer and fixer sub-agents concurrently, each isolated in their own git worktree under .claude/worktrees/
---

# Parallel Review-Fix Swarm

## Overview

Two swarms run simultaneously: reviewers file `issues/<7hex>-<slug>.md`, fixers pick them up and fix them. Each agent owns an isolated git worktree. All merges are linear — rebase-then-FF, no merge commits ever.

## Setup

```bash
# Add worktree dir to .gitignore (revert at cleanup)
echo "/.claude/worktrees/" >> .gitignore
mkdir -p issues/
```

Add `.gitignore` line to track in git if needed, or keep it local. **Warning:** `git reset --hard` silently reverts uncommitted `.gitignore` changes — re-add the line after any hard reset.

## Phase 1 — Reviewer Swarm

Launch all reviewers **in one parallel message** (`run_in_background: true`). One agent per module/file group.

**Worktree per reviewer:**

```bash
git worktree add .claude/worktrees/review-<module> -b review/<module>
```

**Reviewer prompt template:**

```text
Review <file(s)> in the repo at <absolute-path>.
Do NOT invoke any Skill tool.

For each real issue (bug, security hole, missing error handling, logic error):
1. Generate a 7-char hex: $(openssl rand -hex 4 | head -c 7)
2. Write issues/<hex>-<slug>.md using the format below
3. One issue per file

Skip style nits and hypothetical future concerns.
Report: N issues filed, IDs listed.

Issue file format:
# <hex>-<slug>
**Severity:** high|medium|low
**File:** path/file:line
**Type:** bug|security|error-handling|logic
## Description
## Suggested Fix
```

## Phase 2 — Fixer Swarm

Launch all fixers **in one parallel message** — either simultaneously with reviewers (they wait for issue files to appear) or immediately after reviewers complete.

**Worktree per fixer:**

```bash
git worktree add .claude/worktrees/fix-<hex> -b fix/<slug>
```

**Fixer prompt template:**

```text
Read issues/<hex>-<slug>.md. Work in the repo at <absolute-path>.
Do NOT invoke any Skill tool.

Steps:
1. Read the issue; read the affected file at the noted line
2. Fix the root cause, not the symptom
3. Run tests if available
4. Commit: fix(<module>): <description>

Do NOT fix other issues you notice. Do NOT change unrelated code.
Report: what changed and why.
```

## Phase 3 — Merge (Linear History Only)

**Never `git merge` directly.** Always rebase first so `--ff-only` can apply cleanly.

```bash
# For each fix branch (one at a time, shortest diff first):
git rebase <current-HEAD> fix/<slug>
git merge --ff-only fix/<slug>
# Repeat — each subsequent branch rebases onto the updated HEAD
```

If two fixers touched the same file, expect a rebase conflict. Resolve it, then `git rebase --continue`.

## Phase 4 — Cleanup

```bash
# Remove issue files and commit (or just delete)
rm -rf issues/

# Remove all worktrees
git worktree list --porcelain \
  | awk '/^worktree /{print $2}' \
  | grep "\.claude/worktrees" \
  | xargs -I{} git worktree remove --force {}

# Delete fix/* and review/* branches
git branch | grep -E "^\s+(fix|review)/" | xargs git branch -D

# Revert .gitignore (remove the /.claude/worktrees/ line)
```

## Key Pitfalls

| Pitfall                                   | Fix                                                                         |
| ----------------------------------------- | --------------------------------------------------------------------------- |
| `git merge` creates merge commit          | Always rebase first, then `--ff-only`                                       |
| Hard reset silently reverts .gitignore    | Re-add `/.claude/worktrees/` after every `reset --hard`                     |
| Fixer invokes a Skill tool                | Add "Do NOT invoke any Skill tool" to prompt                                |
| Two fixers edit same file                 | Rebase them sequentially; first one conflicts, resolve, continue            |
| Pre-commit `fmt` hook reformats on commit | Re-stage reformatted files, re-commit                                       |
| Reviewer files too many nits              | Constrain prompt: "only real bugs, not style"                               |
| Cherry-pick order matters                 | Always rebase in chronological order; shortest diff first reduces conflicts |
