---
inclusion: always
---

# Git Workflow — okf-mcp

All changes to this repository MUST go through a pull request. Never push directly to `main`.

## Required workflow

1. Create a feature branch from `main` with a descriptive name (e.g. `fix/fetch-degenerate-vectors`, `feat/input-validation`)
2. Commit changes to the feature branch
3. Push the branch with `-u` to set up tracking
4. Provide the user with the PR creation URL that GitHub prints after pushing a new branch (the `remote: Create a pull request...` link)

## Branch naming conventions

- `fix/` — bug fixes
- `feat/` — new features
- `chore/` — maintenance, refactoring, docs updates
- `security/` — security-related changes

## Rules

- Never push directly to `main`, even for small changes
- Never use `--force` push unless explicitly asked
- Keep PRs focused — one logical change per PR
