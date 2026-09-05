---
name: uestc-paper
description: >
  Retrieve individual academic papers for authorized users of the University
  of Electronic Science and Technology of China (UESTC). Prefer lawful Open
  Access copies first, then use user-controlled institutional access such as
  publisher institutional login/CARSI or the official UESTC WebVPN. Use for
  DOI, title, or publisher-URL paper retrieval requests. Never request or store
  institutional credentials and never perform systematic bulk downloading of
  subscribed resources.
---

# UESTC Paper

Use this skill when an authorized UESTC user asks to find or download an academic paper by DOI, title, citation, or publisher URL.

## Primary objective

Retrieve the requested individual article PDF through the least privileged lawful route available, while keeping institutional authentication under the user's direct control.

## Access priority

1. Open Access
2. Publisher institutional login / CARSI
3. UESTC WebVPN
4. Report unavailable or manual action required

Read `references/uestc-access.md` for institution-specific access rules.
Read `references/compliance.md` before implementing or invoking subscribed-resource retrieval.

## Authentication rules

Institutional authentication must be completed manually by the user in a visible browser.

Never request, read, store, log, transmit, or autofill:

- UESTC username/password pairs
- passwords
- OTP or 2FA codes
- CAPTCHA answers
- recovery codes

A local persistent browser profile/session may be reused after the user has authenticated it manually.

Do not upload browser profiles, cookies, session storage, or authorization headers to GitHub or remote services.

## Retrieval workflow

When given a DOI, title, citation, or publisher URL:

1. Normalize the identifier.
2. Resolve DOI and bibliographic metadata when possible.
3. Search lawful Open Access locations first.
4. If a valid OA full-text PDF is available, retrieve and verify it.
5. If OA is unavailable, inspect whether a reusable local institutional browser session exists.
6. Prefer publisher institutional login/CARSI when supported.
7. Use the official UESTC WebVPN route as a fallback where applicable.
8. If authentication is required, open a visible browser and let the user complete UESTC authentication manually.
9. Continue only with the resulting authorized browser session.
10. Retrieve the explicitly requested article.
11. Verify that the downloaded file is the genuine full article PDF.
12. Save it locally and report the access route used.

## UESTC WebVPN constraint

Do not assume that visiting an arbitrary publisher URL after logging into WebVPN automatically grants proxied institutional access. Treat UESTC WebVPN as a resource-list-based web proxy and implement routing through the institution-provided resource entry points where required.

## Publisher adapters

Keep publisher-specific behavior behind adapters. V0.1 should prioritize:

- IEEE Xplore
- Elsevier / ScienceDirect
- SpringerLink
- AIP Publishing
- Wiley

Prefer one reliable end-to-end adapter over many incomplete adapters.

## PDF success criteria

Do not treat HTTP 200 as success by itself.

At minimum verify:

- file begins with `%PDF`
- file size is plausible for a full article
- PDF parses successfully
- page count is plausible
- title or DOI matches when feasible
- response is not HTML/login/error content
- obvious one-page previews are rejected when distinguishable

## Prohibited behavior

Do not:

- automate password entry
- solve or bypass CAPTCHA
- bypass paywalls or publisher security controls
- evade rate limits or anti-bot controls
- expose an institutional proxy to third parties
- perform systematic or bulk downloading of subscribed resources
- commit downloaded subscription PDFs, cookies, sessions, or browser profiles

## V0.1 behavior

Focus on user-requested single-paper retrieval.

Expected CLI direction:

```text
uestc-paper setup
uestc-paper login
uestc-paper get <identifier>
uestc-paper status
```

`login` should only prepare/open the visible browser flow and detect whether the resulting local session is usable. It must never collect institutional credentials.
