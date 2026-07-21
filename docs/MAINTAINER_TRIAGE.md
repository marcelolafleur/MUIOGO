# Maintainer Triage Guide

This document defines the triage vocabulary used on the project board — priorities, tracks, and stability lanes. These are maintainer-assigned metadata to organize work; they are not gates on contribution.

## Priorities

- `Priority: High` — work on ASAP
- `Priority: Medium` — important
- `Priority: Low` — may matter, can wait

Priority labels sync to the board's `Priority` field automatically (see `.github/workflows/sync-project-priority-from-labels.yml`).

## Tracks

- `Track: Cross-Platform`
  Cross-platform install, startup, path, and runtime compatibility work

- `Track: OG Onboarding`
  First-run UX, contributor/user guidance, onboarding flow, and related docs

- `Track: Integration`
  OG-Core, coupled workflows, orchestration, and integration interfaces

- `Track: Stability`
  Run safety, async execution design, shared-state integrity, run identity and status tracking, and runtime robustness

## Stability lanes

Internal triage vocabulary for Stability-track work.

- `Safety Guardrails`
  Narrow fixes that make the current synchronous design safer without redesigning execution flow

- `Async Architecture`
  Non-blocking job execution, polling, cancellation, and task orchestration proposals

- `Supporting Infrastructure`
  Run identity, atomic status tracking, shared metadata safety, and run-level observability work

## Handling duplicates and overlap

If an issue or PR clearly duplicates or supersedes existing work, consolidate rather than carrying parallel work: point to the canonical item and close the duplicate, or link the dependency explicitly. Maintainers decide whether a proposal is correct, useful, or merge-ready.
