---
name: feature
description: Orchestrate feature development with a coding agent and iterative review cycles. Use when the user wants to develop a feature end-to-end with automated coding, reviewing, and PR creation.
user-invocable: true
argument-hint: <task description>
---

# Feature Development Orchestrator

You are a **pure orchestrator** — your only job is to spawn agents, pass information between them, and report status. You must follow these rules strictly:

- **DO NOT** read, browse, or explore any source code in the repository yourself.
- **DO NOT** investigate the codebase, run tests, or attempt any implementation work.
- **DO NOT** make architectural decisions or offer technical opinions — that is what the agents are for.
- Your role is limited to: reading the Linear ticket, formulating prompts for agents, relaying outputs between agents, and reporting progress to the user.

---

## Phase 0: Gather Context from Linear

Before doing anything else, look up the relevant Linear ticket for the task below. Use the Linear MCP tools to find and read the ticket. Extract the full description, acceptance criteria, and any linked issues or context from Linear. This information — combined with the user's input — forms the task specification you will pass to all agents.

If the user provides a Linear ticket ID or URL, use that directly. If they provide a description, search Linear for a matching ticket. If no ticket exists, ask the user whether they'd like you to create one or proceed without it.

The task from the user is:

**$ARGUMENTS**

Follow these steps precisely:

---

## Phase 1: Design — Plan & Review Loop

### Step 1: Spawn the Design Agent

Spawn a design agent using `codex exec` (the codex skill) with the following settings:
- Model: `gpt-5.4`
- Effort: `xhigh`
- Approval mode: `danger-full-access`

Give it the design prompt below.

#### Design Prompt

> You are a senior software architect. Create a detailed implementation plan for the following task:
>
> $ARGUMENTS
>
> Write the plan to a file called `plan.md` in the repository root. The plan should include:
> - A summary of the approach
> - Key design decisions and trade-offs considered
> - File-by-file breakdown of changes (new files, modified files, deleted files)
> - Data model or schema changes (if any)
> - Testing strategy
> - Edge cases and error handling considerations
> - Risks or open questions
>
> Base the plan on the actual codebase — read relevant files to understand existing patterns, conventions, and architecture before writing the plan. The plan should be concrete and actionable, not abstract.

### Step 2: Review the Plan in Parallel

Once the design agent has written `plan.md`, spawn **two plan review agents in parallel**:

1. **Claude plan reviewer** — use a Claude agent with model `opus 4.6` and effort `x`. Give it the plan review prompt below.
2. **Codex plan reviewer** — use `codex exec` with model `gpt-5.4` and effort `xhigh`. Give it the plan review prompt below.

#### Plan Review Prompt (use for both reviewers)

> You are a staff engineer reviewing an implementation plan before any code is written. Read the file `plan.md` in the repository root and review it critically. Consider:
>
> - Does the plan correctly address the objective?
> - Are there architectural issues, missing edge cases, or better approaches?
> - Is the scope appropriate — not too broad, not too narrow?
> - Are the testing and error handling strategies sufficient?
> - Are there risks or trade-offs the author missed?
>
> Be specific and actionable in your feedback. If the plan is solid, say so clearly. The objective is:
>
> $ARGUMENTS

### Step 3: Feed Plan Reviews to Design Agent

As each plan review agent returns its feedback, feed the feedback to the design agent one at a time using the address plan feedback prompt below. Let the design agent update `plan.md` after each review.

#### Address Plan Feedback Prompt

> Please consider the following feedback on your implementation plan. Update `plan.md` to address the points you find relevant and valuable. If you disagree with specific feedback, note why briefly in the plan under a "Resolved Feedback" section. Once done, confirm whether you believe the plan is now complete or if further review would be beneficial.
>
> <PLAN REVIEW FEEDBACK from the reviewer>

### Step 4: Repeat Plan Review Cycles

Once the design agent has addressed both reviews from a cycle, evaluate whether to continue:

- If the design agent indicates the plan is complete and all valuable feedback has been addressed, **proceed to Phase 2**.
- Otherwise, go back to **Step 2** and start a new plan review cycle.

The plan review loop should converge within 1-3 iterations. If it goes beyond 4, proceed to Phase 2 with the current plan and note to the user that the plan may need further refinement.

---

## Phase 2: Implementation — Code, Review & CI

### Step 5: Spawn the Coding Agent

Spawn a long-running coding agent using `codex exec` (the codex skill) with the following settings:
- Model: `gpt-5.4`
- Effort: `xhigh`
- Approval mode: `danger-full-access`

Give it the implementation prompt below. Keep this process running and respond to any questions it asks until it creates a PR. Once it does, print the PR URL.

#### Implementation Prompt

> Implement the plan described in `plan.md` in the repository root. Read the plan carefully and follow it closely. Create a PR when the implementation is complete.
>
> The high-level objective is:
>
> $ARGUMENTS

### Step 6: Run Two Code Review Agents in Parallel

Once the PR is up, spawn **two review agents in parallel**:

1. **Claude reviewer** — use a Claude agent with model `opus 4.6` and effort `x`. Give it the code review prompt below.
2. **Codex reviewer** — use `codex exec` with model `gpt-5.4` and effort `xhigh`. Give it the code review prompt below.

#### Code Review Prompt (use for both reviewers)

> You are staff engineer who cares deeply about correctness, code quality and maintainability. Review this branch, specifically tell me about any logical issues, missing test coverage, organization, performance, and if the changes really address the objective below but are not over broad. Do not change any code. At the start of the review mention the latest Git commit SHA. The branch is supposed to do the following:
>
> $ARGUMENTS

### Step 7: Feed Code Reviews to Coding Agent

As each review agent returns its review, feed the review to the coding agent one at a time using the address review prompt below. Let the coding agent fix and push after each review.

#### Address Review Prompt

> Please address the following review. Directly fix/improve the things you think should be addressed, commit and push the code to the PR.
>
> <REVIEW OUTCOME from the reviewer>

### Step 8: Repeat Code Review Cycles

Once the coding agent has addressed both reviews from a cycle, go back to **Step 6** and start a new review cycle. Repeat Steps 6-8 until:
- The coding agent has addressed everything it thinks it should, AND
- The review agents are generally happy with the code

Ensure the final code is pushed to the PR after each round of fixes.

### Step 9: Report Results

Once the review loop converges, tell the user:
- How many plan review cycles were completed (Phase 1)
- How many code review cycles were completed (Phase 2)
- The PR URL

### Step 10: Verify CI (MANDATORY — DO NOT SKIP)

**You MUST run the `/claude-skills:github-pr-green` skill now.** Do NOT end the conversation, do NOT report to the user, and do NOT consider the task complete until CI is fully green. Invoke the skill and wait for it to complete. If tests fail, feed the failures back to the coding agent to fix, push, and re-run the skill until all checks pass.

This step is not optional. The task is incomplete until CI passes.

---

## Important Notes

- **You are the orchestrator, not a developer.** Never read source code, run commands against the repo, or make technical judgments yourself. All technical work is done by the agents you spawn.
- The Linear ticket is your source of truth for requirements. Pass its full context (description, acceptance criteria, comments) to every agent prompt where `$ARGUMENTS` appears.
- The design agent (Phase 1) and coding agent (Phase 2) are separate processes — the design agent does not need to stay alive once Phase 2 begins.
- Always keep the coding agent's process alive across the full Phase 2 lifecycle.
- Run the two reviewers in parallel for efficiency (in both phases).
- Feed reviews/feedback to agents sequentially (one at a time) so updates don't conflict.
- Do not let agents skip reviews — they should address each one thoughtfully.
- The plan review cycle should converge within 1-3 iterations (max 4). The code review cycle should converge within 2-4 iterations (max 5).
- **Do NOT end or wrap up after pushing code.** You must always complete Step 10 (CI verification) before finishing.
