# v0.1.0-rc1 frozen baseline

Recorded: 2026-09-06T20:30:22 (Asia/Shanghai).
Branch: main
Pre-release HEAD: bbc66dc1be989876305f244b1c059442513ee819
The E2E implementation was uncommitted at this HEAD. This baseline describes the
working tree, not the old HEAD's implementation. The release commit will capture it.

## Real immutable PDF evidence

- DOI: 10.1109/LED.2024.3497584
- Real run outcome: E2E_SUCCESS (recorded 2026-09-06; no new download this release turn)
- Filename: 932bdf7f5c76995a-c97adb57.pdf
- Exact bytes: 17065057
- SHA-256: e888caec872ab5ae2a5c2abd8197d391ff5a438735711312179ecace013f2dfa
- Pages: 4
- starts_with_%PDF: True
- %%EOF_near_end: True
- Verifier: PDF_VERIFIED
- DOI identity: MATCH
- REAL_PDF_OUTSIDE_REPOSITORY=true
- The file is under D:/文件, outside this Git worktree. No PDF is staged or tracked.
- Each successful Search/result PDF/Viewer Download/native Save action ran once.

## Environment and initial QA

- Windows-11-10.0.26200-SP0
- Python: 3.13.9 | packaged by Anaconda, Inc. | (main, Oct 21 2025, 19:09:58) [MSC v.1929 64 bit (AMD64)]
- Dependencies: playwright=1.62.0, pypdf=6.17.0, pywinauto=0.6.9, comtypes=1.4.16
- Visible dedicated native Chromium; official UESTC IEEE/IEL proxy; Windows UIA Save As.
- 184 tests PASS re-run before release changes; Ruff/build PASS at successful baseline.

## Initial working tree

```text
M .gitignore
 M README.md
?? docs/
?? pyproject.toml
?? tests/
?? uestc_paper/
```

```text
.gitignore |   6 +++
 README.md  | 127 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++-
 2 files changed, 131 insertions(+), 2 deletions(-)
```

Source/tests/pyproject and validation docs above were untracked development output.
No retrieval algorithm changes are authorized in this release-freeze turn.

## RC final QA and audit

- Version: 0.1.0rc1; annotated tag name: v0.1.0-rc1.
- 184 tests PASS; Ruff PASS; compile/import PASS; wheel and sdist build PASS.
- WHEEL_CONTENT_AUDIT_PASS; SDIST_CONTENT_AUDIT_PASS. Python package, MIT license,
  metadata and Skill/reference Markdown included; no runtime/PDF/profile/log/image
  artifacts. Wheel contains 44 entries; source archive contains 92 files.
- Installed wheel in a temporary venv outside the source import path; third-party
  dependencies reused from the validated environment via a local .pth file.
  Installed package origin/version checked, import and all five CLI help commands
  PASS. No authentication, browser launch or paper retrieval in release QA.
- SECRET_SCAN_PASS. Tracked/staged/untracked candidate text and artifact paths
  checked. Six signed-URL keyword findings were synthetic uppercase-placeholder
  fixtures in tests; no real signed URL or token was retained. Generic safety words
  in docs/code are not secrets. No claim of universal secret-detection completeness.
- COOKIE_FILE_TRACKED=false; BROWSER_PROFILE_TRACKED=false;
  SUBSCRIPTION_PDF_TRACKED=false; CREDENTIAL_ARTIFACT_TRACKED=false.
- Runtime/capture/forensics, PDFs, partial downloads, caches and build artifacts ignored.
- Core-file hash comparison against the initial working tree: unchanged except
  __init__.py version metadata/line-ending normalization. No algorithm changes.
- No diagnostic code deleted: production imports some diagnostic helpers.
- README, Skill and validation current-status summary updated; historical failures preserved.
- Remote confirmed as private yjkbaba/uestc-paper, default branch main; visibility unchanged.
- The release commit SHA is recorded by the annotated tag and final release report,
  not embedded recursively in this committed baseline file.
