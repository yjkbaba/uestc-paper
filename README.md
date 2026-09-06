# uestc-paper

Single-paper retrieval for authorized University of Electronic Science and
Technology of China (UESTC) users. Release candidate: **0.1.0rc1**.

## What it does

- DOI-first: one DOI per invocation; raw DOI, `doi:` and `https://doi.org/` accepted.
- Open Access first; public Crossref metadata and Europe PMC OA locations.
- Institutional fallback through a visible, dedicated persistent browser.
- UESTC authentication remains manual; resource navigation and retrieval are automatic.
- Current real institutional validation: **IEEE/IEL on Windows**.
- Final PDF delivery requires the verifier and exclusive final-save gate.

Title and publisher-URL input are not implemented in this RC.

## Current validated path

Open Access implementation (automated fixture coverage; source coverage is limited):

```text
DOI → lawful OA location → download → verifier → save
```

IEEE institutional (one real production E2E verified):

```text
DOI → metadata → OA lookup → opportunistic direct IEEE
→ if not verified: UESTC WebVPN → official IEEE/IEL resource
→ IEEE main search → exact target result PDF → Chrome PDF Viewer
→ Viewer Download → native Save As → Windows UIA temporary-path save
→ verifier (DOI MATCH) → exclusive final output → E2E_SUCCESS
```

An invalid direct candidate does not end retrieval. No direct retry or URL replay
is used. WebVPN access follows its resource portal; logging into WebVPN alone is
not treated as permission on ordinary publisher URLs. If the result card has no
reliable PDF control, the existing article-detail fallback is available.

## Installation and CLI

Python 3.10+; the validated environment used Windows 11 and Python 3.13.9.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install .
python -m playwright install chromium
uestc-paper --help
uestc-paper setup
uestc-paper status
uestc-paper login
uestc-paper get 10.1109/LED.2024.3497584 --wait-seconds 600
```

`setup` creates local directories and reports runtime availability; it does not
install a browser. `login` opens the visible browser, lets you authenticate, then
asks for terminal Enter to close it. During `get`, portal detection continues
without terminal confirmation. `--wait-seconds` controls institutional entry wait
(1–3600; default 300), not a fixed sleep. `--no-browser` limits retrieval to OA.

Keep the same working directory or set `UESTC_PAPER_HOME`; `--home PATH` overrides
it. The dedicated profile is `runtime/browser-profile/`, and unverified downloads
stay in `runtime/download-capture/`. Verified output defaults to `downloads/`.
Set `UESTC_PAPER_OUTPUT` to choose another local final directory, for example:

```powershell
$env:UESTC_PAPER_OUTPUT = 'D:\文件'
uestc-paper get 10.1109/LED.2024.3497584 --wait-seconds 600
```

The wheel includes this Skill under `share/uestc-paper/skills/uestc-paper` in the
installation prefix. The repository Skill is also usable directly.

## Authentication boundary

The tool does **not** automate or collect passwords, OTPs, CAPTCHA answers or
other authentication secrets. Complete school login and required SSO confirmation
yourself in the visible browser. Local session data remains in the ignored profile;
never upload it, export cookies, or commit authentication screenshots.

Windows UIA automation is limited to the newly detected Chrome/Edge **Save As**
window: unique filename field, exact temporary-path read-back, and one Save action.
It does not operate school authentication controls or unrelated Windows windows.
There are no paywall, CAPTCHA, anti-bot or rate-limit bypasses.

## Windows limitation

The full IEEE Viewer-save chain is currently validated **only on Windows** because
it uses Windows UI Automation for native Save As. Non-Windows institutional E2E
has not been verified; its native Save fallback reports `NATIVE_SAVE_AS_UNSUPPORTED`.
Public OA retrieval has no Windows UI dependency.

Production uses native visible Chromium with a loopback-only Playwright CDP
connection preserving Chrome download behavior. The dedicated profile allows the
built-in PDF Viewer and disables download prompts. Viewer Save As can still occur;
the scoped UIA fallback handles it. Production does not apply `allowAndName`.

## Scope

V0.1 is single-paper retrieval, not a bulk downloader, crawler, or systematic
subscribed-content harvesting tool. IEEE is the only institutional adapter.
Elsevier, Springer, ACM, Wiley and other publishers are **not verified or supported**
by institutional adapters in this RC. Use only papers you are entitled to access.

## Verification

HTTP 200 or a download event is not success. The existing verifier checks `%PDF`,
512 bytes–100 MiB size, strict PDF parsing, 1–1000 pages, error/preview evidence,
and DOI/title identity from metadata and the first page. The native Viewer route
requires **DOI MATCH**, not title-only evidence. `.crdownload` is never accepted.
Unconfirmed files are not delivered; final files receive unique names and existing
files are not overwritten. These are conservative identity/structure heuristics,
not a guarantee of every page's visual completeness; no OCR is implemented.

## Status

**IEEE real E2E: VERIFIED**, for DOI `10.1109/LED.2024.3497584`: 17,065,057 bytes,
4 pages, PDF_VERIFIED, DOI MATCH. This is one successful real environment/paper,
not a reliability claim for every session or article. Historical failures remain
in [validation.md](docs/validation.md); see the [frozen baseline](docs/release-v0.1.0-rc1-baseline.md).

`status` reports installed runtime and local profile-file presence; UNKNOWN is
not NO_ACCESS. It never claims an ACTIVE entitlement from file presence alone.
`login` returns `LOGIN_STATE_UNKNOWN` because local state cannot prove entitlement.

Failure states include `OA_NOT_FOUND`, `OA_TEMPORARILY_UNAVAILABLE`,
`IEEE_SEARCH_OBSERVATION_INCONCLUSIVE`, `IEEE_PDF_VIEWER_TIMEOUT`, native Save
failure states and `RETRIEVAL_UNVERIFIED`. Only verified final saving is success.
Exit 0 denotes success; unavailable/unverified CLI paths generally use 2, cancellation
130. Some historical browser-failure runs exited 1; rely on the explicit stage too.

## Dependencies and development

Runtime: Playwright >=1.62,<2; pypdf >=5,<7; Windows-only pywinauto >=0.6.9,<0.7
(with comtypes/pywin32 transitive dependencies). The minimum matches validated Playwright 1.62.0 native-CDP capabilities. Dev: pytest and Ruff; setuptools build.

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m compileall -q uestc_paper
```

Tests use synthetic files and mocked UI, no real credentials or subscriptions.
Do not delete diagnostic modules during RC freeze: production reuses several.
No new live download is needed for release smoke testing.

## License

MIT; see [LICENSE](LICENSE). Never commit PDFs, browser state or credentials.
