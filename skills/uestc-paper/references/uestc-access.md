# UESTC institutional access

## Purpose

This document defines institution-specific access behavior for authorized users of the University of Electronic Science and Technology of China (UESTC).

## Official remote-access route

The official UESTC WebVPN entry point is:

`https://vpn.uestc.edu.cn`

Treat this value as configuration, not as a hidden credential.

## Important WebVPN behavior

UESTC WebVPN should be treated as a resource-list-based web proxy. Do not assume that an arbitrary publisher URL opened after authentication is automatically routed through the institution.

A robust implementation should:

1. open the official WebVPN in a visible browser;
2. let the user complete authentication manually;
3. verify that authentication succeeded without reading credentials;
4. identify the relevant institution-provided library/database resource entry;
5. navigate through that resource route when WebVPN proxying is required;
6. continue to the target article inside the authorized browser context.

Do not hard-code fragile DOM selectors without fallback strategies and tests.

## CARSI / publisher institutional login

Where a publisher supports institutional sign-in, prefer the publisher's supported institutional flow when it can legitimately recognize UESTC access. The exact list of supported publishers/databases can change, so detection should be capability-based rather than treated as a permanent hard-coded list.

Recommended behavior:

- detect an institutional-sign-in option;
- select or search for UESTC only through the publisher's normal UI;
- allow any UESTC SSO step to occur visibly;
- reuse an existing authenticated browser session where available;
- never automate password, OTP, or CAPTCHA entry.

## Session persistence

A persistent local browser profile may contain cookies and local storage needed to avoid repeating login on every retrieval.

Requirements:

- keep the profile on the user's machine;
- store it under an ignored runtime directory;
- never serialize cookies into logs;
- never commit the profile to Git;
- never sync it to a public or shared service;
- provide a way for the user to delete/reset the local session.

## Status detection

`uestc-paper status` should eventually report only non-secret state, for example:

```text
Browser profile: present
Institutional session: likely active / expired / unknown
Output directory: configured
```

It should not print cookies, tokens, usernames, authorization headers, or personal account information.

## Failure handling

If institutional access fails, distinguish among:

- authentication required;
- session expired;
- publisher/database not exposed through the current route;
- institution may not subscribe to the requested content;
- publisher blocked automation and requires manual browser continuation;
- article identifier could not be resolved.

Do not misreport access failure as proof that UESTC lacks a subscription.
