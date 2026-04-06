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

**Important:** You MUST use `codex exec` (the codex skill) for this agent — do NOT fall back to the Claude Agent tool. If codex fails to run, stop and report the error to the user instead of substituting a different agent.

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

First, get the latest commit SHA on the branch:

```bash
git log -1 --format='%H'
```

Include this SHA in the review prompt below (replace `<LATEST_COMMIT_SHA>`). Spawn **two review agents in parallel**:

1. **Claude reviewer** — use the Claude `Agent` tool with model `opus` and subagent_type `general-purpose`. Give it the review prompt below.
2. **Codex reviewer** — you MUST use `codex exec` via the `skill-codex:codex` skill for this reviewer. Do NOT use the Claude Agent tool. Do NOT substitute a second Claude agent. If `codex exec` fails for ANY reason (not installed, crashes, times out, errors, etc.), you MUST stop the entire task and report the error to the user. Do NOT fall back to any other agent, tool, or method. Give it the review prompt below with model `gpt-5.4` and effort `xhigh`.

### Review Prompt (use for both reviewers)

> You are staff engineer who cares deeply about correctness, code quality and maintainability. Review this branch, specifically tell me about any logical issues, missing test coverage, organization, performance, and if the changes really address the objective below but are not over broad. Do not change any code. Review the latest commit on the branch, not the first. The latest commit SHA is `<LATEST_COMMIT_SHA>`. At the start of your review you MUST include this commit SHA to confirm which commit you reviewed. The branch is supposed to do the following:
>
> $ARGUMENTS

## Step 4: Feed Reviews to Coding Agent

As each review agent returns its review, verify that it includes the commit SHA you provided. If a review doesn't include the SHA, discard it and re-run that reviewer. Feed each valid review to the coding agent one at a time using the address review prompt below. Let the coding agent fix and push after each review.

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
- Run the two reviewers in parallel for efficiency. One MUST be a Claude Agent, the other MUST be a Codex agent via `codex exec`. Never use two Claude agents or two Codex agents. If Codex fails, abort — do not substitute.
- Feed reviews to the coding agent sequentially (one at a time) so fixes don't conflict.
- Do not let the coding agent skip reviews — it should address each one thoughtfully.
- The review cycle should converge within 2-4 iterations in most cases. If it goes beyond 5, stop and report to the user.
- **Do NOT end or wrap up after pushing code.** You must always complete Step 7 (CI verification) before finishing.
