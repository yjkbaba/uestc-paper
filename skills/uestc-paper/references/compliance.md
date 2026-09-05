# Compliance and responsible use

## Scope

`uestc-paper` is intended to assist authorized UESTC users with individual academic-paper retrieval through lawful Open Access or institutionally authorized access.

## Subscribed-resource restrictions

Do not implement or encourage systematic, continuous, concentrated, or bulk downloading of subscribed electronic resources.

V0.1 should operate on explicit single-paper requests. If future versions add convenience workflows, they must preserve publisher and library usage rules and avoid patterns that resemble harvesting or mirroring.

## Authentication safety

The project must not collect or persist institutional credentials.

Do not:

- ask users to paste passwords into the CLI or agent chat;
- store passwords in environment variables for automation;
- log OTP/2FA/CAPTCHA values;
- bypass CAPTCHA or anti-bot protections;
- extract secrets from browser password managers;
- publish session cookies, tokens, or authenticated browser profiles.

## Access controls

Do not bypass paywalls, access-control mechanisms, license restrictions, or publisher security systems. Institutional access is valid only when the user is authorized and the publisher/library route grants access normally.

## Repository content

Do not commit:

- subscription PDFs downloaded for personal use;
- authentication screenshots containing personal information;
- cookies or session files;
- browser profiles;
- secrets or local tokens.

Open Access test fixtures should be preferred for automated tests.

## Logging

Logs should record operational state without secrets. Avoid logging:

- Cookie headers
- Authorization headers
- session tokens
- usernames/student identifiers unless strictly necessary
- full redirect URLs when they contain authentication tokens

## User control

Authentication-sensitive actions must remain visible to the user. The user should be able to cancel, close the browser, reset the profile, and delete local session state.
