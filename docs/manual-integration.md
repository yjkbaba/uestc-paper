# Manual integration: one authorized article

## Preparation

1. Use a private local checkout with Python 3.10+. Follow README installation steps.
2. Run `uestc-paper --help`, `uestc-paper setup`, and `uestc-paper status`.
3. If runtime is missing, run `python -m playwright install chromium`. `READY` only
   indicates runtime files exist; the next step tests actual launch.
4. Confirm `git check-ignore runtime/browser-profile/Default/Preferences downloads/test.pdf`
   lists both paths. Never add ignored files with `git add -f`.

## Visible login and persistence

1. Run `uestc-paper login`. Confirm a visible Chromium/Chrome/Edge opens the official
   `https://vpn.uestc.edu.cn` entry in a separate persistent profile.
2. The authorized user completes login manually. Passwords, OTPs and CAPTCHA answers
   must only be entered into the official visible browser UI.
3. Press Enter in the terminal. Expect `LOGIN_STATE_UNKNOWN` and exit code 2, even
   after successful manual authentication. Do not treat this as proof of failure
   or success; this command reports local state rather than live entitlement.
4. Run `uestc-paper status`: expect `Browser profile: FOUND`; session may be
   `UNKNOWN` or `MISSING`. Reopen `login` and manually check whether the site retains
   the session. Never export cookies or capture authentication screenshots.

## OA retrieval

1. Choose one known lawful OA article indexed by Europe PMC, and run
   `uestc-paper get <DOI> --no-browser`.
2. Expected success sequence: `DOI_NORMALIZED`, metadata status, `OA_FOUND`,
   `OA_DOWNLOAD`, `PDF_VERIFIED`, `SAVED (OA / Europe PMC)`.
3. Open the saved PDF yourself. Check article title, DOI and apparent completeness.
4. `OA_NOT_FOUND` is a supported outcome outside source coverage. `OA_LOOKUP_FAILED`
   is a service/network error; do not interpret it as no OA.
5. On OA 403/429/timeouts, expect `OA_TEMPORARILY_UNAVAILABLE`, never success or
   `OA_NOT_FOUND`. A failed OA source is not retried; normal visible institutional
   access may follow. Do not change identities or routes to evade controls. Stop
   automated actions at publisher anti-bot challenges; record only safe status codes.
6. A rejected or identity-unconfirmed PDF must not appear in `downloads/` as success.

## IEEE institutional path (Windows)

Only run when a new real integration is explicitly authorized; release smoke does
not require a real download. Use one entitled DOI and the same dedicated profile.

1. Run get with --wait-seconds 600: OA first, then direct IEEE.
2. If direct does not verify, user authentication occurs visibly in WebVPN.
   Portal detection continues automatically; no terminal confirmation/direct retry.
3. Official IEEE/IEL resource → main DOI search → exact target result PDF → Viewer.
4. Viewer Download once → new native Save As → UIA temporary-path read-back → Save
   once → completed file. Do not manually click PDF/Download/Save in this test.
5. Only verifier success, DOI MATCH and final exclusive save permit E2E_SUCCESS.
6. Record safe DOI, route, sizes, pages, verifier and outcome only. Never capture
   credentials, cookies, signed proxy URLs or authentication screenshots for Git.

The 2026-09-06 real success is in validation.md; this is separate from mock tests.
This document does not authorize new live downloads during release preparation.

## Safe phase evidence for the first IEEE test

- `DOI_NORMALIZED`: equivalent to resolved DOI input; metadata status follows.
- `OA_NOT_FOUND`, `OA_TEMPORARILY_UNAVAILABLE`, `OA_DOWNLOAD_FAILED`, or
  `OA_VERIFICATION_FAILED`: distinguish absence, service failure, bad transfer and bad file.
- `INSTITUTION_SESSION_UNKNOWN` / `INSTITUTION_SESSION_MISSING`: local evidence only.
- `USER_AUTH_REQUIRED`: authentication, if needed, is performed only by the user.
- `IEEE_DIRECT_OPENED`: normal IEEE domain reached; PDF identity remains unverified.
  `IEEE_ARTICLE_NOT_CONFIRMED` means navigation did not establish that state.
- `IEEE_DIRECT_DOWNLOAD_ATTEMPT`: the normal PDF action is clicked automatically.
- `OPENING_UESTC_WEBVPN` / `WAITING_FOR_USER_AUTH`: only this phase permits long waiting.
- `UESTC_IEEE_ENTRY_FOUND` / `IEEE_VIA_WEBVPN`: resource entry and proxied publisher UI detected.
- `UESTC_WEBVPN_PORTAL_READY`: a known resource-portal marker detected on the official host.
- `UESTC_LIBRARY_DATABASES_OPENED`, `UESTC_IEEE_RESOURCE_FOUND`,
  `UESTC_IEEE_RESOURCE_OPENED`: official database route selected automatically.
- `UESTC_DOMAIN_FALLBACK`: official resource selection did not establish a route;
  the portal's own HTTPS domain widget was used, not a direct external navigation.
- `IEEE_VIA_UESTC_OPENED`: a page created through this portal flow retains a UESTC
  WebVPN host and IEEE application structure. Host only is logged; no URL queries.
- `IEEE_DOWNLOAD_STARTED`: first browser download event received.
- `PDF_DOWNLOADED`: local browser download has PDF magic; parsing still required.
- `PDF_VERIFIED`: parser, page count and DOI/title identity checks passed.
- `SAVED` and `SUCCESS`: verified file written to the local download directory.

Never log download URLs, redirect queries, headers, cookie values, browser storage
or authentication form content. Playwright DEBUG/PWDEBUG modes are blocked during
browser operation. Parser diagnostic text is suppressed; structured verifier
status, file size and page count are retained. Do not enable traces, HARs or screenshots.

## Historical development diagnostics (not the production RC path)

Retained for development history and shared-code stability. These entry points
are not release smoke commands and require explicit authorization for any live run.

### Local institutional-only diagnostic

To retest a previously identified single IEEE article without repeating OA/direct
access, explicitly invoke the local diagnostic module:

```powershell
.venv\Scripts\python -u -m uestc_paper.integration 10.1109/LED.2024.3497584 --article-number 10752539 --wait-seconds 600
```

The article number is supplied from the prior observed IEEE page, not embedded in
the resolver. This diagnostic reuses the local visible persistent profile but does
not assume server-side authentication survived a restart. It prioritizes an existing
authenticated `webvpn.uestc.edu.cn` portal over legacy candidates, otherwise waits
for user authentication without terminal confirmation. It uses the official resource
flow and unchanged article/PDF diagnostics and verifier. Default `uestc-paper get`
remains OA-first. Verified files are initially saved in the configured downloads folder.

The institutional diagnostic installs Chromium CDP Network observation before the
PDF click. It observes official proxy PDF responses (200 or 206), waits
for loadingFinished and reads each distinct candidate body without replaying its URL.
Small/non-PDF complete bodies are rejected while the observation window continues.
Partial ranges are logged numerically and left unassembled; only a complete body
with plausible size and PDF magic may proceed to the unchanged verifier. A
loadingFailed event records fixed safe error categories. For ABORTED, Browser
download events are correlated with the same observed response URL: a five-second
grace period distinguishes handoff from absence of a download event. Browser-managed
files go to a unique ignored `runtime/download-capture/` subdirectory using GUID
filenames; they are retained through verification. There is no
authenticated request replay or observed-resource navigation fallback. The single
PDF diagnostic window is bounded to 90 seconds; a restart is not an automatic retry.
Only the existing verifier can authorize saving the captured bytes as a final PDF.

After one official IEEE resource click, a separate 25-second observation window
scans all current pages and child frames for the existing IEEE application markers.
It tolerates transitional navigation/frame errors and never repeats that resource
click or opens a second domain route during this window. Diagnostics use only
page counts/indices, hosts, fixed categories and structural counts.

### Manual PDF click checkpoint

Run `.venv\Scripts\python -u -m uestc_paper.manual_checkpoint` for the current
single-paper ground truth. Search stops at the exact target result rather than
opening its article. A unique arnumber-matching PDF link within that result is
outlined in green. MANUAL_PDF_GROUND_TRUTH_READY means observers are installed and
the user may click that red PDF icon once. No programmatic PDF click occurs.
The event loop stays active and the browser remains open until the user closes it.
PDF viewer structure alone is not proof that all article pages rendered; manual
confirmation or verified article bytes is needed for the success conclusion.
# Local automatic-click comparison

After closing the previous diagnostic browser, run
`.venv\Scripts\python -u -m uestc_paper.auto_click_diagnostic`.
This single-DOI diagnostic reuses the manual checkpoint's exact result-container
PDF locator. It logs allowlisted control categories, performs a trial click and
read-only center hit test, then dispatches one normal locator click. It does not
retry, replay PDF URLs, or save final PDFs. Frozen retrieval components are reused.
The passive observation window is 90 seconds; the browser stays open afterward.
`IEEE_PDF_VIEWER_OPENED` records viewer structure only. Confirm complete paper
rendering in that window before recording `AUTO_LOCATOR_CLICK_SUCCESS`.
A failed locator experiment must not be followed by a second PDF click in that run.
