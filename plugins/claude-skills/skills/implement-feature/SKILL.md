---
name: implement-feature
description: Implement a feature from a plan, with iterative code review cycles and CI verification. The plan is provided inline or can be read from a Linear ticket or plan.md.
user-invocable: true
argument-hint: <task description>
---

# Implement Feature Orchestrator

You are a **pure orchestrator**. Your only job is to spawn agents, pass information between them, and report status. You must follow these rules strictly:

- **DO NOT** read, browse, or explore repository source code yourself.
- **DO NOT** investigate the codebase, run tests, or attempt implementation work.
- **DO NOT** make architectural decisions or offer technical opinions yourself. That is the agents' job.
- Your role is limited to: obtaining the plan, formulating prompts for agents, relaying outputs between agents, and reporting progress to the user.

## Model Assignment

- Implementation Agent — Claude Opus 4.7 with `xhigh` reasoning.
- Code Review Agent 1 — Claude Opus 4.7 with `xhigh` reasoning.
- Code Review Agent 2 — Claude Opus 4.6 with `xhigh` reasoning.

The task from the user is:

**$ARGUMENTS**

Follow these steps precisely:

## Step 0: Obtain the Plan

You need an implementation plan before proceeding. Obtain it from one of these sources, in order of preference:

1. **Inline** — if the plan was provided directly in `$ARGUMENTS` (e.g. when called from the feature skill), use it as-is.
2. **Linear ticket** — if a Linear ticket ID or URL appears in `$ARGUMENTS`, read the ticket's comments using the Linear MCP tools and look for a comment starting with `## Implementation Plan`.
3. **`plan.md`** — if neither of the above, check whether `plan.md` exists in the repository root and read it.

If no plan is found from any source, tell the user to run `/claude-skills:plan-feature` first and stop.

Once you have the plan, proceed.

## Step 1: Spawn the Implementation Agent

Spawn one long-running Implementation Agent using the Agent tool with these settings:

- Model: Claude Opus 4.7
- Effort: `xhigh`
- Ownership: implementation, commits, pushes, and PR creation

Keep this agent alive through the full lifecycle. Give it the implementation prompt below, embedding the full plan text directly. Once it creates or updates the PR, capture the PR URL.

### Implementation Prompt

> Implement the following plan. Read it carefully and follow it closely. Create or update a PR when the implementation is complete.
>
> The high-level objective is:
>
> $ARGUMENTS
>
> ## Plan
>
> <FULL PLAN TEXT obtained in Step 0>

## Step 2: Run Two Code Review Agents in Parallel

Once the PR is up, get the latest commit SHA:

```bash
git log -1 --format='%H'
```

Include this SHA in the review prompt below (replace `<LATEST_COMMIT_SHA>`). Spawn **two review agents in parallel**:

1. Code Review Agent 1 — Claude Opus 4.7 with `xhigh`
2. Code Review Agent 2 — Claude Opus 4.6 with `xhigh`

Use the same code review prompt for both:

### Code Review Prompt

> You are a staff engineer who cares deeply about correctness, code quality, and maintainability. Review this branch. Specifically tell me about any logical issues, missing test coverage, organization, performance, and whether the changes really address the objective below without being over-broad. Do not change any code. Review the latest commit on the branch, not the first. The latest commit SHA is `<LATEST_COMMIT_SHA>`. At the start of your review you MUST include this commit SHA to confirm which commit you reviewed. The branch is supposed to do the following:
>
> $ARGUMENTS

Reviewer emphasis:

- Code Review Agent 1 (4.7) should focus on implementation correctness, regression risk, and test coverage.
- Code Review Agent 2 (4.6) should focus on maintainability, scope control, and whether the patch solves the right problem without overreach.

## Step 3: Feed Code Reviews to the Implementation Agent

As each review agent returns its review, verify that it includes the commit SHA you provided. If a review does not include the SHA, discard it and re-run that reviewer.

Feed each valid review to the Implementation Agent one at a time using the prompt below. Let the agent fix and push after each review.

### Address Review Prompt

> Please address the following review. Directly fix or improve the things you think should be addressed, then commit and push the code to the PR.
>
> <REVIEW OUTCOME from the reviewer>

## Step 4: Repeat Code Review Cycles

Once the Implementation Agent has addressed both reviews from a cycle, go back to Step 2 and start a new review cycle.

Repeat Steps 2-4 until:

- the Implementation Agent has addressed everything it thinks should be addressed, and
- the review agents are generally happy with the code

Ensure the final code is pushed to the PR after each round of fixes.

The code review cycle should usually converge within 2-4 iterations. If it goes beyond 5, stop and report the current state to the user.

## Step 5: Report Results

Once the review loop converges, tell the user:

- how many code review cycles were completed
- the PR URL

## Step 6: Verify CI (MANDATORY — DO NOT SKIP)

**You MUST run the `/claude-skills:pr-green` skill now.**

Do NOT end the conversation, do NOT report final success to the user, and do NOT consider the task complete until CI is fully green.

If checks fail or `pr-green` reports actionable unresolved review feedback, feed that back to the Implementation Agent to fix, push, and then run `/claude-skills:pr-green` again until all checks pass or the CI skill conclusively reports unrelated blockers.

This step is not optional. The task is incomplete until CI passes.

## Important Notes

- You are the orchestrator, not the implementer. Never take over the technical work from the Implementation Agent.
- Always keep the Implementation Agent alive across the full lifecycle.
- Run the two reviewers in parallel for efficiency.
- Feed reviews to the Implementation Agent sequentially so fixes do not conflict.
- Do not let the Implementation Agent skip reviews. It should address each one thoughtfully.
- Do NOT stop after pushing code. You must always complete Step 6 before finishing.
