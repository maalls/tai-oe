---
applyTo: 'sage/**'
---

# Sage Folder Copilot Instructions

These instructions apply only to files under the sage folder.

## Working Mode

1. Move very slowly, in tiny increments.
2. Execute only one micro-step at a time.
3. Before changing code, explain the exact next micro-step in plain language.
4. After each micro-step, stop and ask for approval before continuing.
5. Do not jump ahead, even if the next steps seem obvious.

## Communication Style

1. Assume the user is new to .NET.
2. Keep explanations simple, short, and concrete.
3. Avoid jargon when possible; if jargon is used, define it in one sentence.
4. Prefer examples over abstract explanations.

## Coding Rules

1. Prefer minimal, reversible edits.
2. Keep each commit-sized change focused on one objective.
3. Do not introduce architectural complexity early.
4. Add only the smallest amount of code needed for the current micro-step.
5. Keep defaults explicit and safe.

## Execution Safety

1. Do not run destructive commands.
2. Validate after each change with the smallest relevant check.
3. If an error appears, stop and explain the cause before fixing.
4. Present at most one fix path at a time unless asked for alternatives.

## Plan Adherence

1. Use the plan in sage/PLAN.md as the source of truth.
2. Follow phases in order unless the user explicitly changes priorities.
3. Mark progress clearly: current step, result, next step.

## Step Completion Ritual

After the user approves that a step is done, always perform these two actions before moving on:

1. **Strike out the completed step in `sage/PLAN.md`**: wrap the action line with `~~…~~` (e.g. `- ~~Action: verify dotnet is installed~~`).
2. **Commit the changes to git**: stage all modified files and commit with a short, descriptive message that names the completed step (e.g. `git add -A && git commit -m "sage: phase 0.1 — verify dotnet tooling"`).

Do not skip either action, and do not proceed to the next step until both are done.

## Integration Goal Reminder

Target outcome:

1. Query Sage for data such as clients.
2. Post data such as quotes.
3. Expose this through a reliable service used by Ai Oe.
