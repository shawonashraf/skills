---
name: git-rules
description: Git workflow rules for coding agents. Governs when and how to commit, when NOT to touch branches, when to prompt before pushing, and how to handle remote conflicts safely.
license: MIT
---

# Git Rules for Coding Agents

Rules for how a coding agent should interact with git after completing a task. The guiding principle: **the agent owns commits, the user owns branches and remotes.**

## 1. Commit After Every Completed Task

Once a task is finished and tested, stage and commit the changes.

- Write a commit message that reflects **why** the change was made, not just what files changed.
- Scope the commit to the task — don't bundle unrelated cleanup or speculative changes.
- Follow the existing commit style in the repo (check `git log` before writing the first message).
- Never commit files that likely contain secrets (`.env`, credentials, private keys). Warn the user if they ask you to. Respect the `.gitignore` and if needed ask the user if a file or directory should be added to `.gitignore` in case you are not sure or if the said file or directory are artifacts of a program.
- Stage specific files by name. Avoid `git add -A` or `git add .` unless you have explicitly reviewed every untracked file.

## 2. Never Touch Branches Uninstructed

Branch management is the user's domain. Do not:

- Create, rename, or delete branches
- Switch the working branch (`git checkout`, `git switch`)
- Merge branches
- Rebase onto another branch

**Only act on branch operations if the user explicitly asks.** Phrases like "merge this", "switch to main", or "create a feature branch" are explicit. Implicit hints ("this should probably go on a separate branch") are not — ask for clarification instead.

## 3. Always Prompt Before Pushing

After committing, ask the user whether to push the current branch to the remote before running `git push`.

Prompt format (adapt to context):
> "Changes committed. Should I push the current branch (`<branch-name>`) to the remote?"

Do not push silently, even if the user said "commit and push" earlier in a different task — confirm each time.

## 4. Handle Remote Conflicts Carefully

If a push or sync with the remote fails due to conflicts, diverged history, or merge issues:

1. **First, ask the user** whether they want to handle it themselves or delegate it to you.
2. If delegated to you:
   a. Inspect the conflict (`git status`, `git log --oneline --graph`, `git diff`) before planning anything.
   b. Draft a plain-language plan: what you intend to do, in order, and what you will NOT do (e.g., "I will not force-push").
   c. Show the plan to the user and wait for **explicit approval** before executing a single step.
   d. Never force-push (`--force`, `--force-with-lease`) without the user reading and approving that specific action in the plan.
3. If the user says they'll handle it, stop and wait. Do not offer partial fixes or run diagnostic commands unless asked.

## 5. Never Use Destructive Git Commands Without Explicit Instruction

The following commands must not run without explicit user request and confirmation:

- `git push --force` / `git push --force-with-lease`
- `git reset --hard`
- `git checkout -- .` / `git restore .`
- `git clean -f` / `git clean -fd`
- `git branch -D`
- Amending published commits (`git commit --amend` after a push)

If you believe one of these is the right fix, explain why in plain language and let the user decide.

## Quick Reference

| Situation | Agent action |
|---|---|
| Task complete and tested | Commit with a clear message |
| About to push | Ask the user first |
| User says "create a branch" | Do it |
| User hints at a branch change | Ask for clarification |
| Remote conflict on push | Ask user: self-handle or delegate? |
| Delegated conflict resolution | Plan → show → wait for approval → execute |
| Force-push needed | State why, show it in the plan, require explicit approval |
