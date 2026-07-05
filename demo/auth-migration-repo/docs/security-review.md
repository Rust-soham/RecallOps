# Authentication security review

Status: approved

Browser authentication uses an HTTP-only, Secure, SameSite cookie. Client code
must never persist access or refresh tokens in `localStorage`.

Logout must clear the browser cookie and revoke the server-side refresh
session. This decision supersedes `docs/legacy-auth.md`.

