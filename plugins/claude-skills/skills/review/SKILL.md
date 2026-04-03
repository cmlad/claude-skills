---
name: review
description: Orchestrate iterative code review and improvement cycles on the current branch using a coding agent and parallel reviewers. Use when the user wants to review, polish, and improve an existing WIP branch.
user-invocable: true
argument-hint: <description of what the branch is supposed to do>
---

# Review Orchestrator

You are an orchestrator managing an iterative review and improvement lifecycle for the current branch. The objective of the branch is:

**$ARGUMENTS**

Follow these steps precisely:

## Step 1: Gather Existing PR Feedback

Check if the current branch is linked to a GitHub PR:

```bash
gh pr view --json number,url,comments,reviews
```

If a PR exists, collect all review comments and PR comments. Format them into a consolidated summary of existing feedback. If no PR exists, skip this and proceed with an empty feedback section.

## Step 2: Spawn the Coding Agent

Spawn a long-running coding agent using `codex exec` (the codex skill) with the following settings:
- Model: `gpt-5.4`
- Effort: `xhigh`
- Approval mode: `danger-full-access`

Give it the familiarize prompt below so it understands the branch, the task, and any existing PR feedback. Keep this process running throughout the lifecycle.

### Familiarize Prompt

> This is a WIP in progress branch. Familiarize yourself with the code. The aim of the branch is to:
>
> $ARGUMENTS
>
> The following existing review comments/feedback have been left on the PR (if any). Please read and understand them — you will be asked to address these along with new reviews:
>
> <EXISTING PR FEEDBACK — insert the consolidated comments and reviews gathered in Step 1, or "No existing PR feedback." if none>

## Step 3: Run Two Review Agents in Parallel

Spawn **two review agents in parallel**:

1. **Claude reviewer** — use a Claude agent with model `opus 4.6` and effort `x`. Give it the review prompt below.
2. **Codex reviewer** — use `codex exec` with model `gpt-5.4` and effort `xhigh`. Give it the review prompt below.

### Review Prompt (use for both reviewers)

> You are staff engineer who cares deeply about correctness, code quality and maintainability. Review this branch, specifically tell me about any logical issues, missing test coverage, organization, performance, and if the changes really address the objective below but are not over broad. Do not change any code. At the start of the review mention the latest Git commit SHA. The branch is supposed to do the following:
>
> $ARGUMENTS

## Step 4: Feed Reviews to Coding Agent

As each review agent returns its review, feed the review to the coding agent one at a time using the address review prompt below. Let the coding agent fix and push after each review.

### Address Review Prompt

> Please address the following review. Directly fix/improve the things you think should be addressed, commit and push the code to the PR.
>
> <REVIEW OUTCOME from the reviewer>

## Step 5: Repeat Review Cycles

Once the coding agent has addressed both reviews from a cycle, go back to **Step 3** and start a new review cycle. Repeat Steps 3-5 until:
- The coding agent has addressed everything it thinks it should, AND
- The review agents are generally happy with the code

Ensure the final code is pushed to the PR after each round of fixes.

## Step 6: Report Results

Once the review loop converges, tell the user:
- How many review cycles were completed
- The PR URL

## Step 7: Verify CI (MANDATORY — DO NOT SKIP)

**You MUST run the `/claude-skills:github-pr-green` skill now.** Do NOT end the conversation, do NOT report to the user, and do NOT consider the task complete until CI is fully green. Invoke the skill and wait for it to complete. If tests fail, feed the failures back to the coding agent to fix, push, and re-run the skill until all checks pass.

This step is not optional. The task is incomplete until CI passes.

---

## Important Notes

- Always keep the coding agent's process alive across the full lifecycle.
- Run the two reviewers in parallel for efficiency.
- Feed reviews to the coding agent sequentially (one at a time) so fixes don't conflict.
- Do not let the coding agent skip reviews — it should address each one thoughtfully.
- The review cycle should converge within 2-4 iterations in most cases. If it goes beyond 5, stop and report to the user.
- **Do NOT end or wrap up after pushing code.** You must always complete Step 7 (CI verification) before finishing.
