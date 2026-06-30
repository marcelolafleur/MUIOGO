# Contributing to MUIOGO

Thanks for contributing.

## Before starting

1. Read `README.md`, `docs/GSoC-2026.md`, `SUPPORT.md`, `docs/ARCHITECTURE.md`, and `docs/DOCS_POLICY.md`
2. Search existing issues and PRs before proposing implementation work
3. Create or reuse an issue before starting implementation work
4. Create a feature branch from `main`
5. Confirm acceptance criteria in the issue so review can be objective

## Scope and repository boundaries

- This repo is downstream from `OSeMOSYS/MUIO` and must be deliverable on its own
- Do not block work here on upstream changes
- Upstream collaboration is encouraged, but this repo needs independent completion
- `MUIO-Mac` may be referenced, but `MUIOGO` targets platform-independent operation

## Issue prioritization and tracks

We use the following priority system:
- High: issues that should be worked on ASAP
- Medium: important issues
- Low: issues that may be important but that can wait

Priorities and track labels are assigned by maintainers.

Current tracks:
- `Track: Cross-Platform`
- `Track: OG Onboarding`
- `Track: Integration`
- `Track: Stability`

## Issues and PRs

- Search existing issues and PRs first so we avoid duplicate work.
- For anything beyond a small fix, open an issue before implementation so scope and acceptance criteria are clear.
- Link the issue from your PR (`Closes #123`).
- Keep each PR scoped to one issue, or a tightly related set.
- If you find related work, link it so any overlap is visible — a quick reference is enough.

## Workflow

1. Start from an issue
2. Create a feature branch from `main`
3. Keep branch changes scoped to one issue or one tightly related set of issues
4. Include tests or validation steps whenever behavior changes
5. Update docs for any setup, architecture, or workflow change
6. Open a PR into `EAPD-DRB/MUIOGO:main` using the repository PR template

## Required branching rule

Every implementation contribution must use:
- an issue for scope and acceptance criteria
- a feature branch for implementation

Suggested branch format:
- `feature/<issue-number>-short-description`

## Communication model

This project uses event-driven updates (no weekly cadence requirement).
Post updates when one of these events occurs:
- Work started
- Blocked longer than 48 hours
- PR opened
- PR ready for review
- Milestone completed

## PR requirements

- Clear description of what changed and why
- Link to issue(s)
- Validation evidence:
  - test output, or
  - reproducible manual verification steps
- Docs updated when needed
- No unrelated refactors in the same PR
- PR target is `EAPD-DRB/MUIOGO:main` (not upstream `OSeMOSYS/MUIO`)

Small docs or typo-only PRs do not need a linked issue.

## Definition of done

A task is done when:

1. Acceptance criteria in the issue are met
2. Code and docs are updated together
3. Reviewer feedback is resolved
4. Changes are merged to `EAPD-DRB/MUIOGO:main`
