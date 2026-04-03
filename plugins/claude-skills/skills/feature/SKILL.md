---
name: feature
description: Orchestrate feature development with a coding agent and iterative review cycles. Use when the user wants to develop a feature end-to-end with automated coding, reviewing, and PR creation.
user-invocable: true
argument-hint: <task description>
---

# Feature Development Orchestrator

You are an orchestrator managing a feature development lifecycle. The task to accomplish is:

**$ARGUMENTS**

Follow these steps precisely:

## Step 1: Spawn the Coding Agent

Spawn a long-running coding agent using `codex exec` (the codex skill) with the following settings:
- Model: `gpt-5.4`
- Effort: `xhigh`
- Approval mode: `danger-full-access`

Give it the full task described above. Keep this process running and respond to any questions it asks until it creates a PR. Once it does, print the PR URL.

## Step 2: Run Two Review Agents in Parallel

Once the PR is up, spawn **two review agents in parallel**:

1. **Claude reviewer** — use a Claude agent with model `opus 4.6` and effort `x`. Give it the review prompt below.
2. **Codex reviewer** — use `codex exec` with model `gpt-5.4` and effort `xhigh`. Give it the review prompt below.

### Review Prompt (use for both reviewers)

> You are staff engineer who cares deeply about correctness, code quality and maintainability. Review this branch, specifically tell me about any logical issues, missing test coverage, organization, performance, and if the changes really address the objective below but are not over broad. Do not change any code. At the start of the review mention the latest Git commit SHA. The branch is supposed to do the following:
>
> $ARGUMENTS

## Step 3: Feed Reviews to Coding Agent

As each review agent returns its review, feed the review to the coding agent one at a time using the address review prompt below. Let the coding agent fix and push after each review.

### Address Review Prompt

> Please address the following review. Directly fix/improve the things you think should be addressed, commit and push the code to the PR.
>
> <REVIEW OUTCOME from the reviewer>

## Step 4: Repeat Review Cycles

Once the coding agent has addressed both reviews from a cycle, go back to **Step 2** and start a new review cycle. Repeat Steps 2-4 until:
- The coding agent has addressed everything it thinks it should, AND
- The review agents are generally happy with the code

Ensure the final code is pushed to the PR after each round of fixes.

## Step 5: Report Results

Once the review loop converges, tell the user:
- How many review cycles were completed
- The PR URL

## Step 6: Verify CI

Use the github-tests skill to check that the PR passes all tests. If tests fail, feed the failures back to the coding agent to fix, then re-verify.

---

## Important Notes

- Always keep the coding agent's process alive across the full lifecycle.
- Run the two reviewers in parallel for efficiency.
- Feed reviews to the coding agent sequentially (one at a time) so fixes don't conflict.
- Do not let the coding agent skip reviews — it should address each one thoughtfully.
- The review cycle should converge within 2-4 iterations in most cases. If it goes beyond 5, stop and report to the user.
