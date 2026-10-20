# GitHub preparation and reliability plan

> Historical record of the account edition. Superseded by
> [the single-operator design](superpowers/specs/2026-10-20-single-operator-rebuild-design.md)
> and [current implementation plan](superpowers/plans/2026-10-20-single-operator.md).
> For current setup and verification commands, use the root README.

Goal: make SecScan a reproducible local security-tool orchestration project with trustworthy combined results.

The user authorized implementing the preceding review and removing unnecessary material. Keep Flask, SQLite, React, TypeScript, and the four existing scanner integrations. Work in the supplied folder: it has no .git directory and Git is unavailable, so there is no branch or worktree to isolate. Do not create or publish a remote repository.

## Design

- Use signed, HttpOnly Flask sessions, CSRF tokens, server-side login verification, and scan ownership. Store the signing key in ignored instance data unless supplied through the environment. Restrict browser origins.
- Persist scan jobs/results in SQLite, with bounded background execution and explicit interrupted-job recovery. Reject unsupported tools and invalid targets. Default scan scope to localhost; require administrators to configure any other exact allowed hosts. Scanner networks must also be isolated to constrain redirects/crawlers.
- Keep adapter subprocess calls without a shell. Use one adapter result shape: execution status, findings, observations, errors. Errors and completion messages must never count as vulnerabilities. Nmap services are observations.
- Normalize issue types, locations and parameters, retain raw evidence and source confidence, and correlate only matching issues. An automated scanner report is not proof of exploitability. Do not correlate unrelated endpoints or infer disagreement when a tool failed or was not selected.
- Preserve the visual identity. Replace the standalone login demo with React authentication, remove unsupported tool options, show real execution state and correlated evidence, and use credentialed API calls through a development proxy.
- Remove generated scan artifacts, obsolete planning docs/models, duplicate result processors, mock naming, unused UI scaffolding, and redundant package-manager files after reference checks. Preserve the existing user database; exclude it from publication.
- Add root setup/API/contribution/security documentation, environment examples, meaningful regression tests, and CI. The owner selected MIT during implementation; add the MIT license.

## Tasks and verification ledger

- [x] Backend regression tests added: 25 cases covering authentication, CSRF, ownership, input/scope validation, capacity, persistence, error isolation, correlation, reports and ZAP cleanup. Runtime execution is blocked below.
- [x] Backend implementation: app configuration/security, job persistence, bounded runner, normalized adapters, reports.
- [x] Frontend implementation: real auth, typed API, scanner lifecycle, evidence/confidence, error/empty states, truthful copy.
- [x] Cleanup and documentation: checked imports before removal; deleted unused source/templates and generated report files; preserved the ignored account database. Empty ignored cache directories remain because recursive directory deletion was rejected.
- [ ] Verification: backend full test suite; frontend lint, type check, build; browser checks where runtime is available; independent review and fixes.

Review focus: malformed JSON; cross-user access; failed/not-selected SQLMap; overlapping ZAP jobs; host/port and IPv6 parsing; redirects and scan scope; restart during a job; lost browser session.

Baseline: frontend build fails because node_modules has no working Vite executable. Python and Git are not on PATH. Investigate local uv/runtime availability and reinstall dependencies inside this workspace if possible. No baseline test suite exists.

## Verification results

- Passed: all six frontend Node tests (credentialed API calls, CSRF headers, unauthorized responses, in-progress results, HTTP errors, real progress and active-state handling).
- Passed: all local frontend imports resolve; package and regenerated lockfile match. npm regenerated the lockfile in offline mode after unused dependencies were removed.
- Passed: Impeccable mechanical detector reported no findings for changed UI targets.
- Independent static review: corrected over-broad issue matching, SQLMap execution diagnostics, partial scan outcomes, and interrupted-job timestamps. Follow-up found no definite important bugs or obvious test failures.
- Blocked: Python tests could not start because the available uv Python trampoline cannot spawn its interpreter (permission denied). Downloading an isolated interpreter was blocked by network policy.
- Blocked: frontend lint, typecheck and build could not start because ESLint, TypeScript and Vite are unavailable. npm dependency downloads were blocked by network policy. The pre-existing dependency folder was already incomplete at baseline.
- Not performed: browser rendering, live scanner integration checks, online dependency vulnerability audits, or a GitHub upload. These must be verified in an environment with the required runtimes/dependencies before release.

Ruling: continue authorized implementation with explicit runtime verification limits rather than misreport blocked checks as passing. CI contains the full test, lint, typecheck and build commands.
