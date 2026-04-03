---
name: github-pr-green
description: Monitor a GitHub PR's CI checks, fix failures caused by the PR, retry flaky tests, and loop until all checks are green. Use when you need to get a PR to pass CI.
user-invocable: true
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
---

# Get PR Green

You are responsible for getting a GitHub PR's CI checks to all-green. You MUST keep polling and working until every check is green or you have conclusively proven remaining failures are unrelated to the PR. Do NOT stop early.

## Step 1: Identify the PR

Find the PR for the current branch:

```bash
gh pr view --json number,url,headRefName
```

If no PR exists, tell the user and stop — this skill requires an existing PR.

Push any uncommitted changes if needed:

```bash
git push
```

If there is no upstream branch yet:

```bash
git push -u origin HEAD
```

## Step 2: Wait For All Checks To Complete

You MUST actively poll until every single check has reached a terminal state (success, failure, or cancelled). No check may be left in pending/queued/in_progress state.

Use `gh pr checks --watch --fail-fast` to block until a failure occurs or all checks complete. This is the preferred method as it avoids manual polling.

```bash
gh pr checks --watch --fail-fast 2>&1 || true
```

After `--watch` exits (whether from a failure or all passing), get the full status:

```bash
gh pr checks --json name,bucket,state,link 2>&1
```

**CRITICAL**: If ANY check is still pending/in_progress/queued, you MUST continue waiting. Run `gh pr checks --watch` again or poll every 60 seconds. Do NOT proceed to the final report while checks are still running.

## Step 3: Handle Failures

When checks fail, you must determine if each failure is caused by the PR or unrelated.

### 3a: Get the PR diff

```bash
gh pr diff --name-only
```

### 3b: Get Failure Details

For each failed check, get the logs:

```bash
gh run view <run_id> --log-failed 2>&1 | tail -200
```

If output is too large, target a specific job:

```bash
gh run view <run_id> --json jobs --jq '.jobs[] | {id: .databaseId, name: .name, conclusion: .conclusion}'
gh run view <run_id> --job <job_id> --log-failed 2>&1 | tail -200
```

### 3c: Classify Failures

**PR-caused failures** (you MUST fix these):
- Lint errors on files changed in the PR
- Import errors or dependency issues from the PR's changes
- Test failures in tests that exercise code modified by the PR
- Any error message referencing functions, classes, or files in the PR diff

**Unrelated failures** (retry these):
- Test failures in code not touched by the PR
- Infrastructure flakes (network timeouts, Docker pull failures, runner issues)
- Tests that were already failing on the base branch
- Container build failures (almost never caused by code changes)

When unsure, check if the test was passing on the base branch:

```bash
gh run list --branch main --workflow "<workflow_name>" --limit 3 --json conclusion,databaseId
```

### 3d: Fix PR-Caused Failures

Read the failing code, understand the failure, and fix it. For lint errors, try auto-fixing first (e.g. `ruff check --fix . && ruff format .`).

After fixing, commit and push:

```bash
git add <specific files>
git commit -m "fix: address CI failures

Co-Authored-By: Claude <noreply@anthropic.com>"
git push
```

**Then go back to Step 2 and wait for ALL checks again.** Do NOT skip this.

### 3e: Retry Unrelated Failures

For failures not caused by the PR:

```bash
gh run rerun <run_id> --failed
```

After rerunning, **go back to Step 2 and wait for ALL checks again.** Do NOT skip this.

Track retry counts per workflow run. Retry up to 4 times per unrelated failure.

## Looping Until Green

You MUST repeat the cycle of Step 2 -> Step 3 until one of these conditions is met:

1. **All checks are green.** Report success and stop.
2. **All remaining failures are unrelated AND have been retried 4 times each.** Report the unrelated failures and stop.
3. **You have been looping for over 2 hours total.** Report current state and stop.

Do NOT exit the loop early. Do NOT report success while any check is still pending or failed. Each time you push a fix or retry a run, you MUST go back to Step 2 and wait again.

## Final Report

Only produce a final report when one of the exit conditions above is met.

If all checks pass:
```
All CI checks are green.
```

If unrelated failures persist after retries:
```
## CI Status

### Passing
All PR-related checks are green.

### Still Failing (unrelated to PR)

| Check Name | Workflow | Retries | Run URL |
|------------|----------|---------|---------|
| <name>     | <wf>     | 4/4     | <link>  |

### Failure Details

#### <Check Name>
- **Error**: <brief error from logs>
- **Why unrelated**: <explanation - e.g. "test does not touch any files in this PR's diff", "same failure on base branch">
```

$ARGUMENTS
