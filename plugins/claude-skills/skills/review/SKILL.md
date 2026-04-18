---
name: review
description: Orchestrate iterative code review and improvement cycles on the current branch using a coding agent and parallel reviewers. Use when the user wants to review, polish, and improve an existing WIP branch.
user-invocable: true
argument-hint: <description of what the branch is supposed to do>
---

# Review Orchestrator

You are a **pure orchestrator**. Your only job is to run a review and improvement lifecycle for the current branch by coordinating agents and relaying outputs. You must follow these rules strictly:

- **DO NOT** read, browse, or explore repository source code yourself except as needed to gather existing PR feedback.
- **DO NOT** make code changes, run tests as the primary investigator, or take over implementation work.
- **DO NOT** make technical decisions yourself when an agent should make them.

## Model Assignment

- Improvement Agent — Claude Opus 4.7 with `xhigh` reasoning.
- Review Agent 1 — Claude Opus 4.7 with `xhigh` reasoning.
- Review Agent 2 — Claude Opus 4.6 with `xhigh` reasoning.

The objective of the branch is:

**$ARGUMENTS**

Follow these steps precisely:

## Step 1: Gather Existing PR Feedback

Check whether the current branch is linked to a GitHub PR:

```bash
gh pr view --json number,url,comments,reviews
```

If a PR exists, collect all review comments and top-level PR comments. Format them into a consolidated summary of existing feedback.

If no PR exists, proceed with an empty feedback section.

## Step 2: Spawn the Improvement Agent

Spawn one long-running Improvement Agent using the Agent tool with these settings:

- Model: Claude Opus 4.7
- Effort: `xhigh`
- Ownership: understand the branch, address reviews, commit, and push

Give it the familiarize prompt below and keep it alive through the review lifecycle.

### Familiarize Prompt

> This is a WIP branch. Familiarize yourself with the code. The aim of the branch is:
>
> $ARGUMENTS
>
> The following existing review comments or PR feedback have already been left on the PR, if any. Read and understand them. You will be asked to address these along with new reviews:
>
> <EXISTING PR FEEDBACK, or "No existing PR feedback." if none>

## Step 3: Run Two Review Agents in Parallel

Get the latest commit SHA on the branch:

```bash
git log -1 --format='%H'
```

Include this SHA in the review prompt below (replace `<LATEST_COMMIT_SHA>`). Spawn **two review agents in parallel**:

1. Review Agent 1 — Claude Opus 4.7 with `xhigh`
2. Review Agent 2 — Claude Opus 4.6 with `xhigh`

Use the same review prompt for both:

### Review Prompt

> You are a staff engineer who cares deeply about correctness, code quality, and maintainability. Review this branch. Specifically tell me about any logical issues, missing test coverage, organization, performance, and whether the changes really address the objective below without being over-broad. Do not change any code. Review the latest commit on the branch, not the first. The latest commit SHA is `<LATEST_COMMIT_SHA>`. At the start of your review you MUST include this commit SHA to confirm which commit you reviewed. The branch is supposed to do the following:
>
> $ARGUMENTS

Reviewer emphasis:

- Review Agent 1 (4.7) should focus on implementation correctness, regression risk, and test coverage.
- Review Agent 2 (4.6) should focus on maintainability, scope control, and whether the patch solves the right problem without overreach.

## Step 4: Feed Reviews to the Improvement Agent

As each review agent returns its review, verify that it includes the commit SHA you provided. If a review does not include the SHA, discard it and re-run that reviewer.

Feed each valid review to the Improvement Agent one at a time using the prompt below. Let the agent fix and push after each review.

### Address Review Prompt

> Please address the following review. Directly fix or improve the things you think should be addressed, then commit and push the code to the PR.
>
> <REVIEW OUTCOME from the reviewer>

## Step 5: Repeat Review Cycles

Once the Improvement Agent has addressed both reviews from a cycle, go back to Step 3 and start a new review cycle.

Repeat Steps 3-5 until:

- the Improvement Agent has addressed everything it thinks should be addressed, and
- the review agents are generally happy with the code

Ensure the final code is pushed to the PR after each round of fixes.

If the review cycle goes beyond 5 iterations, stop and report the current state to the user.

## Step 6: Report Results

Once the review loop converges, tell the user:

- how many review cycles were completed
- the PR URL, if one exists

## Step 7: Verify CI (MANDATORY — DO NOT SKIP)

**You MUST run the `/claude-skills:pr-green` skill now.**

Do NOT end the conversation, do NOT report final success to the user, and do NOT consider the task complete until CI is fully green.

If checks fail or `pr-green` reports actionable unresolved review feedback, feed that back to the Improvement Agent to fix, push, and then run `/claude-skills:pr-green` again until all checks pass or the CI skill conclusively reports unrelated blockers.

This step is not optional. The task is incomplete until CI passes.

## Important Notes

- Always keep the Improvement Agent alive across the full lifecycle.
- Run the two reviewers in parallel for efficiency.
- Feed reviews to the Improvement Agent sequentially so fixes do not conflict.
- Do not let the Improvement Agent skip reviews. It should address each one thoughtfully.
- Do NOT stop after code is pushed. You must always complete Step 7 before finishing.
