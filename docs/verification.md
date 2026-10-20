# Single-operator rebuild verification

This records checks performed during the rebuild, not a claim that external
scanner installations have been tested.

## Passed

- Operator-supplied output from the corrected `verify.cmd` run confirms **All checks passed**:
  36 backend tests, 12 frontend tests, ESLint, TypeScript checks, and Vite production build.
- Storage migration preservation, idempotency, rollback, collision checks, and
  Windows temporary-database cleanup all passed in that run.
- Frontend automated tests: 12 passed.
- Frontend ESLint: no errors or warnings.
- Frontend TypeScript checks: passed.
- Python syntax compilation of `backend/app` and `backend/tests`: passed.
- Static reference scan: no remaining imports of removed authentication modules.
- Independent code review: no Critical or Important findings in inspected code.
  Its tool-refresh usability finding was corrected.

## Blocked in the automation environment

- Backend unittest discovery cannot import installed MarkupSafe/SQLAlchemy files
  because the execution environment denies access. Tests did not execute.
- Vite production build cannot load its configuration because esbuild is denied
  access while inspecting parent directories.
- npm dependency audit cannot reach the registry audit endpoint. The earlier
  user-reported audit findings have not been resolved or revalidated.

These automation-environment restrictions were bypassed operationally by running
the unchanged verification command in the operator's normal terminal. Its supplied
output confirms the rebuilt application passes the complete automated check suite.
The dependency audit remains pending; `verify.cmd` does not perform that audit.

## Still requires the operator's environment

- Back up local instance data, stop old servers, and restart the rebuilt app.
- Confirm old history survives first startup.
- Install/configure the selected scanners, start the dedicated ZAP daemon, and
  run a local fixture assessment.
- Review dependency audit results before publishing a release.

No live scan was initiated, no existing user database was modified by the agent,
and no GitHub repository was created or published.

## Follow-up: Windows storage-test cleanup

The operator ran `verify.cmd`: 36 backend tests ran, with four errors in storage
test cleanup. Assertions completed, but direct sqlite3 connections stayed open
and Windows refused to delete temporary databases (`WinError 32`). SQLite's
connection context manager controls transactions; it does not close connections.

Every direct connection in `test_storage.py` now uses `contextlib.closing` around
the transaction context. A standalone Windows reproduction confirmed transaction
commit, explicit close, and successful database deletion; syntax compilation
passed. The operator then reran `verify.cmd`: all 36 backend tests passed with no
cleanup errors, followed by all frontend checks and a successful production build.
The logged `RuntimeError: unavailable` is deliberately injected by the scanner
failure-isolation test, which passes. The outdated Browserslist database warning
does not fail the build.

## Scanner provisioning follow-up

The live backend returned `available: false` for all four tools. No scanner/Perl
installation was located on PATH or in the checked standard installation
directories; only Java 8 was detected. An attempted GitHub download from the
agent environment failed to connect.

Added `setup-scanners.ps1` for execution in the operator's normal Windows
terminal, and optional `PERL_PATH` support to avoid inheriting stale PATH after
installation. PowerShell syntax parsing and Python syntax compilation passed.
Installer execution, downloads, daemon startup and the additional interpreter
resolution regression test are not verified in this environment. This new
backend test was added after the operator's previous successful 36-test run.
