# Contributing

Use the setup and checks in README.md. Keep changes focused and add regression tests for altered scan, storage migration, request validation, or correlation behavior.

Never run tests against public or third-party targets. Automated tests replace external scanner calls with controlled fixtures. Scanner adapters should return execution status, findings, and observations separately.

Before proposing a change:

- Run the backend test suite and frontend tests, lint, type check, and build.
- Keep one canonical tool ID: `nmap`, `zap`, `sqlmap`, or `nikto`.
- Preserve the source evidence and affected location when grouping findings.
- Keep generated results, local databases (including legacy account archives), and secrets out of commits.
- Document API/configuration changes and verify English and Arabic layouts.

Dependency updates must include the matching npm lockfile and pass the same checks. Do not add unsupported tools to the UI.
