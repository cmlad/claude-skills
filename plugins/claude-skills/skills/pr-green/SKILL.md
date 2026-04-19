---
name: pr-green
description: Drive a GitHub PR to green by triaging unresolved review threads and looping on CI — fix PR-caused failures, retry flakes, and resolve review comments that the current code already addresses. Use when you need to get a PR across the finish line.
user-invocable: true
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
---

# Get PR Green

You are responsible for getting a GitHub PR fully green: every CI check must pass (or remaining failures must be conclusively unrelated), and every unresolved review thread must be triaged. You MUST keep looping until one of these is true:

- all checks are green and outstanding review threads have been triaged
- only unrelated failures remain after reasonable retries
- the run is conclusively blocked

Do NOT stop early.

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

## Step 2: Triage Unresolved Review Threads

Fetch unresolved review comments (line comments) and relevant top-level reviews:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate --jq '.[] | select(.in_reply_to_id == null) | {id: .id, path: .path, line: .line, original_line: .original_line, body: .body, diff_hunk: .diff_hunk, subject_type: .subject_type}'
```

```bash
gh api repos/{owner}/{repo}/pulls/{number}/reviews --paginate --jq '.[] | select(.body != "" and .body != null and .state != "DISMISSED") | {id: .id, body: .body, state: .state}'
```

For each unresolved thread:

1. **Read the comment** to understand what change was requested.
2. **Read the current code** at the referenced path and line area using the `Read` tool. Comments may reference shifted lines — use `diff_hunk` and surrounding context to locate the relevant code.
3. **Decide conservatively** whether the feedback has been addressed. Count as addressed only when you are confident — direct change, equivalent refactor, or deletion of the problematic code. If unsure, leave the thread unresolved.

For each thread you judge addressed:

- Reply with a short explanation:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies -f body="Done — <brief explanation of how the feedback was addressed>"
```

- Resolve the thread. First get its GraphQL node ID:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id} --jq '.node_id'
```

Then resolve:

```bash
gh api graphql -f query='mutation { resolveReviewThread(input: { threadId: "<node_id>" }) { thread { isResolved } } }'
```

If actionable unresolved feedback remains that the code has NOT addressed, fix it directly, commit, push, and repeat Step 2 before moving on.

## Always Comment After Pushing Code

Whenever you push a commit during this skill — whether to address review feedback or to fix CI failures — you MUST leave a top-level PR comment summarizing what that push addressed. Do this after every push, no exceptions.

```bash
gh pr comment <number> --body "$(cat <<'EOF'
Addressed in <short SHA>:

- <feedback item 1> — <how it was addressed>
- <feedback item 2> — <how it was addressed>
- <CI failure> — <fix>
EOF
)"
```

Keep the comment concrete: reference the specific review threads or check failures the push addresses, and briefly describe the change. If the push addresses nothing reviewer-visible (e.g. a pure flake retry), skip the comment.

## Always Update The PR Description After Pushing Code

After every push you make in this skill, you MUST also update the PR description so it stays in sync with what the branch actually does. Review cycles and CI fixes routinely extend a PR beyond what the original description covered — do not let the description go stale.

Fetch the current description, then edit it to reflect the current branch state:

```bash
gh pr view <number> --json body --jq '.body'
gh pr edit <number> --body "$(cat <<'EOF'
<updated summary reflecting the current branch state>

## Test plan
- <checklist>
EOF
)"
```

Update the summary, scope notes, and test plan as needed. Preserve anything the author wrote that is still accurate (context, linked issues, screenshots) — only rewrite the parts that no longer match the code. Skip the update only for pure flake retries where nothing on the branch changed.

## Step 3: Wait For All Checks To Complete

You MUST actively poll until every single check has reached a terminal state (success, failure, or cancelled). No check may be left in pending/queued/in_progress state.

Use `gh pr checks --watch --fail-fast` to block until a failure occurs or all checks complete:

```bash
gh pr checks --watch --fail-fast 2>&1 || true
```

After `--watch` exits, get the full status:

```bash
gh pr checks --json name,bucket,state,link 2>&1
```

**CRITICAL**: If ANY check is still pending/in_progress/queued, continue waiting. Run `gh pr checks --watch` again or poll every 60 seconds. Do NOT proceed to the final report while checks are still running.

## Step 4: Handle Failures

When checks fail, determine whether each failure is caused by the PR or unrelated.

### 4a: Get the PR diff

```bash
gh pr diff --name-only
```

### 4b: Get Failure Details

For each failed check:

```bash
gh run view <run_id> --log-failed 2>&1 | tail -200
```

If output is too large, target a specific job:

```bash
gh run view <run_id> --json jobs --jq '.jobs[] | {id: .databaseId, name: .name, conclusion: .conclusion}'
gh run view <run_id> --job <job_id> --log-failed 2>&1 | tail -200
```

### 4c: Classify Failures

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

### 4d: Fix PR-Caused Failures

Read the failing code, understand the failure, and fix it. For lint errors, try auto-fixing first (e.g. `ruff check --fix . && ruff format .`).

After fixing, commit and push:

```bash
git add <specific files>
git commit -m "fix: address CI failures

Co-Authored-By: Claude <noreply@anthropic.com>"
git push
```

**Then go back to Step 2 and re-triage review threads, then Step 3 and wait for ALL checks again.** Do NOT skip this.

### 4e: Retry Unrelated Failures

```bash
gh run rerun <run_id> --failed
```

After rerunning, go back to Step 3 and wait for ALL checks again. Track retry counts per workflow run and retry up to 4 times per unrelated failure.

## Looping Until Green

Repeat Steps 2 → 3 → 4 until one of these conditions is met:

1. **All checks are green AND all unresolved review threads have been triaged.** Report success and stop.
2. **All remaining failures are unrelated AND have been retried 4 times each, AND review threads have been triaged.** Report and stop.
3. **You have been looping for over 2 hours total.** Report current state and stop.

Do NOT exit the loop early. Do NOT report success while any check is pending or any actionable review thread remains unaddressed. Each time you push a fix or retry a run, go back to Step 2.

## Final Report

Only produce a final report when one of the exit conditions above is met.

If all checks pass and review feedback is triaged:
```
All CI checks are green. Unresolved review threads triaged: <N resolved>, <N still actionable>.
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
- **Why unrelated**: <explanation — e.g. "test does not touch any files in this PR's diff", "same failure on base branch">

### Review Threads
- Resolved this run: <N>
- Still open (actionable): <N>
- Still open (not addressed): <list with file:line>
```

$ARGUMENTS
