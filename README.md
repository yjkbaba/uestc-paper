# uestc-paper

An academic paper retrieval skill for authorized users of the University of Electronic Science and Technology of China (UESTC).

## Goal

`uestc-paper` is intended to help UESTC students and staff retrieve individual academic papers they are authorized to access. The workflow prefers lawful open-access copies first, then uses user-controlled institutional access such as publisher institutional login/CARSI or the official UESTC WebVPN.

## Design principles

- Open Access first.
- Institutional authentication is completed by the user in a visible browser.
- Never request, store, log, or autofill UESTC passwords, OTPs, or CAPTCHA answers.
- Reuse only local browser session/profile state.
- Do not upload cookies, browser profiles, or session state to GitHub or remote services.
- Do not implement systematic or bulk downloading of subscribed library resources.
- Verify that a downloaded file is a genuine article PDF rather than a login/error/preview page.

## Planned access order

1. Open Access source
2. Publisher institutional login / CARSI
3. UESTC WebVPN
4. Report unavailable

## V0.1 scope

The first version will focus on a single-paper workflow:

```text
DOI / title / publisher URL
        ↓
Resolve metadata
        ↓
Open Access check
        ↓
Institutional access if needed
        ↓
Visible browser authentication
        ↓
Download PDF
        ↓
Verify PDF
        ↓
Save locally
```

Planned CLI:

```bash
uestc-paper setup
uestc-paper login
uestc-paper get <identifier>
uestc-paper status
```

## Project status

Early-stage repository skeleton. Browser automation, publisher adapters, DOI resolution, Open Access resolution, and PDF verification are planned for subsequent versions.

## License

MIT License. See `LICENSE`.
