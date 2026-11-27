---
name: incremental-squash
description: Squashes a multi-commit git feature branch into clean, atomic, bisectable Conventional Commits (feat, fix, chore, docs, test, refactor, perf) with zero tree drift. Use when squashing branch commits into incremental commits, cleaning up WIP or fixup history, or structuring PR commits.
user-invocable: true
---

# Incremental Squash (`incremental-squash`)

Transforms a multi-commit feature branch (containing WIP commits, fixups, test iterations, or merge noise) into a clean, bisectable sequence of atomic **Conventional Commits** (`feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`).

---

## Core Principles

1. **Zero Content Drift:** The final tree (`HEAD`) after squashing must be byte-for-byte identical (`git diff HEAD "$BACKUP_REF"` is empty) to the tree before squashing.
2. **Bisectability:** Every intermediate commit must build cleanly and pass its relevant tests.
3. **Atomic Grouping:** Each commit represents one coherent concern (for example backend endpoint + unit test, frontend service + component, or documentation).
4. **Safety First:** Always create a backup branch ref before rewriting history.
5. **No In-Scope Fix Commits:** A branch must not carry `fix`, `docs`, `style`,
   `test`, `chore` or `refactor` commits that correct, tidy, clean up, or
   harden work within the branch's own scope, including pre-existing code the
   feature reworks or removes. Fold each such change into the feature commit
   it belongs to (for example, dropping obsolete objects lands with the commit
   that replaces or re-homes them). A safeguard required by the feature (for
   example tolerating a schema column the branch adds) lands with that
   feature. Separate commits of these types are only for changes genuinely
   outside the branch's scope; a `refactor` commit is only valid when the
   branch's purpose is the refactor itself.

---

## Execution Workflow

Copy this checklist and track progress:

```text
Incremental Squash Progress:
- [ ] Step 1: Verify non-main feature branch, detect merge-base, and create backup ref
- [ ] Step 2: Inspect full diff against merge-base and plan logical commit layers
- [ ] Step 3: Soft reset to merge-base and unstage all changes
- [ ] Step 4: Stage and commit each logical layer using Conventional Commits
- [ ] Step 5: Verify zero tree drift (git diff HEAD "$BACKUP_REF") and run test suite
```

### Step 1: Pre-Flight Safety & Base Detection

#### 1. Verify Feature Branch (Never Run on `main` or `master`)

```bash
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
  echo "Error: Cannot squash directly on $CURRENT_BRANCH branch."
  exit 1
fi
```

#### 2. Detect Merge Base

```bash
BASE_COMMIT=$(git merge-base origin/main HEAD 2>/dev/null || git merge-base main HEAD)
```

#### 3. Create Backup Ref

```bash
BACKUP_REF="backup/${CURRENT_BRANCH}-$(date +%s)"
git branch "$BACKUP_REF" HEAD
echo "Created backup ref: $BACKUP_REF"
```

---

### Step 2: Inspect & Plan Logical Commit Layers

Examine all changes between `$BASE_COMMIT` and `HEAD`:

```bash
git diff --stat "$BASE_COMMIT"..HEAD
git diff --name-status "$BASE_COMMIT"..HEAD
```

Group changed files into ordered dependency layers:

- **Layer 1 - Backend / Core (`feat(api)` or `fix(api)`):** Data models, endpoints, database queries, backend services, and colocated unit tests.
- **Layer 2 - Frontend Services & State (`feat(ui)` or `fix(ui)`):** Client services, API clients, state stores, and service unit tests.
- **Layer 3 - Frontend UI Components (`feat(ui)` or `fix(ui)`):** UI components, templates, styles, and component tests.
- **Layer 4 - Infrastructure & Build (`chore(...)`):** Terraform, Dockerfiles, Makefiles, `package.json`, scripts.
- **Layer 5 - End-to-End Tests (`test(...)`):** Playwright, Cypress, or E2E test suites.
- **Layer 6 - Documentation (`docs(...)`):** `README.md`, architecture docs, API specs.

Before committing, check every planned non-`feat` layer (`fix`, `docs`,
`style`, `test`, `chore`, `refactor`) against Core Principle 5: if it touches
code the branch introduces, reworks, or removes, merge it into the owning
feature layer instead of committing it separately.

**Example:**
Input: A dashboard branch planned as `docs: English comment in view SQL`,
`fix: pair dashboard turns correctly`, `feat: scope dashboard views to v3`,
`fix: keep events when the new column lags the schema`, `feat: log tokens`
Output: `feat: scope dashboard views to v3` (includes the comment and pairing
corrections) and `feat: log tokens` (includes the schema-lag safeguard)

Input: A branch moving dashboard views into Terraform planned as
`refactor: drop unused dashboard views`, `feat: manage dashboard views in
Terraform`
Output: `feat: manage dashboard views in Terraform` (only the views the
dashboard reads are adopted; the body explains why the rest are dropped)

---

### Step 3: Soft Reset to Merge Base

Un-commit all branch commits while keeping every modification intact in the working tree:

```bash
git reset --soft "$BASE_COMMIT"
git reset
```

---

### Step 4: Incrementally Stage and Commit

#### 1. Stage Related Files (or Hunks)

```bash
git add path/to/module.py path/to/test_module.py
# Or stage specific hunks when a file spans multiple logical commits:
git add -p path/to/shared_file.py
```

#### 2. Commit Following Conventional Commits & Formatting Rules

- Wrap commit body prose at **72 columns**.
- Explain non-obvious trade-offs and rationale in the body.
- Use plain hyphens (`-`), never em dashes.
- Never add an agent as a commit co-author (`Co-authored-by:`).

**Example 1:**
Input: Added JWT login endpoint, token validation middleware, and unit tests
Output:

```text
feat(auth): implement JWT-based authentication

Add the login endpoint and bearer token validation middleware. Verify
token expiration and signature claims in unit tests before routing
protected API requests.
```

**Example 2:**
Input: Fixed timezone bug in report date formatting
Output:

```text
fix(reports): normalize report timestamps to UTC

Convert incoming client timestamps to UTC before date truncation so
daily aggregation boundaries remain consistent across caller timezones.
```

---

### Step 5: Validation Loop (Zero Drift & Test Suite)

#### 1. Verify Zero Tree Drift

```bash
# Must produce empty output
git diff HEAD "$BACKUP_REF"
```

If `git diff HEAD "$BACKUP_REF"` is non-empty or `git status --porcelain` shows untracked/unstaged files from the branch, stage and fold the missing changes into the appropriate commit (via `git commit --fixup=<sha>` and `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash "$BASE_COMMIT"`), then re-run `git diff HEAD "$BACKUP_REF"` until empty.

#### 2. Run Repository Test Suite

Execute the project's unit/lint verification commands and confirm the new commit log:

```bash
git log "$BASE_COMMIT"..HEAD --oneline
```
