---
name: pr-comments
description: Review all unresolved comments on a GitHub PR, check if each is already addressed by the current code, and for solved ones reply with an explanation and resolve the thread. Use when you want to clean up addressed review feedback.
user-invocable: true
allowed-tools: Bash, Read, Grep, Glob
---

# PR Comments

You are responsible for reviewing all unresolved comments on a GitHub PR and resolving any that have already been addressed by the current code.

## Step 1: Identify the PR

Find the PR for the current branch:

```bash
gh pr view --json number,url,headRefName
```

If no PR exists, tell the user and stop.

## Step 2: Fetch All Review Comments

Get all review comments (these are comments on specific lines of code):

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate --jq '.[] | select(.in_reply_to_id == null) | {id: .id, path: .path, line: .line, original_line: .original_line, body: .body, diff_hunk: .diff_hunk, subject_type: .subject_type}'
```

Also check for top-level PR review comments that may contain actionable feedback:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/reviews --paginate --jq '.[] | select(.body != "" and .body != null and .state != "DISMISSED") | {id: .id, body: .body, state: .state}'
```

## Step 3: Check Resolution Status

For each review comment thread that is not already resolved, determine whether the feedback has been addressed:

1. **Read the comment** to understand what change was requested.
2. **Read the current version of the file** at the referenced path and line area. Use the `Read` tool to examine the current code.
3. **Compare against the feedback**: Has the code been changed to address the comment? Consider:
   - Direct code changes that implement the suggestion
   - Refactors that achieve the same goal differently
   - Removal of the problematic code entirely
   - Comments may reference lines that have shifted due to other changes — use the `diff_hunk` and surrounding context to locate the relevant code

**Be conservative**: Only mark a comment as resolved if you are confident the feedback has been fully addressed. If you're unsure, leave it unresolved.

## Step 4: Reply and Resolve

For each comment that has been addressed:

1. **Reply** to the comment thread explaining briefly how it was addressed:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies -f body="Done — <brief explanation of how the feedback was addressed>"
```

2. **Resolve** the comment thread. First find the GraphQL node ID for the thread:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id} --jq '.node_id'
```

Then resolve it:

```bash
gh api graphql -f query='mutation { resolveReviewThread(input: { threadId: "<node_id>" }) { thread { isResolved } } }'
```

## Step 5: Report

After processing all comments, produce a summary:

```
## PR Comments Summary

### Resolved
- **<file>:<line>** — <brief comment summary> → <how addressed>

### Still Open
- **<file>:<line>** — <brief comment summary> → <why still open>

### Stats
- Total comment threads: <N>
- Resolved by this run: <N>
- Already resolved: <N>
- Still open: <N>
```

$ARGUMENTS
