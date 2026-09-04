---
name: incremental-squash
description: Squash changes on a git feature branch into clean, atomic, incremental conventional commits (feat, fix, chore, docs, test, refactor) by logically grouping diffs, verifying tests, and preserving a clean Git history. Use when asked to squash changes on a branch into incremental commits, organize messy commit histories, or structure PR commits.
user-invocable: true
---

# Incremental Squash

`incremental-squash` transforms a messy, multi-commit feature branch (containing fixups, WIP commits, test iterations, and merge noise) into a clean, bisectable sequence of logical, incremental **Conventional Commits** (`feat`, `fix`, `chore`, `docs`, `test`, `refactor`).

---

## Core Principles

1. **Zero Content Drift**: The final tree (`HEAD`) after squashing must be identical (`git diff HEAD backup_ref` is completely empty) to the tree before squashing.
2. **Bisectability**: Every intermediate commit should build cleanly and pass relevant unit tests whenever possible.
3. **Atomic Grouping**: Each commit must represent a single coherent concern (e.g. backend endpoint + backend test, frontend service + UI component, or documentation updates).
4. **Safety First**: Always create an immutable backup ref/tag before performing any history rewrite.

---

## Step-by-Step Execution Workflow

### Step 1: Pre-Flight Safety & Base Detection

1. **Verify Branch**: Ensure you are on a feature branch and **never directly on `main` or `master`**.

   ```bash
   CURRENT_BRANCH=$(git branch --show-current)
   if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
     echo "Error: Cannot squash directly on $CURRENT_BRANCH branch."
     exit 1
   fi
   ```

2. **Detect Merge Base**:

   ```bash
   BASE_COMMIT=$(git merge-base origin/main HEAD 2>/dev/null || git merge-base main HEAD)
   ```

3. **Create Safety Backup Ref**:

   ```bash
   BACKUP_REF="backup/${CURRENT_BRANCH}-$(date +%s)"
   git branch "$BACKUP_REF" HEAD
   echo "Created backup ref: $BACKUP_REF"
   ```

---

### Step 2: Inspect & Analyze the Full Diff

Examine the aggregated changes between the merge base and `HEAD`:

```bash
git diff --stat "$BASE_COMMIT"..HEAD
git diff --name-status "$BASE_COMMIT"..HEAD
```

Group changed files into logical layers:

- **Layer 1: Backend / API Core (`feat(api)` or `fix(api)`)**: Data models, endpoints, database queries, server-side services, and their colocated unit tests.
- **Layer 2: Frontend Services & State (`feat(ui)` or `fix(ui)`)**: Client services, API clients, state management, and service spec tests.
- **Layer 3: Frontend UI Components (`feat(ui)` or `fix(ui)`)**: Angular/React components, templates, styling, and component spec tests.
- **Layer 4: Infrastructure & Build (`chore(...)` or `infra(...)`)**: Terraform, Dockerfile, Makefile, package.json, scripts.
- **Layer 5: End-to-End Tests (`test(...)` or `chore(tests)`)**: Playwright, Cypress, or integration test suites.
- **Layer 6: Documentation (`docs(...)`)**: README, architecture docs, TODOs, API specs.

---

### Step 3: Soft Reset to Merge Base

Perform a soft reset to un-commit all changes while preserving all edits in the working index and working directory:

```bash
git reset --soft "$BASE_COMMIT"
```

Unstage all files so you can stage each logical group individually:

```bash
git reset
```

---

### Step 4: Incrementally Stage and Commit

For each logical layer identified in Step 2:

1. **Stage Related Files**:

   ```bash
   git add path/to/file1 path/to/file2 path/to/related_test.spec.ts
   ```

   _If a single file contains changes spanning multiple concerns, use patch staging:_

   ```bash
   git add -p path/to/file
   ```

2. **Commit with Conventional Commits Standard**:
   Follow the format:

   ```text
   <type>(<scope>): <short imperative subject>

   [optional body explaining motivation, context, and key decisions]
   ```

   **Allowed Types:**
   - `feat`: New feature or user-facing capability.
   - `fix`: Bug fix or error resolution.
   - `chore`: Build scripts, dependencies, auxiliary tooling, maintenance.
   - `docs`: Documentation changes, TODO updates, guides.
   - `test`: Adding or refactoring tests without application code changes.
   - `refactor`: Code changes that neither fix a bug nor add a feature.
   - `perf`: Performance improvements.

3. **Verify Intermediate Build / Tests** (if fast):
   Run relevant local tests or lint checks for the staged files before proceeding to the next commit.

---

### Step 5: Post-Squash Tree Equivalence Verification

1. **Assert Zero Code Drift**:

   ```bash
   # Must produce NO output
   git diff HEAD "$BACKUP_REF"
   ```

   If `git diff` produces any output, inspect why files or lines were missed and reconcile them before proceeding.

2. **Run Full Test Suite**:
   Execute repository test suites to ensure everything compiles and passes:

   ```bash
   # Run project test commands (e.g. backend + frontend tests)
   pytest tests/unit/
   npm test
   ```

3. **Display Clean Commit Log**:

   ```bash
   git log "$BASE_COMMIT"..HEAD --oneline
   ```

4. **Cleanup Backup (Optional)**:
   Keep `$BACKUP_REF` available until the user confirms satisfaction or pushes the branch.

---

## Example Execution

```bash
# 1. Check branch and create backup
git branch backup/my-feature-branch HEAD

# 2. Soft reset to base
git reset --soft $(git merge-base main HEAD)
git reset

# 3. Commit 1: Backend Endpoint & Test
git add backend/api.py tests/unit/test_api.py
git commit -m "feat(api): add export endpoint with format options"

# 4. Commit 2: Frontend Service & Component
git add src/app/services/export.service.ts src/app/components/export/
git commit -m "feat(ui): add ExportButton component and export service integration"

# 5. Commit 3: Documentation
git add docs/API.md
git commit -m "docs(api): document export endpoint schema and query parameters"

# 6. Verify zero drift
git diff HEAD backup/my-feature-branch
```
