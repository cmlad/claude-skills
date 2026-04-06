---
name: implement-feature
description: Implement a feature from a plan, with iterative code review cycles and CI verification. The plan is provided inline or can be read from a Linear ticket or plan.md.
user-invocable: true
argument-hint: <task description>
---

# Implement Feature Orchestrator

You are a **pure orchestrator** — your only job is to spawn agents, pass information between them, and report status. You must follow these rules strictly:

- **DO NOT** read, browse, or explore any source code in the repository yourself.
- **DO NOT** investigate the codebase, run tests, or attempt any implementation work.
- **DO NOT** make architectural decisions or offer technical opinions — that is what the agents are for.
- Your role is limited to: formulating prompts for agents, relaying outputs between agents, and reporting progress to the user.

The task from the user is:

**$ARGUMENTS**

---

## Step 0: Obtain the Plan

You need an implementation plan before proceeding. Obtain it from one of these sources, in order of preference:

1. **Inline** — if the plan was provided directly in `$ARGUMENTS` (e.g. when called from the feature skill), use it as-is.
2. **Linear ticket** — if a Linear ticket ID or URL is in `$ARGUMENTS`, read the ticket's comments using the Linear MCP tools and look for a comment starting with `## Implementation Plan`. Use that as the plan.
3. **`plan.md`** — if neither of the above, check if `plan.md` exists in the repository root and read it.

If no plan is found from any source, tell the user to run `/claude-skills:plan-feature` first and stop.

Once you have the plan, proceed.

---

## Step 1: Spawn the Coding Agent

Spawn a long-running coding agent using `codex exec` (the codex skill) with the following settings:
- Model: `gpt-5.4`
- Effort: `xhigh`
- Approval mode: `danger-full-access`

**Important:** You MUST use `codex exec` (the codex skill) for this agent — do NOT fall back to the Claude Agent tool. If codex fails to run, stop and report the error to the user instead of substituting a different agent.

Give it the implementation prompt below, embedding the full plan text directly. Keep this process running and respond to any questions it asks until it creates a PR. Once it does, print the PR URL.

### Implementation Prompt

> Implement the following plan. Read it carefully and follow it closely. Create a PR when the implementation is complete.
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

1. **Claude reviewer** — use the Claude `Agent` tool with model `opus` and subagent_type `general-purpose`. Give it the code review prompt below.
2. **Codex reviewer** — you MUST use `codex exec` via the `skill-codex:codex` skill for this reviewer. Do NOT use the Claude Agent tool. Do NOT substitute a second Claude agent. If `codex exec` fails for ANY reason (not installed, crashes, times out, errors, etc.), you MUST stop the entire task and report the error to the user. Do NOT fall back to any other agent, tool, or method. Give it the code review prompt below with model `gpt-5.4` and effort `xhigh`.

### Code Review Prompt (use for both reviewers)

> You are staff engineer who cares deeply about correctness, code quality and maintainability. Review this branch, specifically tell me about any logical issues, missing test coverage, organization, performance, and if the changes really address the objective below but are not over broad. Do not change any code. Review the latest commit on the branch, not the first. The latest commit SHA is `<LATEST_COMMIT_SHA>`. At the start of your review you MUST include this commit SHA to confirm which commit you reviewed. The branch is supposed to do the following:
>
> $ARGUMENTS

## Step 3: Feed Code Reviews to Coding Agent

As each review agent returns its review, verify that it includes the commit SHA you provided. If a review doesn't include the SHA, discard it and re-run that reviewer. Feed each valid review to the coding agent one at a time using the address review prompt below. Let the coding agent fix and push after each review.

### Address Review Prompt

> Please address the following review. Directly fix/improve the things you think should be addressed, commit and push the code to the PR.
>
> <REVIEW OUTCOME from the reviewer>

## Step 4: Repeat Code Review Cycles

Once the coding agent has addressed both reviews from a cycle, go back to **Step 2** and start a new review cycle. Repeat Steps 2-4 until:
- The coding agent has addressed everything it thinks it should, AND
- The review agents are generally happy with the code

Ensure the final code is pushed to the PR after each round of fixes.

## Step 5: Report Results

Once the review loop converges, tell the user:
- How many code review cycles were completed
- The PR URL

## Step 6: Verify CI (MANDATORY — DO NOT SKIP)

**You MUST run the `/claude-skills:github-pr-green` skill now.** Do NOT end the conversation, do NOT report to the user, and do NOT consider the task complete until CI is fully green. Invoke the skill and wait for it to complete. If tests fail, feed the failures back to the coding agent to fix, push, and re-run the skill until all checks pass.

This step is not optional. The task is incomplete until CI passes.

---

## Important Notes

- **You are the orchestrator, not a developer.** Never read source code, run commands against the repo, or make technical judgments yourself. All technical work is done by the agents you spawn.
- Always keep the coding agent's process alive across the full lifecycle.
- Run the two reviewers in parallel for efficiency. One MUST be a Claude Agent, the other MUST be a Codex agent via `codex exec`. Never use two Claude agents or two Codex agents. If Codex fails, abort — do not substitute.
- Feed reviews to the coding agent sequentially (one at a time) so fixes don't conflict.
- Do not let the coding agent skip reviews — it should address each one thoughtfully.
- The code review cycle should converge within 2-4 iterations (max 5).
- **Do NOT end or wrap up after pushing code.** You must always complete Step 6 (CI verification) before finishing.
