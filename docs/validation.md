## V0.1 RC1 current status

- REAL_IEEE_E2E = PASS
- DOI = 10.1109/LED.2024.3497584
- PDF: 17,065,057 bytes; 4 pages; PDF_VERIFIED; DOI MATCH
- Automation: Search once; result PDF once; Viewer Download once; native Save once
- Successful baseline checks: 184 tests PASS; Ruff PASS; build PASS
- Platform: Windows, visible dedicated Chromium, official UESTC IEEE/IEL access
- RC freeze evidence: [release-v0.1.0-rc1-baseline.md](release-v0.1.0-rc1-baseline.md)

Earlier failed diagnostics remain preserved below as development history.
No new real paper download is run for release QA.

---

# V0.1 validation record

Environment: Windows, Python 3.13.9. Direct dependency versions used locally:
Playwright 1.62.0, pypdf 6.17.0; pytest 8.4.2, Ruff 0.12.0.

- Each implementation phase ran the accumulated pytest suite, Ruff and Python
  compile/import checks. Final suite: **53 passed**; Ruff and compile/import checks
  passed. A distributable wheel built successfully.
- Installed editable package successfully; `pip check` found no broken requirements.
- Actual installed CLI `--help`, `setup`, and `status` ran successfully.
- Actual `login` launched a visible persistent browser and reached the official
  UESTC entry. The smoke test immediately submitted an empty Enter to finish without
  authenticating. Result: `LOGIN_STATE_UNKNOWN`. A later `status` reported runtime
  `READY`, profile `FOUND`, session `UNKNOWN`. This is not a login-success claim.
- Public-network single-DOI tests for `10.1371/journal.pone.0000308` and
  `10.7554/eLife.45374` both reached `METADATA_FOUND` and `OA_FOUND`. Both PDF
  requests received HTTP 429. No automatic retries were performed and no PDF was
  reported as saved. Live OA download/verification success remains unverified.
- Offline synthetic tests exercise the full DOI → OA → verification → save flow,
  plus failure paths. They do not substitute for external-service verification.
- Real UESTC authentication, session expiry detection, CARSI availability, WebVPN
  resource navigation and UESTC → IEEE full retrieval have **not** been validated.

No credentials, exported cookies or subscription PDFs are part of the test suite.
Browser runtime files remain local and ignored. No hosted proxy, batch mode,
credential collection or access-control workaround was implemented.

## First authenticated IEEE test preparation — 2026-09-05

- Baseline rerun: 53 tests passed, Ruff passed, wheel build passed.
- Preparation changes: distinguish OA temporary unavailability from absence; allow
  normal visible institutional fallback without retrying the failed OA source;
  protect existing output with exclusive creation; add safe phase states; block
  protocol debug logging and suppress raw parser diagnostics.
- After changes: 68 tests passed, Ruff passed, wheel build passed. Tests cover OA
  lookup/download 403, 429, timeout and network failure, temporary file cleanup,
  existing-file preservation, safe errors and user-controlled IEEE fallback.
- Actual setup/status completed. Runtime READY, profile FOUND, institution session
  UNKNOWN. Actual visible persistent login opened the official UESTC entry; the user
  reported completing authentication. Login then closed normally and returned
  LOGIN_STATE_UNKNOWN. Subsequent status: READY / FOUND / UNKNOWN. File presence is
  not proof of access. No authentication fields were automated or read.
- Requested final output directory: `D:\文件`; only a verified result may be delivered.
- Test IEEE DOI: `10.1109/LED.2024.3497584`. No authenticated
  IEEE retrieval or E2E SUCCESS is asserted by this preparation record.

## IEEE automatic download / WebVPN UX revision — 2026-09-05

- Scope: IEEE normal PDF action and UESTC resource-entry fallback only; no new publisher.
- Automated suite: 72 tests passed; Ruff and wheel build passed. A late-download
  route attribution fix ensures direct downloads are not mislabeled as WebVPN.
- Browser: visible persistent Chromium/Chrome, headless disabled. PDF-viewer preference
  makes ordinary PDF responses download locally; no private download endpoint is used.
- DOI: `10.1109/LED.2024.3497584`.
- Actual sequence: METADATA_FOUND → OA_NOT_FOUND → INSTITUTION_SESSION_UNKNOWN →
  IEEE_DIRECT_OPENED → IEEE_DIRECT_DOWNLOAD_ATTEMPT → IEEE_DOWNLOAD_NOT_RECEIVED →
  INSTITUTION_AUTH_REQUIRED → OPENING_UESTC_WEBVPN → WAITING_FOR_USER_AUTH.
- Evidence: the normal IEEE PDF control was clicked automatically. No browser download
  event arrived within the short direct window, and the official WebVPN opened
  automatically in the same context. This does not prove absence of a subscription.
- Resource selection / proxied IEEE search / final download remain unverified in the
  real environment. The program waits for user authentication or one resource-entry
  selection if automatic resource recognition fails. PDF clicking is automatic.
- Overall: not E2E SUCCESS; no verified paper has been delivered to `D:\文件` yet.

## Automatic Library / IEEE / IEL resource selection — 2026-09-05

- Added portal detection from known resource labels and the domain-access widget;
  cookie contents and authentication fields are never inspected.
- Priority: official foreign-library database category and IEEE/IEL entry, then
  the portal's HTTPS domain-access widget. No externally constructed proxy URL.
- Automated validation: 80 tests passed, Ruff passed, wheel build passed. Tests
  cover IEEE/IEL naming, category click, official-route priority, domain fallback,
  explicit failures and absence of credential-field inspection.
- Real test for `10.1109/LED.2024.3497584` restarted. Metadata found; OA not found;
  normal direct PDF action clicked, no download event received in the short window;
  WebVPN opened automatically and reached WAITING_FOR_USER_AUTH.
- At this checkpoint the expected authenticated resource-portal markers have not
  appeared. Automatic portal → IEEE → target PDF is not yet verified in the real
  environment. No PDF or E2E SUCCESS is claimed.
- User feedback confirmed the visible page contained “校内常用资源”. The detector had
  required multiple simultaneous portal labels, which prevented the Library click.
  The minimal fix accepts a known resource marker on the official host, supports a
  short “图书馆” label, focuses the new portal tab, and checks embedded frames.
- After this fix: 83 tests passed, Ruff passed, wheel build passed. The same DOI
  test was restarted and is awaiting authenticated portal detection. This record
  does not claim that the Library/IEEE route or PDF delivery has succeeded yet.

## Post-authentication direct retry priority — 2026-09-05

- No publisher or portal selectors added. After automatic resource-portal detection,
  the original persistent context opens the same DOI and retries normal direct PDF
  access before any Library action. No terminal authentication confirmation is used.
- A retry download must pass the PDF verifier before this shortcut succeeds. A failed
  download or verifier continues to the existing library/resource/domain flow.
  A direct result after portal authentication is labeled as direct, not as proxied.
- Automated validation: 86 tests passed, Ruff passed, wheel build passed. New tests
  prove retry success avoids Library, retry failure reaches Library, invalid PDFs
  cannot trigger the shortcut, and all pages belong to the original context.
- The same real DOI test has been restarted; final PDF outcome remains pending.

## Correct WebVPN page selection — 2026-09-05

- User-observed browser evidence identified the authenticated portal at
  `webvpn.uestc.edu.cn`, not the legacy `vpn.uestc.edu.cn` hostname. The old detector
  rejected that host and excluded pre-existing pages, so it missed the authenticated
  third tab and eventually returned UESTC_AUTH_OR_ENTRY_TIMEOUT. This is a detector
  failure, not evidence that the user failed to authenticate.
- Added a regression first for `[about:blank, IEEE PDF, webvpn portal]`; the old
  implementation opened an unnecessary fourth tab instead of using the third.
- Fixed: enumerate all current pages on every poll, recognize both official hosts,
  reuse an existing WebVPN tab, inspect its main frame before child frames, and require
  a resource marker rather than accepting host alone. Existing working tabs are not closed.
- Diagnostics print page indices, host only, candidate indices and fixed portal
  markers. Query strings, fragments, path tokens, cookies and headers are not logged.
- Validation: 90 tests passed, Ruff passed, wheel build passed. Tests cover a third-tab
  portal, a host without authenticated markers, main-frame priority and child-frame fallback.
- The old running process could not hot-load the source fix and reached its existing
  timeout. A fresh test using the same local profile has begun; no final PDF claimed.

### Actual result after page-selection fix

- DOI: `10.1109/LED.2024.3497584`; browser mode: visible persistent context.
- Observed host selection: PAGE[2] changed from `vpn.uestc.edu.cn` to
  `webvpn.uestc.edu.cn`; the detector selected PAGE[2] and matched “校内常用资源”.
- Actual phases: UESTC_WEBVPN_PORTAL_READY → IEEE_POST_AUTH_DIRECT_RETRY →
  IEEE_DIRECT_DOWNLOAD_ATTEMPT → IEEE_DOWNLOAD_NOT_RECEIVED →
  IEEE_POST_AUTH_DIRECT_FAILED → UESTC_IEEE_RESOURCE_FOUND →
  UESTC_IEEE_RESOURCE_OPENED → IEEE_VIA_UESTC_OPENED → IEEE_TARGET_NOT_FOUND.
- The official resource opened PAGE[4] on `webvpn.uestc.edu.cn`, with IEEE application
  structure recognized. Authentication detection, direct retry and official resource
  selection ran in the same context without terminal login confirmation or manual
  database/PDF clicks. No claim is made that a Library category click occurred; the
  resource itself was found in the official portal.
- First remaining failure: target article navigation/search within proxied IEEE.
  The current result does not distinguish a missing search control from a missing
  matching search result. It is not evidence of missing subscription entitlement.
- Verification result: not reached. Page count and file size: not applicable.
  Final PDF saved: none; `D:\文件` delivery not completed. Overall: E2E FAILED
  at IEEE_TARGET_NOT_FOUND. Page-selection regression is verified fixed.

## IEEE target identity/navigation fix — 2026-09-05

- Final automated validation: 98 tests passed, Ruff passed, wheel build passed.

- Scope: IEEE article identity and target navigation only. OA, authentication,
  portal detection and resource selection were not modified in this revision.
- Direct IEEE navigation automatically extracted arnumber **10752539** for DOI
  `10.1109/LED.2024.3497584`; this number was not hard-coded into the workflow.
- The proxied IEEE page (index 4, host `webvpn.uestc.edu.cn`, 4 frames) was inspected
  for existing article links and labeled search controls. A searchbox was detected.
- Actual sequence: IEEE_SEARCH_SUBMITTED (requested DOI) → IEEE_CANDIDATE_RESULTS
  (4 matching links, arnumber 10752539) → IEEE_TARGET_RESULT_FOUND →
  **IEEE_TARGET_ARTICLE_OPENED** → IEEE_WEBVPN_DOWNLOAD_ATTEMPT → IEEE_ACCESS_REQUIRED.
- No proxy URL was synthesized. The program selected a matching link from IEEE's
  own search results. No manual article search or PDF click was requested.
- Result: real proxied target-navigation Definition of Done met. The subsequent
  normal PDF click encountered a visible authentication/purchase/subscription heading
  recognized by the existing adapter; no download event was received before exit.
  This does not establish whether UESTC lacks a subscription.
- PDF verifier was not reached; page count/file size not applicable; no paper was
  delivered to `D:\文件`. Overall full retrieval remains unsuccessful.

## PDF navigation diagnostics — 2026-09-05

- Baseline: 98 tests passed. Updated checks: 105 tests passed, Ruff passed,
  wheel build passed (`pip wheel --no-deps --no-build-isolation`).
- Scope: normal IEEE PDF controls, popup/navigation evidence and outcome classification.
  DOI search, article-number resolution, OA, portal detection and routing are unchanged.
- Diagnostics retain page indices, host and fixed path/title categories only.
  Arbitrary titles are redacted. No query strings, raw proxy paths, credentials,
  storage, cookies or authorization headers are logged.
- Tests distinguish escaped direct-host popups/downloads, proxied purchase/sign-in
  pages, and stamp viewers. Observed proxy DOM/frame PDF links take priority;
  no WebVPN URL is constructed. A viewer state is not download success.
- Actual first retest of `10.1109/LED.2024.3497584`: direct article PAGE[1],
  host `ieeexplore.ieee.org`, path type ARTICLE. PDF control host was the same,
  path type STAMP. The click navigated the same page to STAMP; observed navigation
  response host was `ieeexplore.ieee.org`. No download event occurred.
- The subsequent WebVPN stage found a candidate at `vpn.uestc.edu.cn`, but did
  not detect an authenticated resource portal within 300 seconds and returned
  UESTC_AUTH_OR_ENTRY_TIMEOUT. This retest therefore did **not** reach the proxied
  article/PDF stage, and cannot prove proxy escape or genuine entitlement failure.
- A second visible run with live diagnostic output reached the same direct STAMP
  navigation, then also returned UESTC_AUTH_OR_ENTRY_TIMEOUT. Neither run reached
  the proxied article. The PDF-navigation Definition of Done remains unfulfilled.
- Final code additionally requires PDF embed/object or the recognized full-text
  viewer title before reporting IEEE_PDF_VIEWER_OPENED; a STAMP path alone yields
  IEEE_PDF_VIEWER_UNCONFIRMED. This refinement passed unit tests but has not been
  exercised in the authenticated real proxy environment.
- No verified PDF, page count, or file size is available; delivery to `D:\文件`
  remains incomplete. No full E2E success or subscription-entitlement conclusion.

## Authenticated portal reuse and institutional-only retest — 2026-09-06

- Baseline: 105 tests passed. Portal priority and local diagnostic entry checks:
  107 tests passed, Ruff passed, wheel build passed.
- Before opening any VPN URL, existing pages and their frames are checked for
  existing portal markers. An authenticated `webvpn.uestc.edu.cn` portal takes
  priority over legacy candidates. Host alone does not establish authentication.
  No portal selectors or PDF classification/algorithm were changed this revision.
- Added explicit local `python -m uestc_paper.integration` entry. The same DOI and
  previously observed arnumber 10752539 are supplied as arguments. It skips the
  default OA/direct diagnostic stages only for this explicit invocation; the
  production get workflow remains unchanged. Authentication stays manual and visible.
- The first diagnostic invocation stopped with a browser/runtime error after the
  host changed to `webvpn.uestc.edu.cn`; its precise cause was not captured. Fixed
  phase/error-category diagnostics were added without printing raw exceptions.
- The next actual run detected the existing marker “校内常用资源”, automatically
  opened the official IEEE resource, submitted the requested DOI, found four
  matching candidate links and reached **IEEE_TARGET_ARTICLE_OPENED**.
- Real PDF evidence for DOI `10.1109/LED.2024.3497584`:
  - Article page index: 2; host: `webvpn.uestc.edu.cn`; path category: ARTICLE;
    safe title category: IEEE Xplore.
  - PDF control host: `webvpn.uestc.edu.cn`; path category: STAMP.
  - Normal PDF click: same-page navigation; no popup or download event observed.
  - Resulting host: `webvpn.uestc.edu.cn`; final path category: STAMP.
  - Final navigation-response host: `webvpn.uestc.edu.cn`; path category: STAMP.
  - Existing classifier outcome: **IEEE_PDF_VIEWER_UNCONFIRMED**.
- Result: this revision's real target-open + PDF navigation-classification
  Definition of Done is met. No proxy escape was observed in this attempt.
  Viewer/full-text availability remains unconfirmed; this is not evidence of
  missing subscription entitlement. PDF bytes and verifier were not reached,
  no file was saved to `D:\文件`, and full retrieval E2E success is not claimed.

## STAMP response/body path — 2026-09-06

- Scope: IEEE PDF response observer, observed resource handling and existing verifier
  handoff only. OA, VPN, portal detection and article search/navigation are unchanged.
- Automated checks: 118 tests passed, Ruff passed, wheel build passed. Synthetic
  coverage includes HTML followed by PDF without a download event; iframe/embed/object
  attributes; valid/invalid bodies through the existing final-save verifier; exact
  observed-resource request/browser fallback; nonproxy/error responses and log redaction.
- Real institutional-only runs used DOI `10.1109/LED.2024.3497584`, arnumber 10752539.
  The authenticated official resource route reached IEEE_TARGET_ARTICLE_OPENED.
- Observed normal path: PAGE[2] on `webvpn.uestc.edu.cn`, STAMP response HTTP 200,
  HTML MIME category → IEEE_STAMP_OPENED → actual iframe attribute on the same host
  → HTTP 200 PDF MIME category response, Content-Disposition present, Content-Length
  unavailable → **IEEE_PDF_RESPONSE_OBSERVED**. The embedded resource path is retained
  only as category OTHER; no raw resource URLs or signed parameters are recorded.
- The browser response body was unavailable. One request per observed resource using
  the same context and exact already-visited proxy URL timed out (first 15 seconds,
  subsequent 30 seconds). No redirects or guessed/private endpoints were used.
- A subsequent normal visible browser navigation to that exact observed resource
  produced a PDF response on PAGE[3] at `webvpn.uestc.edu.cn` and a download event.
  However, Playwright download completion returned DOWNLOAD_FAILED. Its precise
  network failure reason was not captured during that run.
- Fixed safe download-error diagnostics were added. The final diagnostic retest
  instead returned **IEEE_PROXY_ACCESS_REQUIRED** after the normal PDF click;
  it did not reproduce the body/download failure. Further requests were stopped.
- No real IEEE_PDF_BYTES_CAPTURED or PDF_VERIFIED occurred. File size/page count are
  unavailable and no PDF was delivered to `D:\文件`. The observed PDF response path
  is established; complete valid PDF retrieval remains unresolved. No E2E SUCCESS.
- A PDF MIME response with an unreadable body now returns IEEE_PDF_BODY_UNAVAILABLE;
  IEEE_PDF_VIEWER_UNCONFIRMED is reserved for absence of PDF response evidence.

## First-response CDP capture — 2026-09-06

- Baseline: 118 tests passed. Final checks: 122 tests passed, Ruff passed, wheel
  build passed. Tests cover first-response locking, loadingFinished/body reading,
  base64 decoding, loadingFailed/redaction, and valid/invalid CDP bytes through
  the existing final-save verifier. Previous resource-replay tests were replaced
  with no-replay assertions because replay has been removed.
- Institutional-only diagnostics enable Chromium Network observation before the
  normal PDF click. Only the first HTTP 200/206 PDF response from exactly
  `webvpn.uestc.edu.cn` is selected. Request identifiers are transient and not logged.
  loadingFinished reads Network.getResponseBody once. No resource GET or navigation
  replay remains. OA, portal, search and target navigation are unchanged.
- Exactly one real invocation was performed for DOI `10.1109/LED.2024.3497584`,
  arnumber 10752539. It reached authenticated portal → official IEEE resource →
  target article → normal PDF click → proxied STAMP → observed iframe.
- First actual CDP PDF response: host `webvpn.uestc.edu.cn`, fixed path category
  OTHER, HTTP 200, PDF MIME category. State: IEEE_PDF_RESPONSE_OBSERVED.
- The matching request then emitted Network.loadingFailed:
  error category **ABORTED**, canceled **true**, blocked reason **NONE**,
  CORS error category **NONE**. Final outcome: **IEEE_CDP_LOADING_FAILED**.
- No loadingFinished/body capture occurred for that response. The run stopped
  immediately without replaying the resource or starting another real test.
  These events establish cancellation, not its underlying cause or entitlement.
- Real IEEE_PDF_BYTES_CAPTURED and PDF_VERIFIED were not reached. No page count,
  completed file size or delivered PDF exists for this run. `D:\文件` delivery and
  E2E success remain incomplete. This turn's bytes-capture Definition of Done is
  **not met**; the first actual network failure is now documented.

## Browser download-manager handoff diagnostic — 2026-09-06

- Confirmed persistent Chromium already explicitly sets accept_downloads=True;
  its existing PDF preference was not changed. OA, portal, search, article and
  STAMP/iframe navigation logic were not modified.
- Added Browser.downloadWillBegin/downloadProgress monitoring before PDF click,
  preferring a browser-level CDP session. Browser.setDownloadBehavior uses
  allowAndName, eventsEnabled and a unique ignored runtime/download-capture
  directory; unverified downloads never go directly to the user's final directory.
- The first PDF response URL is matched in memory with downloadWillBegin. After
  Network ABORTED, a matching event yields IEEE_PDF_DOWNLOAD_HANDOFF. No matching
  event within five seconds yields IEEE_PDF_ABORT_WITHOUT_DOWNLOAD. Download
  progress logs only fixed state and numeric sizes. Completed GUID-named files
  remain available while their bytes pass through the existing verifier.
- Baseline: 122 tests passed. Final validation: 127 tests passed, Ruff passed,
  wheel build passed. Tests exercise handoff, no handoff, canceled progress,
  completed files and invalid completed files rejected before final output.
- Exactly one institutional-only real invocation was performed for DOI
  10.1109/LED.2024.3497584, arnumber 10752539. Actual sequence:
  UESTC_WEBVPN_PORTAL_READY → UESTC_IEEE_RESOURCE_FOUND →
  UESTC_IEEE_RESOURCE_OPENED → UESTC_ENTRY_UNRECOGNIZED.
- The existing resource-entry stage did not confirm proxied IEEE in this run.
  Target article, PDF click and download-manager observation were not reached.
  No second invocation or PDF URL replay was attempted.
- Result: this run cannot classify the prior ABORTED as handoff or no handoff;
  neither requested real outcome was obtained. Definition of Done remains unmet.
  No verified PDF or final D:\文件 delivery; no E2E SUCCESS claimed.

## Official resource navigation race — 2026-09-06

- Scope: resource-click completion and subsequent application observation only.
  Existing IEEE markers, DOI search, article navigation, PDF/CDP/download-manager
  code and verifier were not changed.
- After one official resource click, poll all context pages and child frames for
  up to 25 seconds. Reuse xpl-root/IEEE Xplore image evidence. Transitional frame
  and navigation errors do not cause immediate failure. No second resource click
  or domain fallback is issued after the official resource was selected.
- Diagnostics contain page count/index, host, fixed structural title category,
  frame count, marker/search booleans and article-link count only.
- Exactly one real invocation used DOI 10.1109/LED.2024.3497584, arnumber 10752539.
  Actual sequence: UESTC_WEBVPN_PORTAL_READY → UESTC_IEEE_RESOURCE_FOUND →
  INTEGRATION_FAILED (phase UESTC_PORTAL, reason BROWSER_TIMEOUT).
- The resource click itself timed out before entering the new observation window.
  Dispatch/navigation completion was not established. This run did not reach
  IEEE_VIA_UESTC_OPENED or the target/PDF stage, so no handoff conclusion is possible.
- Minimal follow-up fix: catch the resource click's Playwright timeout, report
  UESTC_RESOURCE_CLICK_UNCONFIRMED and observe the context without clicking again.
  A regression demonstrates an already-dispatched click whose navigation wait
  times out can still lead to the existing proxied app marker.
- Final checks: 132 tests passed, Ruff passed, wheel build passed. Coverage also
  includes delayed same-tab/new-tab/frame bootstrap and navigation-race timeout.
  The follow-up fix has not been retested live: no second real run was started,
  honoring the single-run constraint. Neither real Definition of Done layer was
  achieved this turn. No verified PDF or D:\文件 delivery; no E2E SUCCESS.

## Dedicated profile PDF preference — 2026-09-06

- User reports full-paper viewing works in ordinary Chrome after changing its PDF
  preference. This is manual evidence, not verification of the automated profile.
- Confirmed the application startup code forced plugins.always_open_pdf_externally
  to true. The actual dedicated runtime/browser-profile/Default/Preferences also
  contained true. Changed startup to false and safely replaced only this preference
  in the closed dedicated profile. No profile deletion, cookie/password/token
  inspection or ordinary-Chrome profile modification was performed.
- accept_downloads=True is retained. Resource routing, selectors, CDP/download
  manager and verifier code were not modified.
- Validation: existing 132 tests passed, Ruff passed, wheel build passed.
- Exactly one institutional-only real test used DOI 10.1109/LED.2024.3497584,
  arnumber 10752539. It selected a webvpn.uestc.edu.cn candidate then exited with
  INTEGRATION_FAILED: phase=UESTC_PORTAL; reason=FRAME_DETACHED.
- The run never reached IEEE/PDF. IEEE_PDF_VIEWER_OPENED, response-body capture
  and verifier success were not observed. No second run or PDF replay was made.
- After browser exit, the dedicated profile preference was confirmed still false.
  The configuration correction is verified; the real Viewer Definition of Done
  remains unmet. No D:\文件 delivery or automated E2E success claimed.

## Transient portal frame lifecycle — 2026-09-06

- Scope: portal/resource detection only. Detached-frame exceptions emit
  FRAME_DETACHED_TRANSIENT and discard stale scopes; each poll enumerates current
  pages/frames. A detached resource click transitions to observation without
  another click. Scopes are refreshed after the optional long post-auth callback.
- Exactly two regressions were added: portal marker frame replacement, and a
  dispatched resource click detaching before a new frame exposes IEEE markers.
  Final checks before the real run: 134 tests passed, Ruff passed, wheel build passed.
- Exactly one real institutional-only run used the same dedicated profile and DOI
  10.1109/LED.2024.3497584, arnumber 10752539. Actual sequence:
  UESTC_WEBVPN_PORTAL_READY → UESTC_IEEE_RESOURCE_OPENED → IEEE_VIA_UESTC_OPENED →
  IEEE_TARGET_ARTICLE_OPENED → IEEE_STAMP_OPENED → IEEE_PDF_EMBED_FOUND →
  IEEE_PDF_RESPONSE_OBSERVED → IEEE_PDF_BYTES_CAPTURED → DOWNLOAD_RECEIVED.
- The proxied application was detected on PAGE[2], webvpn.uestc.edu.cn, after its
  frame count grew from 1 to 4. The PDF response was HTTP 200, PDF MIME category,
  on webvpn.uestc.edu.cn, fixed path category OTHER.
- The existing CDP loadingFinished/body path obtained 536 bytes. Existing verifier
  result: INVALID_PDF_MAGIC; pages=0; size=536; identity=UNKNOWN. The temporary
  unverified file was discarded by the existing workflow; no final PDF was saved.
- No real FRAME_DETACHED_TRANSIENT was emitted in this run, so recovery from that
  exception is covered by the focused mocks; the actual portal route succeeded.
- IEEE_PDF_VIEWER_OPENED was not observed. PDF MIME and captured bytes do not prove
  a rendered viewer or valid article. No ABORTED or browser download handoff was
  observed before the response-body result. No code was changed after the run and
  no second run/PDF URL replay occurred. D:\文件 delivery and E2E SUCCESS remain unmet.

## Passive multiple PDF candidates — 2026-09-06

- CDP candidate observation no longer locks on the first PDF MIME response. Each
  distinct request/resource-range candidate is processed once; complete bodies below
  512 bytes, above the existing maximum or lacking PDF magic are rejected without
  terminating passive observation. Existing verifier rules are unchanged.
- Candidate logs contain sequence, status, body size, numeric Content-Length,
  Content-Range/Disposition presence and fixed signature category. Numeric ranges
  are logged; partial 206 bodies are neither rejected for missing leading magic
  nor reconstructed. Existing embed/viewer evidence is checked during observation.
- Validation: 136 tests passed, Ruff passed, wheel build passed. Regressions prove
  a 536-byte JSON-like first candidate does not prevent a later full candidate and
  a middle 206 range is not incorrectly rejected for lacking initial PDF magic.
- Exactly one institutional-only real run used DOI 10.1109/LED.2024.3497584 and
  arnumber 10752539. It reached the authenticated portal, proxied IEEE, target
  article and one normal PDF click. The existing full 90-second observation window
  ended with IEEE_PROXY_ACCESS_REQUIRED.
- Actual PDF MIME candidates: **0**. The prior 536-byte candidate was not reproduced;
  no candidate #2/#3, IEEE_PDF_VIEWER_OPENED or 206 range pattern was observed.
  These are bounded observation results, not proof of permanent entitlement status.
- No additional click, URL replay or second run occurred. The invalid-first-candidate
  continuation is unit-verified but not yet reproduced against real multiple PDF
  responses. No verified file or D:\文件 delivery; no E2E SUCCESS.

## Exact search-result PDF pointer click — 2026-09-06

- Manual ground truth: the user confirmed complete paper rendering in the dedicated
  browser after clicking the exact target search result's PDF icon:
  MANUAL_PDF_VIEWER_SUCCESS.
- One subsequent automatic diagnostic used DOI 10.1109/LED.2024.3497584,
  arnumber 10752539, the same dedicated persistent profile, and the manual
  checkpoint's result-container locator. Frozen retrieval components were unchanged.
- Actual route: UESTC_WEBVPN_PORTAL_READY → UESTC_IEEE_RESOURCE_OPENED →
  IEEE_VIA_UESTC_OPENED → IEEE_TARGET_RESULT_FOUND → AUTO_LOCATOR_CLICK_DISPATCHED →
  IEEE_STAMP_OPENED → IEEE_PDF_VIEWER_OPENED → AUTO_OBSERVATION_COMPLETE.
- Target result sibling index: 0. PDF candidates: 1; visible candidates: 1;
  intended visible candidates: 1. Control tag: A; aria category: PDF;
  href path category: STAMP. Visible/enabled/bounding-box checks passed.
  Scroll, hover, trial actionability and center hit-test passed, followed by one
  normal locator.click(), without force, JavaScript click or coordinate retry.
- The resulting STAMP host was webvpn.uestc.edu.cn. The Chrome built-in PDF
  viewer frame appeared. After the 90-second passive observation window, the user
  explicitly confirmed that the complete paper content was displayed.
  Result: **AUTO_LOCATOR_CLICK_SUCCESS** (browser evidence plus user confirmation).
- This diagnostic differs from the earlier article-page/global-PDF flow by clicking
  the PDF inside the exact matching search result. It reproduces manual success;
  it does not isolate target selection versus timing as the sole historical cause.
  No mouse-coordinate A/B was needed or run; default retrieval was not rewritten.
- The existing observer rejected one HTTP 200 PDF-MIME body of 536 bytes as
  HTML_LIKE. No final PDF was saved or verified in this experiment. Viewer success
  does not establish byte-capture success, D:\文件 delivery, or full retrieval E2E SUCCESS.
- Checks before the real run: 140 tests passed, Ruff passed, wheel build passed.
  No second PDF click, URL replay, authentication-secret logging or frozen-module
  changes were performed in this experiment.

## Chromium viewer toolbar download — 2026-09-06

- One real run of viewer_download_diagnostic used the same DOI
  10.1109/LED.2024.3497584 and arnumber 10752539, dedicated visible profile,
  existing institutional route and exact search-result PDF locator.
- Actual sequence: UESTC_WEBVPN_PORTAL_READY → IEEE_VIA_UESTC_OPENED →
  IEEE_TARGET_RESULT_FOUND → AUTO_LOCATOR_CLICK_DISPATCHED →
  IEEE_PDF_VIEWER_OPENED → VIEWER_DOWNLOAD_CONTROL_FOUND →
  IEEE_BROWSER_DOWNLOAD_MONITOR_READY → IEEE_VIEWER_DOWNLOAD_DISPATCHED.
- On page index 2, the pdf-viewer initially exposed zero visible matching download
  buttons, then exposed exactly one enabled visible accessible button during the
  observation window. Normal Playwright shadow-piercing role lookup succeeded;
  the toolbar was not inaccessible. One normal toolbar click was performed.
- Playwright emitted DOWNLOAD_RECEIVED and Browser emitted downloadWillBegin.
  Browser progress observed: inProgress, receivedBytes=0, totalBytes=0.
  Playwright download.failure() returned a nonempty failure categorized by this
  diagnostic as DOWNLOAD_NETWORK_FAILED. No completed progress or completed PDF
  was obtained. The underlying cause is not established by that broad category;
  no raw failure string or sensitive URL was recorded. The run then stopped.
  Post-run inspection found an 8,126,464-byte .crdownload in this run's ignored
  temporary directory. It remains local and was not treated as a completed PDF.
- First unmet stage: download completion. The verifier and final-save branch were
  not reached; no new verified PDF was saved to D:\文件 and no E2E_SUCCESS is claimed.
  No second click, URL replay, keyboard/OS/coordinate fallback, preference change,
  or frozen retrieval-module change occurred.
- Automated validation before the real run: 144 tests passed, Ruff passed,
  wheel build passed. Synthetic completed-file tests cover existing-verifier
  acceptance and invalid-file rejection; these are not real-download evidence.

## Offline retained download forensics — 2026-09-06

- No browser/network flow, download click or URL replay was run. The retained
  8,126,464-byte .crdownload was copied without modification to ignored local
  runtime/forensics/candidate.pdf. SHA-256 comparisons confirmed an identical copy
  and unchanged original. No document text or raw head/tail bytes were logged.
- File size: 8,126,464 bytes. Starts with %PDF: true. Contains %%EOF in the final
  4,096 bytes: false. Existing verify_pdf, called with the requested DOI
  10.1109/LED.2024.3497584, returned valid=false, PDF_PARSE_ERROR, pages=0,
  identity=UNKNOWN. Its exception result reports size=0; that field is not the
  measured file size above.
- Classification: **TRUNCATED_PDF / CRDOWNLOAD_TRUNCATED_PDF**. Neither copy nor
  original was saved to D:\文件. Both remain local for diagnosis.
- Available prior Browser progress evidence: state=inProgress, receivedBytes=0,
  totalBytes=0, followed by the diagnostic failure result. No final byte counters
  or completed event were captured. Local size 8,126,464 does not equal the logged
  zero counters; totalBytes=0 does not establish the expected document size.
  These logs cannot prove finalization/rename failure or determine the exact
  interruption cause. The offline content checks independently reject completeness.

## Native-behavior manual download preparation — 2026-09-06

- Local Playwright source inspection showed that launch_persistent_context with
  accept_downloads=True itself sends Browser.setDownloadBehavior(allowAndName).
  Removing only the application's download manager would not eliminate that variable.
- The isolated manual_viewer_download diagnostic therefore launched visible Chrome
  with the same dedicated profile unchanged and attached over local CDP with the
  documented no_defaults=True option. No download behavior override, download
  manager, PDF body observer or automated Viewer download action was used.
- One real route reached the authenticated portal and proxied IEEE. The existing
  search submitted the DOI and then article number, but the diagnostic stopped
  before target-PDF dispatch or Viewer readiness. The precise browser exception
  cause was not recorded; no transport or entitlement conclusion follows.
- Read-only reattachment to the same still-running browser found no pdf-viewer
  and no visible matching target article links. No new route, search, PDF click
  or download was triggered by those inspections.
- Manual download ground truth remains untested: neither
  MANUAL_VIEWER_DOWNLOAD_COMPLETED nor MANUAL_VIEWER_DOWNLOAD_FAILED is justified.
  No file was obtained for verification in this run. Automatic/manual transfer
  comparison and the cause of the earlier truncated download remain unresolved.
- Checks: 144 tests passed, Ruff passed, wheel build passed. Production modules
  and frozen selectors/preferences were not changed.

## Native manual viewer download succeeded — 2026-09-06

- The user explicitly authorized one further manual-only run. The previous browser
  was unavailable, so the same dedicated profile was launched visibly in Chrome
  and connected with no_defaults=True. No custom Browser.setDownloadBehavior,
  download manager, automatic Viewer download, or PDF resource replay was used.
- The existing route reached UESTC_WEBVPN_PORTAL_READY → IEEE_VIA_UESTC_OPENED →
  IEEE_TARGET_RESULT_FOUND → AUTO_LOCATOR_CLICK_DISPATCHED. A pdf-viewer was
  observed. Toolbar matching changed from zero to two controls; the automated
  readiness helper returned MANUAL_VIEWER_NOT_READY and performed no toolbar click.
  The browser remained open for the manual test; this helper status is not a
  download-failure result.
- The user reported completing the manual download to
  D:\文件\Low_Contact_Resistivity_of_lt10_mm_for_Au-Free_Ohmic_Contact_on_p-GaN_AlGaN_GaN (1).pdf.
  A read-only offline check of that exact file found: size=17,065,064 bytes;
  starts_with_%PDF=true; %%EOF within final 4,096 bytes=true. Existing verify_pdf
  with DOI 10.1109/LED.2024.3497584 returned valid=true, PDF_VERIFIED, pages=4,
  identity=MATCH. The file was not altered or copied into Git.
- Result: **MANUAL_VIEWER_DOWNLOAD_COMPLETED**. A correct verified paper is present
  at the user's requested location. This is manual-download success, not proof of
  successful automated download completion.
- The successful native-behavior run demonstrates that the institution route,
  dedicated profile and Viewer can deliver the requested PDF. It supports focusing
  subsequent comparison on the automation download layer, but does not uniquely
  establish allowAndName as the cause of the previous truncated transfer; timing
  and transport conditions also differed between runs. No production download-layer
  changes or second automatic download test were made in this turn.

## Automatic viewer download with native behavior — 2026-09-06

- After the user closed the previous browser, one authorized auto_viewer_default
  run launched the same dedicated profile and attached with no_defaults=True.
  No Browser.setDownloadBehavior override or custom download manager was installed.
  Production accept_downloads=True remained unchanged; it was not used to attach
  this experiment because the installed Playwright would internally set allowAndName.
- The existing route reached UESTC_WEBVPN_PORTAL_READY → IEEE_VIA_UESTC_OPENED →
  IEEE_TARGET_RESULT_FOUND → AUTO_LOCATOR_CLICK_DISPATCHED. The frozen viewer
  locator observed pdf-viewer on page index 2; matching visible download controls
  changed from zero to two and remained ambiguous through the 90-second window.
- Final emitted statuses: PDF_VIEWER_DOWNLOAD_CONTROL_INACCESSIBLE and
  **AUTO_VIEWER_DOWNLOAD_DEFAULT_BEHAVIOR_FAILED**. In this case INACCESSIBLE
  describes failure to obtain one intended control, not a browser security denial.
  No IEEE_VIEWER_DOWNLOAD_DISPATCHED occurred, so no Viewer download event or
  temporary downloaded file was obtained. Verification/final saving were not reached.
- This is a pre-click locator-ambiguity failure, not evidence of failed native
  download transport or of custom-manager causality. No selector changes, extra
  clicks, URL replay, manual-download comparison or second run followed.
  The previously manually obtained verified PDF is unaffected.
- Checks before this run: 145 tests passed, Ruff passed, wheel build passed.

## Viewer download candidate disambiguation — 2026-09-06

- The previous browser was unavailable. One new native-behavior run used the
  existing institutional/search/PDF path and then paused in the Viewer. Subsequent
  inspections and the single download attempt reused that same browser, with
  no_defaults=True and no PDF navigation replay or download-manager override.
- Actual candidates on page index 0, frame index 2 (PDF_VIEWER): both were visible,
  enabled CR-ICON-BUTTON elements with role=button, empty visible text, and main
  VIEWER-TOOLBAR ancestry. Candidate 0 aria/title: Save to Google Drive, ancestor
  VIEWER-SAVE-TO-DRIVE-CONTROLS, box x=1551.3333740234375,y=12,width=32,height=32.
  Candidate 1 aria/title: Download, ancestor VIEWER-DOWNLOAD-CONTROLS,
  box x=1587.3333740234375,y=12,width=32,height=32. Neither was a menu candidate.
- The new selector excludes Drive controls, menus, hidden/disabled and non-main
  toolbar candidates, prefers exact Download names and standard title/ancestry,
  and rejects ties. It does not select by index, coordinates or DOM order.
  Actual result: VIEWER_DOWNLOAD_SELECTED candidate=1 → IEEE_PDF_VIEWER_OPENED →
  VIEWER_DOWNLOAD_CONTROL_FOUND. The two-to-one disambiguation DoD is satisfied.
- The existing normal pointer/download waiting path then returned
  DOWNLOAD_ACTION_OR_EVENT_TIMEOUT and AUTO_VIEWER_DOWNLOAD_DEFAULT_BEHAVIOR_FAILED.
  Neither IEEE_VIEWER_DOWNLOAD_DISPATCHED nor DOWNLOAD_RECEIVED was logged.
  The current generic timeout does not distinguish scroll/trial/actual-click
  failure; dispatch is unconfirmed. No second attempt followed, no final file was
  obtained, and no download-transport or manager-causality conclusion is justified.
- Only control evidence/selection and its tests changed. Frozen institution,
  search, PDF preference, Viewer detection, download manager and verifier were
  unchanged. 148 tests passed, Ruff passed, wheel build passed before the attempt.

## Passive observation after a single click timeout — 2026-09-06

- Reused the existing complete Viewer in the same dedicated native-behavior
  browser with no_defaults=True. Frozen candidate selection again excluded Save
  to Google Drive and selected the unique main-toolbar Download (candidate 1).
  No institution/PDF navigation or URL replay was performed.
- Before one normal locator.click(timeout=5000), attached Playwright download
  listeners to current/new pages, Browser.downloadWillBegin/downloadProgress
  callbacks, and filesystem snapshots for three deduplicated local directories
  covering configured/default downloads, requested output and runtime.
  No Browser.setDownloadBehavior or other download override was sent. Browser
  event callbacks were passive; silence alone does not prove those events would
  be emitted under native behavior.
- Actual sequence: IEEE_PDF_VIEWER_OPENED → VIEWER_DOWNLOAD_CONTROL_FOUND →
  PASSIVE_DOWNLOAD_OBSERVERS_READY → VIEWER_DOWNLOAD_CLICK_UNCONFIRMED →
  **VIEWER_DOWNLOAD_CLICK_NOT_CONFIRMED** after the complete 30-second window.
- No Playwright download, Browser download evidence, or new/changed .pdf,
  .crdownload or .jsp file was observed in the monitored directories. Existing
  files were excluded using pre-click size/mtime snapshots. No new candidate
  reached verification or final save. This bounded absence of evidence does not
  establish transfer failure or prove that no input event reached the browser.
- No second/trial/coordinate/JavaScript click occurred. Browser remained open.
  Frozen selector, manager, Viewer preferences and verifier were unchanged.
  Before the run: 150 tests passed, Ruff passed, wheel build passed.

## Disable native Save As prompt in dedicated profile — 2026-09-06

- With the user-confirmed dedicated Chrome closed, set and read back only the
  intended download/Viewer preferences: download.prompt_for_download=false,
  download.default_directory=<project>/runtime/download-capture (absolute local
  ignored path), plugins.always_open_pdf_externally=false. No profile was deleted
  and no authentication data was exported. Startup helpers now apply these values.
  The normal persistent-context configuration retains accept_downloads=True.
- The single native-behavior experiment used the existing no_defaults=True
  attachment so that Playwright's internal allowAndName override was not applied.
  No Browser.setDownloadBehavior call or native-dialog automation was used.
- Actual route: UESTC_WEBVPN_PORTAL_READY → UESTC_IEEE_RESOURCE_OPENED →
  IEEE_VIA_UESTC_OPENED → DOI search submitted → arnumber search submitted →
  IEEE_SEARCH_NO_RESULT. Requested DOI: 10.1109/LED.2024.3497584; arnumber: 10752539.
  The Viewer/download callback was not reached; no PDF/download click, new file,
  or verification happened in this run. No second run or URL replay followed.
- Preferences are locally confirmed, but absence of Save As and successful
  automatic download remain untested because of that earlier search failure.
  No E2E_SUCCESS is claimed. Frozen routing/search, Viewer control/PDF selector,
  download manager and verifier were not modified.
- Automated checks after changes: 151 tests passed, Ruff passed, wheel build passed.

## Unchanged institutional-only retest — 2026-09-06

- User authorized exactly one unchanged retest for DOI 10.1109/LED.2024.3497584,
  arnumber 10752539. No code, selectors or download logic changed; no additional
  automatic checks were run. The prior 151-test/Ruff/build baseline remains the
  last automated result.
- Real evidence: UESTC_WEBVPN_PORTAL_READY → UESTC_IEEE_RESOURCE_OPENED →
  IEEE_VIA_UESTC_OPENED. Proxied IEEE was on page index 2, host webvpn.uestc.edu.cn,
  with 3 frames and zero matching article candidates at initial observation.
  The existing searchbox workflow submitted the DOI, then arnumber, and returned
  IEEE_SEARCH_NO_RESULT again. No IEEE_TARGET_RESULT_FOUND occurred.
- Stopped further operations at that failure as requested. No Viewer PDF/download
  action or second network run followed. Whether Save As appears and whether
  native automatic saving completes remain untested in this run. No new verified
  file or E2E_SUCCESS. Only this non-sensitive validation record was updated.

## Manual proxied IEEE search ground truth — 2026-09-06

- Added an isolated pre-search checkpoint. Frozen institution/resource routing,
  production search, result/PDF actions, Viewer, download preferences and verifier
  were not changed. The prior browser was unavailable; the same dedicated profile
  was reopened. Existing portal logic recovered a transient detached frame and
  reached UESTC_WEBVPN_PORTAL_READY → IEEE_VIA_UESTC_OPENED.
- MANUAL_IEEE_SEARCH_READY: page index 2, frame index 0; searchbox count=1;
  selected index=NONE; initial input empty; placeholder category=EMPTY;
  aria-label category=OTHER. No automatic fill, submit, result click or PDF action
  followed. Readiness alone did not classify the box as global versus within-results.
- User manually searched 10.1109/LED.2024.3497584 and confirmed the target was
  found. Arnumber fallback was unnecessary. A subsequent read-only snapshot found
  four visible matching links for arnumber 10752539 on page index 0/frame index 0.
  These are matching links, not four distinct result cards.
- Result: **MANUAL_IEEE_SEARCH_RESULT_FOUND**. The proxied IEEE backend could return
  the target in this session. Next diagnosis can focus on automatic input,
  submission, asynchronous waiting and result detection. This does not identify
  a single cause yet; no automatic search comparison was run in this turn.
- No PDF/download experiment, second search, raw proxy URL or authentication
  secret recording. Browser was left open. 151 tests, Ruff and wheel build passed.

## Automatic main-search diagnostic succeeded — 2026-09-06

- Read-only inspection of the manual-result session identified both the main
  form search input and a within-results input under XPL-SEARCH-WITHIN-MIGR.
  The isolated search_diagnostic selects the unique enabled visible type=search
  form input outside that region; it does not take the first searchbox. Ties stop.
- The old browser closed before execution (read-only reattachment returned
  CONNECTION_REFUSED), so no fill or submission occurred in that attempt. One
  new actual institutional search run then used the same dedicated profile and
  existing institution/resource routing. No PDF or download experiment was run.
- Actual main input: page index 2, frame index 0, index 0; placeholder=EMPTY,
  aria category=OTHER; bounding box x=327.5,y=283.46875,width=518,
  height=35.333343505859375; visible/enabled=true; scope=FORM_SEARCH.
  Initial value was empty. After fill it exactly equaled
  10.1109/LED.2024.3497584, yielding SEARCH_VALUE_CONFIRMED.
- Pre-submit matching target links=0. Submission method=BUTTON: the unique
  enabled visible Search button in that input's form was clicked once. No Enter
  or arnumber fallback was attempted. IEEE_SEARCH_SUBMIT_DISPATCHED was followed
  by navigation=true, first zero result cards/target links, then result_card_count=1
  and matching_arnumber_links=4 for 10752539 → **IEEE_TARGET_RESULT_FOUND**.
  No explicit zero-result UI or sampled loading indicator was observed; absence
  of a loading sample was not interpreted as a completed zero-result response.
- The requested diagnostic DoD is met with fresh target evidence (0 → 4 links).
  The result was not clicked. Frozen production routing, result/PDF clicks, Viewer,
  download preferences/controls and verifier were unchanged. Production search
  has not yet been replaced with the isolated diagnostic implementation.
- This run establishes successful fill/button-submit/result recognition; it does
  not isolate which of input scope, DOI case, submit method or timing caused the
  earlier failures. 154 tests passed, Ruff passed, wheel build passed.

## Verified search integrated into production get — 2026-09-06

- uestc.search_article now delegates to publishers.ieee_search, retaining its
  caller/result continuation contract. The isolated search diagnostic is unchanged.
  Production selects one visible enabled main form search input outside the
  within-results region, fills the IEEE DOI in the validated uppercase query form,
  confirms the exact read-back, and clicks one uniquely associated Search button.
  No Enter-first behavior or automatic arnumber re-query remains. Missing or
  ambiguous buttons stop explicitly; no untested submission fallback was added.
- Production refreshes pages/frames, counts result cards and exact arnumber links,
  and prioritizes target evidence across scopes over zero-result markers. Only a
  submitted search with loading/navigation completion, explicit zero-result UI,
  and no target links can yield IEEE_SEARCH_NO_RESULT. Other bounded absence is
  IEEE_SEARCH_OBSERVATION_INCONCLUSIVE. Existing result click, PDF, Viewer,
  download preferences/manager and verifier were not changed.
- New production integration regressions drive get_paper through the real adapter
  and search implementation, with a within-results box first, main box second,
  fill/read-back, single button submit, delayed results, target detection despite
  a contradictory zero marker, fill-cleared failure, and explicit completed zero UI.
  Initial mock event pumping only advanced the last page; corrected it to advance
  pending page events across the fake context. Final: 157 tests passed, Ruff passed,
  wheel build passed.
- Exactly one real command ran:
  uestc-paper get 10.1109/LED.2024.3497584 --wait-seconds 600.
  Actual sequence: DOI_NORMALIZED → METADATA_FOUND → OA_NOT_FOUND →
  INSTITUTION_SESSION_UNKNOWN → IEEE_DIRECT_OPENED → direct STAMP →
  IEEE_PDF_RESPONSE_OBSERVED → IEEE_PDF_BYTES_CAPTURED → arnumber=10752539 →
  DOWNLOAD_RECEIVED → Verification INVALID_PDF_MAGIC, size=536, pages=0,
  identity=UNKNOWN → RETRIEVAL_UNVERIFIED. The CLI process exited with code 1.
- This run did not reach institutional search or IEEE_TARGET_RESULT_FOUND. The
  frozen direct-download branch returned its invalid candidate and stopped at the
  verifier; it did not fall back to institutional search afterward. No new verified
  paper was saved, no Viewer Download or Save As elimination was tested, and no
  E2E_SUCCESS is claimed. No second real run or out-of-scope download fix followed.
- Production search integration is unit/integration tested; its real first-layer
  DoD remains unverified because this earlier frozen download stage stopped the run.

## Direct-route validation and institutional fallback — 2026-09-06

- Direct candidates now pass the existing verifier before the adapter returns
  success. Valid structure plus identity=MATCH is required. Invalid candidates
  are deleted and capture state cleared before IEEE_DIRECT_RETRIEVAL_FAILED and
  official institutional fallback. Direct navigation/action timeouts also fall
  back. The post-authentication direct retry was removed; late direct-page download
  events cannot replace institutional evidence. Cancellation/security-block stops
  remain explicit and are not treated as authorization to bypass controls.
- Candidate save rejection now reports CANDIDATE_UNVERIFIED. Workflow emits final
  RETRIEVAL_UNVERIFIED only after its remaining institutional route has ended
  without a verified file. OA resolution, production search, resource routing,
  result/PDF actions, Viewer, preferences and verifier implementation are unchanged.
- Production regressions use a 536-byte HTML-like PDFBody: existing verifier
  rejects INVALID_PDF_MAGIC, temporary candidate is absent when institutional
  entry starts, and real production search executes and finds the target in mocks.
  Valid direct PDF skips institution entry; direct timeout falls back. Each asserts
  one direct attempt, no repeated direct URL, and no premature final unverified state.
  Obsolete post-auth-retry tests were replaced with the new no-retry contract.
  Final checks: 158 tests passed, Ruff passed, wheel build passed.
- Exactly one real production command ran for DOI 10.1109/LED.2024.3497584 with
  --wait-seconds 600. This time the direct attempt returned
  IEEE_PDF_VIEWER_UNCONFIRMED, with observed arnumber 10752539, rather than a captured
  536-byte invalid candidate. It emitted IEEE_DIRECT_RETRIEVAL_FAILED and entered
  UESTC_WEBVPN_PORTAL_READY → UESTC_IEEE_RESOURCE_OPENED → IEEE_VIA_UESTC_OPENED.
- Production selected the main searchbox on page 3/frame 0/index 0, confirmed
  10.1109/LED.2024.3497584, and used BUTTON once. The call was unconfirmed, but
  continued observation found result_card_count=1 and matching_arnumber_links=4:
  IEEE_TARGET_RESULT_FOUND → IEEE_TARGET_ARTICLE_OPENED.
- The frozen downstream PDF action ran on webvpn.uestc.edu.cn, then returned
  IEEE_PROXY_ACCESS_REQUIRED. Only then was RETRIEVAL_UNVERIFIED emitted. No verified
  output, Viewer Download/Save As result or E2E_SUCCESS was obtained. No second run
  or out-of-scope PDF/search change followed.
- Real direct-failure → institutional production-search continuation is confirmed.
  The exact invalid-536-byte branch is regression-tested but was not reproduced
  in this single real run; these evidence levels are intentionally distinguished.

### 2026-09-06 — production target-result PDF route

- Production search now passes its exact matched result link to a result-card PDF
  callback. It requires a single visible enabled STAMP link with the same article
  number, and rejects containers containing other article identities. It reuses
  the validated normal pointer click and existing Viewer detection. Article-detail
  navigation is retained only when no reliable result PDF control is available.
  A potentially dispatched PDF click is not retried through the detail route.
- Regression checks cover result PDF selection without detail navigation and
  absent result PDF with detail fallback. Final automated checks: 160 tests passed,
  Ruff passed, wheel build passed.
- Exactly one production get ran for DOI 10.1109/LED.2024.3497584 with a 600-second
  authentication window. Direct retrieval captured 536 bytes; verifier rejected
  INVALID_PDF_MAGIC (pages=0, identity=UNKNOWN). Institutional fallback continued.
- The run observed the legacy VPN candidate but did not detect authenticated
  portal markers before the deadline. Actual terminal outcome:
  UESTC_AUTH_OR_ENTRY_TIMEOUT → RETRIEVAL_UNVERIFIED (process exit code 1).
  This is a detector observation, not proof that the user lacks authorization.
- The run did not reach production search, result PDF click or Viewer Download.
  Therefore the new result-to-Viewer path remains unverified in this real run;
  no new verified PDF or E2E_SUCCESS was produced. No second run was performed.
- Viewer toolbar download remains in the independent diagnostic implementation;
  this change does not integrate or modify it. Existing production download
  listeners and verification remain available if a download event occurs.

### 2026-09-06 — production Viewer download integration, one real run

- The production result-card route now invokes Viewer Download only after
  IEEE_PDF_VIEWER_OPENED. It reuses the existing disambiguation, additionally
  requiring exact Download/下载 aria-label or title, visible/enabled main toolbar,
  and exclusion of Drive/menu controls. One normal locator click is followed by
  a full 30-second observation even on timeout; no second click or URL replay.
- Production get uses a visible native Chromium process with the same dedicated
  profile and a loopback-only CDP connection using no_defaults=True. This avoids
  Playwright's internal allowAndName override. The installed connect_over_cdp API
  has no accept_downloads argument: downloads follow Chrome's native accepting
  behavior. The original launch helper still has accept_downloads=True. Neither
  production native setup nor the new Viewer download helper calls
  Browser.setDownloadBehavior. Browser.close is used only for cleanup.
- Only new/changed files from runtime/download-capture are candidates; .crdownload
  is excluded. The existing verifier must establish structural validity and DOI
  MATCH before handing the candidate to the existing exclusive final-save gate.
  UESTC_PAPER_OUTPUT selects the final directory; this run used D:\文件.
- Automated checks: 167 tests passed, Ruff passed, wheel build passed. Regressions
  cover production Viewer handoff, one click, timeout observation, filesystem and
  Playwright artifacts, rejection of invalid/partial files, and native context
  setup without download overrides.
- One real production get ran for DOI 10.1109/LED.2024.3497584, wait-seconds=600.
  Direct invalid 536-byte candidate was rejected, then the run reached:
  UESTC_WEBVPN_PORTAL_READY → IEEE_VIA_UESTC_OPENED → IEEE_TARGET_RESULT_FOUND
  (one result card, four matching links) → IEEE_TARGET_RESULT_PDF_FOUND →
  IEEE_TARGET_RESULT_PDF_CLICKED → IEEE_STAMP_OPENED → IEEE_PDF_VIEWER_OPENED.
- Main-toolbar Download was uniquely identified and Save to Google Drive excluded.
  VIEWER_DOWNLOAD_CONTROL_FOUND → VIEWER_DOWNLOAD_CLICK_UNCONFIRMED.
  During the full post-click 30 seconds, no Playwright download event or new/changed
  eligible capture-directory file was observed. Terminal result:
  VIEWER_DOWNLOAD_CLICK_NOT_CONFIRMED → RETRIEVAL_UNVERIFIED (exit code 1).
- No new verified PDF/final save or E2E_SUCCESS was obtained. No native dialog was
  automated; absence/presence of Save As was not independently established. The
  observed outcome does not establish whether the click was dispatched or explain
  the root cause. No second run/click followed, and no post-run code fix was made.
- After browser exit, safe preference inspection confirmed prompt_for_download=false,
  always_open_pdf_externally=false, and the configured capture directory unchanged.

### 2026-09-06 — single Viewer pointer-input A/B attempt

- Only Viewer Download input/observation changed: current locator bounding-box
  center, fresh read-only hit test including open shadow roots, then one mouse
  move/down/up. No locator click, forced click, JS click, URL replay, OS automation
  or download-behavior override was added. Existing selection and verification
  gates remain unchanged. Viewer polling is once per second, up to 90 seconds,
  with elapsed time reported if ready. Download observation is bounded to 120
  seconds and returns early for a complete candidate; .crdownload is never verified.
- Regression results: 168 tests passed, Ruff passed, wheel build passed. Tests
  cover failed hit test with no click, dynamic center coordinates, one down/up,
  early valid-file completion, invalid PDF, incomplete file and no download evidence.
- Exactly one production get ran for DOI 10.1109/LED.2024.3497584 with wait-seconds=600
  and final output configured to D:\文件. It reached UESTC_WEBVPN_PORTAL_READY and
  IEEE_VIA_UESTC_OPENED. Main search input read-back matched the requested DOI.
  Search button submission was unconfirmed; the existing bounded search observer
  returned IEEE_SEARCH_OBSERVATION_INCONCLUSIVE → RETRIEVAL_UNVERIFIED (exit code 1).
- This run did not reach the target result or Viewer. Viewer wait time, Download
  uniqueness, hit test, mouse down/up, Save As, partial-file observation, new file
  sizes and verifier results are all not applicable to this attempt. There was
  no Viewer Download click and no new verified final output. E2E_SUCCESS was not
  achieved. The result does not evaluate the pointer A/B path. No second run or
  post-run search/download code change was made.

### 2026-09-06 — Search submit observation and downstream pointer A/B

- Kept the verified searchbox, fill/read-back, associated Search selector and
  result parser. Added bounding-box validity and pre-submit target-count evidence,
  explicit IEEE_SEARCH_SUBMIT_CONFIRMED, and approximately one-second fresh-scope
  polling. Both confirmed and unconfirmed submissions retain the existing full
  60-second post-submit observation. No Enter or alternate pointer fallback added.
- Automated checks: 169 tests passed, Ruff passed, wheel build passed. Regression
  verifies a dispatched Search click that raises timeout still reaches target
  results through bounded observation without a second submission.
- Exactly one real production get ran for DOI 10.1109/LED.2024.3497584. It reached
  UESTC_WEBVPN_PORTAL_READY → IEEE_VIA_UESTC_OPENED. Search evidence: one associated
  visible/enabled Search button; valid bounding box; zero pre-submit target links;
  IEEE_SEARCH_SUBMIT_CONFIRMED → one result card/four target links →
  IEEE_TARGET_RESULT_FOUND. Existing result-card PDF route continued normally.
- Viewer readiness took 69.32 seconds after the result PDF pointer call returned.
  IEEE_PDF_VIEWER_OPENED → VIEWER_DOWNLOAD_CONTROL_FOUND. The existing selector
  uniquely selected main-toolbar Download and excluded Save to Google Drive.
  Existing pointer A/B reported hit-test passed, mouse down completed, mouse up
  completed, VIEWER_MOUSE_CLICK_DISPATCHED. There was exactly one pointer action.
- The full 120-second download observation produced no Playwright download or
  new/changed eligible capture file: crdownload_seen=false, max_bytes=0,
  final_bytes=0. Result: VIEWER_MOUSE_CLICK_NOT_CONFIRMED → RETRIEVAL_UNVERIFIED
  (process exit 1). No candidate existed for verification or final saving.
  Save As presence remains UNKNOWN; no OS inspection/automation was performed.
- This run confirms production search continuation and actual execution of the
  prepared Viewer pointer A/B. It does not establish download activation or
  E2E_SUCCESS. No second run, click, URL replay or post-run code fix followed.

### 2026-09-06 — read-only native Save As confirmation

- Added an opt-in local diagnostic using Win32 EnumWindows, IsWindowVisible and
  GetWindowTextW only. It compares visible top-level Save As/另存为 handles against
  a pre-click snapshot. Only the fixed SAVE_AS category and appeared-after-click
  boolean are emitted; no control contents, raw titles or window handles are logged.
  No Windows control action is implemented. New-dialog detection is polled every
  0.5 seconds for at most 10 seconds. If absent, passive browser/file observation
  continues for 30 seconds. If present, the diagnostic returns immediately.
- Automated checks: 171 tests passed, Ruff passed, wheel build passed. Regression
  distinguishes an already-open Save As from a newly appearing one and checks the
  bounded detection and passive-observation windows.
- One real production run used DOI 10.1109/LED.2024.3497584, wait-seconds=600 and
  UESTC_PAPER_NATIVE_SAVE_AS_DIAGNOSTIC=1. Existing portal/search/result-PDF path
  reached Viewer readiness after 34.82 seconds. Main-toolbar Download was uniquely
  selected, hit-test passed, and one mouse down/up completed.
- Actual evidence: NATIVE_SAVE_AS_SNAPSHOT_READY → VIEWER_MOUSE_CLICK_DISPATCHED →
  NATIVE_SAVE_AS_DETECTED: window_title_category=SAVE_AS; appeared_after_click=true.
  The diagnostic stopped immediately without clicking Save or issuing another
  Download. This satisfies the native-window detection DoD. It is not a file
  retrieval success; no PDF was verified/saved in this run. Production consequently
  returned RETRIEVAL_UNVERIFIED (exit code 1).

### 2026-09-06 — Windows UIA Save As fallback implementation

- Added Windows-only pywinauto>=0.6.9,<0.7 dependency and a mockable UIA layer.
  The pre-click snapshot is retained; only a uniquely new Save As handle is eligible.
  Multiple new dialogs are ambiguous. Before mutation the bound dialog must remain
  new, visible under the Save As category, and belong to chrome.exe/msedge.exe.
- UIA identifies a unique filename Edit and Save Button by control type and
  localized accessible label. It sets a unique absolute runtime/download-capture
  UUID.pdf path, confirms exact read-back, then invokes Save once. It neither sends
  keys nor uses coordinates. A dialog remaining after the bounded close wait returns
  NATIVE_SAVE_AS_SAVE_UNCONFIRMED. Non-Windows UIA returns NATIVE_SAVE_AS_UNSUPPORTED.
- Only that UUID target may enter the existing file completion/verifier path;
  observation is at most 180 seconds, excludes .crdownload, and requires DOI MATCH.
  The existing exclusive final-save gate and verifier implementation are unchanged.
- Automated checks: 180 tests passed, Ruff passed, wheel build passed. Coverage
  includes absent/pre-existing/new dialogs, edit/button ambiguity, read-back
  mismatch, single Save invocation, persistent dialog, unsupported platform, and
  existing completed/partial/invalid PDF gates. Installed local UIA dependencies:
  pywinauto 0.6.9 and comtypes 1.4.16 (existing pywin32 dependency was available).
- Exactly one production get ran for DOI 10.1109/LED.2024.3497584, wait-seconds=600.
  It reached authenticated portal, official IEEE entry, confirmed Search submission,
  one result card/four target links and IEEE_TARGET_RESULT_PDF_FOUND. The frozen
  result PDF pointer returned IEEE_TARGET_RESULT_PDF_CLICK_UNCONFIRMED, and its
  existing observation ended with IEEE_PDF_VIEWER_UNCONFIRMED → RETRIEVAL_UNVERIFIED
  (exit code 1). No confirmed STAMP or Viewer followed in this run.
- Viewer Download, native detection, path entry and Save invocation were not reached.
  No new verified final PDF/E2E_SUCCESS. The UIA fallback remains unvalidated in the
  real browser. No second PDF/Download/Save attempt or post-run upstream fix occurred.

### 2026-09-06 — result PDF passive Viewer wait, 120 seconds

- Changed only post-result-PDF observation: default maximum 120 seconds, fresh
  context page/frame snapshots approximately each second, continue after an
  unconfirmed pointer call, and return immediately on existing Viewer readiness.
  STAMP/frame evidence is recorded separately. No evidence at deadline returns
  IEEE_PDF_VIEWER_TIMEOUT; evidence without readiness returns IEEE_PDF_VIEWER_NOT_READY.
  The PDF locator, click behavior, downstream UIA and verifier are unchanged.
- Automated checks: 183 tests passed, Ruff passed, wheel build passed. New tests
  cover an unconfirmed click with Viewer ready at second 110 (single pointer call),
  120 seconds without evidence, and partial STAMP/frame evidence without readiness.
- Exactly one real production get ran for DOI 10.1109/LED.2024.3497584 with
  wait-seconds=600. It reached UESTC_WEBVPN_PORTAL_READY → IEEE_VIA_UESTC_OPENED,
  confirmed search value and one valid associated Search button. Search returned
  IEEE_SEARCH_SUBMIT_UNCONFIRMED; the frozen search observation ended with
  IEEE_SEARCH_OBSERVATION_INCONCLUSIVE → RETRIEVAL_UNVERIFIED (exit code 1).
- The new Viewer observation was not reached in this run. No institutional result
  PDF, Viewer Download or Save click occurred. No new verified PDF/E2E_SUCCESS.
  No second run or frozen-module fix followed. This run does not evaluate the
  new 120-second Viewer wait or the native UIA fallback.

### 2026-09-06 — first automated production E2E_SUCCESS

- This turn changed only Search button input: the existing unique associated
  visible/enabled button and valid bounding box, fresh hit test, then one dynamic
  center mouse move/down/up. No locator click, Enter fallback, JS click or second
  submit. The result parser and existing post-submit observation were retained.
- Automated validation: 184 tests passed, Ruff passed, wheel build passed.
  Regression checks dynamic center coordinates, exactly one down/up, no dispatch
  on failed hit test, and observation after an unconfirmed mouse dispatch.
- Exactly one real production get ran for DOI 10.1109/LED.2024.3497584 with
  --wait-seconds 600 and final output D:\文件. Search hit test passed and emitted
  IEEE_SEARCH_MOUSE_DISPATCHED, then one result card/four matching arnumber links
  (10752539) → IEEE_TARGET_RESULT_FOUND. The frozen result PDF action ran once.
- Real continuation: IEEE_STAMP_OPENED → IEEE_PDF_VIEWER_FRAME_OBSERVED →
  IEEE_PDF_VIEWER_OPENED (67.20 seconds) → unique main-toolbar Download →
  hit-test passed → one Viewer mouse down/up → VIEWER_MOUSE_CLICK_DISPATCHED →
  NATIVE_SAVE_AS_DETECTED (new SAVE_AS category) → SAVE_AS_PATH_CONFIRMED →
  one NATIVE_SAVE_AS_SAVE_DISPATCHED → DOWNLOAD_FILE_COMPLETED.
- Access route: authenticated UESTC official IEEE/IEL resource, proxied IEEE,
  visible dedicated native Chromium PDF Viewer and Windows UIA Save As. No URL
  replay, additional resource/PDF/Download/Save attempt, or post-run code change.
- Verification: PDF_VERIFIED, 4 pages, 17,065,057 bytes, DOI identity MATCH.
  Existing verifier checked the capture candidate and final-save gate separately.
  Observed max/final size: 17,065,057; crdownload_seen=false. The completed file
  was observed directly. This run's size differs from the earlier manual file;
  the recorded value is the actual new file's size, not the historical baseline.
- Final exclusive output: D:\文件\932bdf7f5c76995a-c97adb57.pdf.
  Offline final-file presence/magic/EOF check: file exists, starts %PDF,
  contains %%EOF near tail. SHA-256:
  e888caec872ab5ae2a5c2abd8197d391ff5a438735711312179ecace013f2dfa.
- Outcome: SUCCESS → E2E_SUCCESS, production process exit code 0. This is the
  first automated end-to-end success for this DOI in the recorded environment;
  it does not establish reliability for other papers or future sessions.
  Profile/capture directories remain ignored. No credentials, cookies, tokens,
  raw proxy URLs, authentication screenshots or subscription PDF content are
  included in this validation record or added to Git.
