---
name: uestc-paper
description: Retrieve one paper by DOI for an authorized UESTC user. Prefer lawful OA then visible user-authenticated IEEE/IEL access. Windows institutional E2E validated. Never collect authentication secrets or bulk-download subscribed resources.
---

# UESTC Paper

## Core Rule

Use this Skill as the entry point for authorized UESTC single-paper retrieval.
For institutional IEEE retrieval, follow this Skill's established workflow instead
of constructing publisher proxy URLs, repeating clicks, automating authentication,
or bypassing access controls.

## Scope and CLI

RC1 accepts one DOI: raw DOI, doi: prefix, or https://doi.org/ URL. Title and
publisher-URL inputs are not implemented. IEEE/IEL is the only institutional adapter.
Read references/uestc-access.md and references/compliance.md before subscribed retrieval.

```text
uestc-paper --help
uestc-paper setup
uestc-paper login
uestc-paper status
uestc-paper get <DOI> [--wait-seconds 600] [--no-browser]
```

Use a consistent private local root, UESTC_PAPER_HOME, or global --home PATH.
UESTC_PAPER_OUTPUT selects verified output (default downloads/). Profile stays in
runtime/browser-profile/; temporary downloads stay in ignored runtime/ directories.
Setup reports browser availability but does not install binaries. See README.

## Retrieval

1. Normalize DOI and resolve metadata.
2. Search lawful OA locations through Europe PMC (limited coverage).
3. Download and verify OA before saving. Temporary OA failure may fall back to
   legitimate institutional access, without retrying to evade controls.
4. Try direct IEEE opportunistically; invalid candidates are discarded. Do not
   replay the URL or retry direct. A failed direct route permits WebVPN fallback.
5. Open/reuse official UESTC WebVPN visibly in the dedicated profile. The user
   personally completes authentication and required SSO. During get, portal
   detection continues without terminal confirmation.
6. Automatically select official IEEE/IEL resource. Do not assume an ordinary
   publisher URL becomes proxied merely because WebVPN login was completed.
7. Search DOI, match target article identity, click its unique result-card PDF,
   wait passively for Viewer. Article-detail fallback is only for absent reliable
   target-card PDF control. Do not choose arbitrary PDF controls elsewhere.
8. Select the unique main-toolbar Download, excluding Google Drive. On Windows,
   UIA may operate only the newly detected Chrome/Edge Save As: unique temporary
   PDF path, exact read-back, one Save. No repeated Download/Save or URL replay.
9. Accept a completed file, never .crdownload. Run existing magic/size/parse/page/
   error-preview/identity verification. Native Viewer retrieval requires DOI MATCH.
10. Save only through the exclusive final-output gate after verification. Report
    the actual local file and access route. E2E_SUCCESS requires verified final save.

## Required Output

Every retrieval attempt must end with a report containing the DOI, metadata title,
access route, final state, verification result, identity result, page count when
available, final file path on success, and the next action when unsuccessful.

Successful report example (the path is illustrative only):

```text
DOI: 10.xxxx/xxxx
Title: Example paper title
Route: UESTC WebVPN → IEEE/IEL
Result: E2E_SUCCESS
Verification: PDF_VERIFIED
Identity: DOI MATCH
Pages: 4
Saved to: <user-selected-output-directory>\example.pdf
```

Unsuccessful report example:

```text
DOI: 10.xxxx/xxxx
Title: Example paper title
Route: UESTC WebVPN → IEEE/IEL
Result: IEEE_PDF_VIEWER_TIMEOUT
Verification: NOT_REACHED
Identity: NOT_REACHED
Next action: retry in a fresh visible session
```

## Final Checks

Before reporting `E2E_SUCCESS`, confirm that the completed file exists, is not a
`.crdownload`, has valid PDF magic bytes, parses successfully, contains more than
zero pages, matches the requested DOI, and passed the final-save gate. If any check
fails, do not report `E2E_SUCCESS`. Viewer visibility or a download event is not
success when the final file does not exist.

## Authentication boundary and safety

Never request, read, store, log, transmit or autofill passwords, username/password
pairs, OTPs, CAPTCHA answers, recovery codes or other authentication secrets.
User authentication remains manual in the visible browser. UIA may not operate
authentication controls or unrelated Windows windows. Never inspect a password
manager or export cookie/storage values. Local session reuse is allowed only locally.

No paywall/security/anti-bot/CAPTCHA bypass, batch retrieval, crawler, systematic
subscription harvesting, remote proxy or session synchronization. Never commit
subscription PDFs, profiles, cookies, HARs, sensitive logs or authentication screenshots.

## Failure reporting

Never report success from HTTP 200, Viewer rendering or download event alone.
Report the actual stage: OA_NOT_FOUND, OA_TEMPORARILY_UNAVAILABLE,
INSTITUTION_AUTH_REQUIRED, IEEE_SEARCH_OBSERVATION_INCONCLUSIVE,
IEEE_PDF_VIEWER_TIMEOUT, IEEE_PDF_VIEWER_NOT_READY, NATIVE_SAVE_AS_...,
PDF_VERIFICATION_FAILED or RETRIEVAL_UNVERIFIED. Do not automatically repeat clicks.

Status MISSING/UNKNOWN describes local file presence, not entitlement. Login asks
for terminal Enter to close and returns LOGIN_STATE_UNKNOWN; get instead detects
portal readiness automatically. Unknown is not proof of authentication failure.

## Real evidence and platform limits

One Windows production E2E is verified for 10.1109/LED.2024.3497584:
17,065,057 bytes, 4 pages, PDF_VERIFIED, DOI MATCH. This does not establish all
papers/sessions. Native Save As uses Windows UIA; non-Windows fallback reports
NATIVE_SAVE_AS_UNSUPPORTED. Other institutional publishers are not implemented or
verified. Public OA retrieval is separate from this Windows-only limitation.
