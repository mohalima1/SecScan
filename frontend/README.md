# SecScan frontend

React, TypeScript, Vite, and Tailwind CSS.

See the [root README](../README.md) for backend setup, scanner prerequisites, scope, and limitations.

```bash
npm ci
npm run dev
```

Open http://127.0.0.1:8080. The development server proxies `/api` to http://127.0.0.1:5000.
The scanner opens directly, without registration or login. On Windows PowerShell use `npm.cmd` in place of `npm`.

Checks: `npm test`, `npm run lint`, `npm run typecheck`, `npm run build`.

For a built deployment, configure a same-origin reverse proxy for `/api`; Vite's development proxy is not included in the static build. `VITE_API_BASE_URL` is a build-time value and must not contain secrets.
