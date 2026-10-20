# Single-operator Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement these tasks in order.

**Goal:** Deliver a local scanner without accounts, with preserved history and complete setup instructions.
**Architecture:** React calls a Flask JSON API. SQLite stores local scans; a single worker runs four scanner adapters.
**Tech Stack:** Python 3.13, Flask, SQLite, React, TypeScript, Node 24.
**Spec:** `docs/superpowers/specs/2026-10-20-single-operator-rebuild-design.md`

## Global Constraints

- Preserve scan records and archived legacy tables.
- Keep exact target allowlisting and one active scan.
- Bind development servers to loopback.
- No GitHub publication or remote creation is included.
- Execute directly in this session; the user requested completion after design review.

## Review Focus

- Migration collisions must fail without modifying existing data.
- Cross-origin browser requests must not trigger local scans.
- Unavailable scanners must produce actionable responses.
- Existing URLs must lead to the scanner.
- Interrupted workers must retain their error state on restart.

## Task 1: Persistence and API

- [x] Add `backend/app/storage.py`: transactional `initialize_storage()` migrates legacy scans, validates rows, retains legacy tables, and rejects collisions.
- [x] Update `backend/app/__init__.py`, `models/scan.py`, `models/__init__.py`, `routes/api.py`, and `services/scan_manager.py` to remove users and sessions.
- [x] Add a local request guard and shared tool availability service; require JSON mutations and reject untrusted Origins/Host headers.
- [x] Remove `backend/app/auth/` source and `models/user.py`.
- [x] Replace API tests, adapt worker tests, and add migration preservation/idempotency/collision tests.
- [x] Run backend unittest discovery (36 passed in operator-supplied output).

## Task 2: Frontend

- [x] Update `App.tsx` to show Scanner at `/` and redirect old entry routes.
- [x] Update Scanner and API client to load tools/history directly without account state.
- [x] Remove unused auth and landing code, update translations and route helpers.
- [x] Update API/UI tests for ordinary JSON requests and scanner titles.
- [x] Run frontend tests, lint, typecheck, and build (all passed in operator-supplied output).

## Task 3: Distribution

- [x] Rewrite README, API docs, security guidance, contributing guide, and environment example.
- [x] Ignore all local runtimes, caches, databases, reports, and secrets.
- [x] Document Windows and Linux setup, scanner installation, startup and troubleshooting.
- [x] Review source references and final checks; record any environment limitations honestly.

## Execution ledger

Ruling: execute directly after the user's instruction to complete all requirements.
No Git executable or repository metadata is available, so edits remain in the
supplied working folder without a worktree or commits.

Ruling: preserve browser Origin/Host checks without login; removing accounts
does not mean allowing unrelated websites to trigger local scans.

Ruling: add explicit script paths for native Windows scanner setup; callers
still use canonical tool IDs and subprocess argument arrays.

Ruling: continue code changes despite blocked backend imports/build permissions;
record verification as pending, never as a passing test. Backend test-first
red/green execution was not possible in this environment.

Frontend tests (12), lint, typecheck, and Python syntax compilation passed here.
After fixing explicit SQLite connection closing in the migration tests, the
operator's `verify.cmd` output confirms all 36 backend tests, all frontend checks,
and Vite production build passed. Live scanners and dependency audit remain
unverified. See `docs/verification.md`.

Independent read-only review found no Critical/Important code issues; its minor
tool-refresh finding was fixed and frontend checks passed afterward. No deferred
code findings. Existing database and configuration values were preserved.
