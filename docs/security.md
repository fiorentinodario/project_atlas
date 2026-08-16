# Security review

## Trust boundaries

- The browser is untrusted; authorization is repeated on every project-owned API resource.
- Uploaded files and extracted document text are untrusted input.
- Retrieved document content is data, never an instruction for the LLM.
- LLM responses are untrusted until their structured shape and source references are validated.
- Secrets enter only through environment variables and are excluded from Git and container contexts.

## Implemented controls

- Password hashing uses scrypt; raw passwords and refresh tokens are never stored.
- Access JWTs are short-lived. Refresh cookies are `HttpOnly`, `SameSite=Lax`, CSRF-protected and rotated.
- Production requires non-default application and JWT secrets and secure cookies.
- Project membership and role checks protect projects, tasks, documents, decisions, analyses and dashboard data.
- Unauthorized project identifiers return `404` to reduce resource enumeration.
- Uploads are size-limited, extension/MIME checked, filename-sanitized and stored under generated paths.
- AI source identifiers are resolved against retrieved chunks instead of trusting generated metadata.
- Suggested decisions require confirmation; suggested tasks require explicit selection.
- Security headers disable MIME sniffing, framing and sensitive browser capabilities.
- Database constraints prevent duplicate membership and duplicate AI-suggestion conversion.
- CI executes deterministic tests with fake AI providers and no production credentials.

## Residual risks and next controls

- Add distributed rate limiting before public deployment, particularly for auth and paid AI endpoints.
- Add malware scanning and asynchronous document isolation for untrusted public uploads.
- Add CSP at the serving edge after inventorying deployment-specific origins.
- Add centralized audit retention, alerting and secret rotation procedures for a production organization.
- Run dependency and container vulnerability scanning in the deployment environment.
