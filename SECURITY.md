# Security and authorized use

SecScan runs active security scanners. Only assess authorized systems inside an isolated environment. The initial-target allowlist is not a firewall or DNS/redirect sandbox.

The current deployment model is one local backend process and one dedicated ZAP daemon. ZAP sessions are reset for every job. The app is not designed as a publicly accessible scanning service.

There are no accounts or login. Every local client has access to the same scans and reports. Bind the backend and frontend to loopback; do not expose them on a shared network or public host. Browser origins and HTTP Host values are checked, and mutations require JSON. These checks do not authenticate local processes.

SQLite data belongs in the ignored backend/instance directory. Migration retains legacy account and scan tables as local archives; they can contain old password hashes and target evidence and must not be published.

Treat scanner evidence, database contents, logs, and downloaded reports as potentially sensitive. Do not publish real target information or credentials. Do not commit .env files or ZAP API keys.

If you find a vulnerability, avoid publishing exploit details or account/target data in a public issue. Once this project is on GitHub, use private vulnerability reporting if the owner enables it; otherwise contact the maintainer privately.

Before deployment or release, run dependency vulnerability checks and address applicable advisories. A passing test suite is not a security certification.
