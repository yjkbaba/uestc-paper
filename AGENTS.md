# AGENTS.md

## Project mission

`uestc-paper` is a focused academic-paper retrieval tool and Agent Skill for authorized users of the University of Electronic Science and Technology of China (UESTC).

The project should help a user retrieve an individual paper they are entitled to access, while preferring lawful Open Access copies and preserving user control over institutional authentication.

## Core rules

1. Open Access first.
2. Institutional authentication must happen in a visible browser controlled by the user.
3. Never request, read, store, log, transmit, or autofill UESTC passwords, OTPs, recovery codes, or CAPTCHA answers.
4. Local persistent browser profiles/session state may be reused, but must remain local and must never be committed to Git.
5. Do not implement bypasses for publisher security controls, CAPTCHA, paywalls, access controls, rate limits, or anti-bot protections.
6. Do not implement systematic or bulk downloading of subscribed library resources.
7. V0.1 should focus on explicit single-paper requests.
8. A successful HTTP response is not sufficient proof of a successful paper download. Validate the resulting file.
9. Keep publisher-specific logic behind adapter interfaces.
10. Prefer small, testable increments over broad automation.

## Institutional access order

For a requested paper:

1. Resolve DOI/title/URL and metadata.
2. Search lawful Open Access sources.
3. If OA is unavailable, try publisher institutional access / CARSI where appropriate.
4. Use the official UESTC WebVPN route as a fallback when applicable.
5. If authentication is required, launch a visible browser and let the user complete authentication manually.
6. Reuse the authenticated local browser profile for the requested retrieval.
7. Verify the final PDF before reporting success.

## Browser requirements

- Use visible browser automation for authentication flows.
- Prefer Playwright persistent context for V0.1.
- Do not store credentials in configuration files.
- Do not log cookies or authorization headers.
- Keep runtime browser data under ignored local directories.

## PDF verification

At minimum, verification should consider:

- PDF magic bytes (`%PDF`)
- plausible file size
- parseable PDF structure/page count
- title/DOI match when feasible
- rejection of login pages, HTML error pages, and obvious previews

## Repository hygiene

Never commit:

- browser profiles
- cookies
- session files
- downloaded subscription PDFs
- `.env` files
- local credentials or tokens
- captured authentication screenshots containing personal information

## Development scope

### V0.1

- Skill definition
- CLI skeleton
- DOI/title/URL resolver
- Open Access resolver
- visible persistent browser
- UESTC access/session detection
- PDF verifier
- one end-to-end publisher prototype, preferably IEEE Xplore
- tests

### Not in V0.1

- MCP server
- batch subscription downloading
- headless institutional login
- CAPTCHA automation
- credential storage
- remote session synchronization

## Reference project

The project may learn architectural ideas from `Rimagination/instsci`. Before copying any source code, review its license and preserve required attribution. Do not copy unrelated multi-institution logic merely for completeness.
