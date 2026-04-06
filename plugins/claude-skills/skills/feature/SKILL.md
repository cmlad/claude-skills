---
name: feature
description: Orchestrate feature development with a coding agent and iterative review cycles. Use when the user wants to develop a feature end-to-end with automated coding, reviewing, and PR creation.
user-invocable: true
argument-hint: <task description>
---

# Feature Development Orchestrator

You are a **pure orchestrator**. This skill composes two sub-skills to deliver a feature end-to-end: first planning, then implementation.

Follow these steps precisely:

## Step 1: Plan the Feature

Run the `/claude-skills:plan-feature` skill with the following arguments:

**$ARGUMENTS**

Wait for it to complete. It will produce a finalized plan and output the full plan text. Capture the plan text from the skill's output — you will pass it to the next step.

## Step 2: Implement the Feature

Run the `/claude-skills:implement-feature` skill. Pass it both the original task description and the full plan text from Step 1:

> $ARGUMENTS
>
> ## Plan
>
> <FULL PLAN TEXT from Step 1>

Wait for it to complete. It will implement the plan, create a PR, run review cycles, and verify CI.

---

## Important Notes

- Do NOT proceed to Step 2 until Step 1 has fully completed.
- You MUST pass the plan text from Step 1 into Step 2's arguments — do not expect implement-feature to find it on its own.
- Do NOT read source code, make technical decisions, or do any implementation work yourself — the sub-skills handle everything.
- The task is not complete until the implement-feature skill finishes (including CI verification).
