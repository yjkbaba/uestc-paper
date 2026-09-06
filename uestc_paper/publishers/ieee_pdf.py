"""Bounded normal PDF actions and secret-free navigation evidence."""

import re
import time
from urllib.parse import urljoin, urlsplit

from playwright.sync_api import Error, TimeoutError

from ..uestc import is_webvpn_url
from .ieee_response import PDFObserver


def location(url):
    parsed = urlsplit(url)
    path = parsed.path.lower()
    kind = ('STAMP' if '/stamp/' in path else 'ARTICLE' if '/document/' in path
            else 'PDF' if path.endswith('.pdf') else 'OTHER')
    return f"host={parsed.hostname or 'NONE'}; path_type={kind}"


def evidence(label, page, context):
    owner = page if page in context.pages else page.page
    # Titles can contain arbitrary reflected query data. Emit an allowlisted title category.
    try:
        title = page.title()
    except (Error, AttributeError):
        title = ''
    safe_title = ('IEEE Xplore Full-Text PDF' if title == 'IEEE Xplore Full-Text PDF'
                  else 'IEEE Xplore' if 'IEEE Xplore' in title else 'REDACTED')
    print(f"{label}: page_index={context.pages.index(owner)}; {location(page.url)}; "
          f"title={safe_title}")


def attempt(page, captured, context, seconds, proxied=False, use_cdp=False, download_directory=None):
    owner = page if page in context.pages else page.page
    original_url = page.url
    before = list(context.pages)
    observed = []
    responses = []
    pdf_observer = PDFObserver(context, proxied, location)
    if use_cdp:
        from .ieee_cdp import CDPPDFObserver
        pdf_observer = CDPPDFObserver(context, owner, location, download_directory)

    def response_received(response):
        pdf_observer.response(response)
        if response.request.is_navigation_request():
            responses.append(location(response.url))

    def attach(new_page):
        observed.append(new_page)
        new_page.on('response', response_received)

    owner.on('response', response_received)
    context.on('page', attach)
    evidence('IEEE_PDF_ARTICLE', page, context)
    clicked = False
    escaped = False
    used = set()
    last = None
    viewer_seen = False
    new = []
    deadline = time.monotonic() + seconds
    try:
        while time.monotonic() < deadline:
            if getattr(pdf_observer, 'failure', None):
                return pdf_observer.failure
            if use_cdp or not captured:
                body = pdf_observer.capture(captured)
                if body is not None:
                    if use_cdp:
                        captured.clear()
                    captured.append((body, 'UESTC WebVPN / IEEE' if proxied else 'IEEE direct'))
                    return 'DOWNLOAD_RECEIVED'
            if captured and not use_cdp:
                print('IEEE_PDF_CLICK: download')
                download = captured[0][0] if isinstance(captured[0], tuple) else None
                download_url = getattr(download, 'url', '')
                if download_url:
                    print(f'IEEE_PDF_DOWNLOAD: {location(download_url)}')
                if proxied and urlsplit(download_url).hostname == 'ieeexplore.ieee.org':
                    captured.clear()
                    return 'IEEE_PDF_PROXY_ESCAPE'
                if responses:
                    print(f'IEEE_PDF_FINAL_RESPONSE: {responses[-1]}')
                return 'DOWNLOAD_RECEIVED'
            if owner.is_closed():
                return 'IEEE_PAGE_CLOSED'
            challenge = page.get_by_text(re.compile(
                r'^(verify you are human|unusual traffic|automated access prohibited)', re.I))
            if challenge.count() and challenge.first.is_visible():
                return 'IEEE_AUTOMATION_BLOCKED'
            new = [p for p in context.pages if p not in before and not p.is_closed()]
            target = new[-1] if new else page
            if clicked and not viewer_seen:
                for scope in [target] + list(getattr(target, 'frames', [])):
                    try:
                        viewer = scope.locator(
                            "embed[type='application/pdf'], object[type='application/pdf']")
                        if viewer.count() or (hasattr(scope, 'title') and
                                              scope.title() == 'IEEE Xplore Full-Text PDF'):
                            viewer_seen = True
                            print('IEEE_PDF_VIEWER_OPENED')
                            break
                    except Error:
                        continue
            if clicked and '/stamp/' in urlsplit(target.url).path:
                if not getattr(pdf_observer, 'stamp_seen', False):
                    print('IEEE_STAMP_OPENED')
                    pdf_observer.stamp_seen = True
                pdf_observer.inspect_embeds(target)
            signature = (target.url, len(new))
            if clicked and signature != last:
                print('IEEE_PDF_CLICK: ' + ('popup' if new else 'same_page'))
                evidence('IEEE_PDF_POPUP' if new else 'IEEE_PDF_TARGET', target, context)
                if responses:
                    print(f'IEEE_PDF_FINAL_RESPONSE: {responses[-1]}')
                last = signature
            if clicked and proxied and urlsplit(target.url).hostname == 'ieeexplore.ieee.org':
                if not escaped:
                    print('IEEE_PDF_PROXY_ESCAPE')
                    escaped = True
                    owner.bring_to_front()
                    if not is_webvpn_url(page.url):
                        page.goto(original_url, wait_until='domcontentloaded', timeout=15000)
                    # Retain the escaped tab but exclude it from the next DOM-action attempt.
                    before = list(context.pages)
                    clicked = False
                else:
                    return 'IEEE_PDF_PROXY_ESCAPE'
            if not clicked:
                scopes = [page] + [f for f in owner.frames if f != owner.main_frame
                                   and f != page and is_webvpn_url(f.url)]
                candidates = []
                for scope in scopes:
                    for group in (scope.get_by_role('link', name=re.compile(r'\bPDF\b', re.I)),
                                  scope.get_by_role('button', name=re.compile(r'\bPDF\b', re.I)),
                                  scope.locator("a[href*='/stamp/stamp.jsp']")):
                        for i in range(min(group.count(), 8)):
                            action = group.nth(i)
                            if action.is_visible() and action.is_enabled():
                                href = action.get_attribute('href') or ''
                                url = urljoin(scope.url, href)
                                key = (scope.url, href, i)
                                rewritten = bool(href) and is_webvpn_url(url)
                                if key not in used and (not escaped or rewritten):
                                    candidates.append((not rewritten, action, url, key))
                if candidates:
                    _, action, url, key = sorted(candidates, key=lambda c: c[0])[0]
                    used.add(key)
                    print(f'IEEE_PDF_CONTROL: {location(url)}')
                    print('IEEE_WEBVPN_DOWNLOAD_ATTEMPT' if proxied
                          else 'IEEE_DIRECT_DOWNLOAD_ATTEMPT')
                    clicked = True
                    try:
                        action.click(timeout=3000)
                    except TimeoutError:
                        pass
                    continue
                if escaped:
                    return 'IEEE_PDF_PROXY_ESCAPE'
            owner.wait_for_timeout(200)
        if captured:
            return 'DOWNLOAD_RECEIVED'
        if getattr(pdf_observer, 'failure', None):
            return pdf_observer.failure
        body = pdf_observer.capture(captured)
        if body is not None:
            captured.append((body, 'UESTC WebVPN / IEEE' if proxied else 'IEEE direct'))
            return 'DOWNLOAD_RECEIVED'
        if captured:
            return 'DOWNLOAD_RECEIVED'
        if pdf_observer.seen:
            if use_cdp:
                print(f'IEEE_PDF_OBSERVATION_COMPLETE: candidates={len(pdf_observer.candidates)}; '
                      f'viewer_evidence={viewer_seen}')
                return pdf_observer.outcome or 'IEEE_PDF_NO_VALID_FULL_CANDIDATE'
            return 'IEEE_PDF_BODY_UNAVAILABLE'
        if escaped and not clicked:
            return 'IEEE_PDF_PROXY_ESCAPE'
        target = new[-1] if new else page
        scopes = [target] + list(getattr(target, 'frames', []))
        for scope in scopes:
            for pattern, state in (
                (r'^(verify you are human|unusual traffic|automated access prohibited)',
                 'IEEE_AUTOMATION_BLOCKED'),
                (r'^(institutional (sign.in|login|access)|sign in)( required)?$',
                 'IEEE_INSTITUTION_SIGNIN_REQUIRED'),
                (r'^(purchase|subscription required|subscribe)( .*)?$',
                 'IEEE_PROXY_ACCESS_REQUIRED' if proxied else 'IEEE_ACCESS_REQUIRED'),
            ):
                control = scope.get_by_role('heading', name=re.compile(pattern, re.I))
                if control.count() and control.first.is_visible():
                    return state
        if '/stamp/' in urlsplit(target.url).path:
            viewer = target.locator("embed[type='application/pdf'], object[type='application/pdf']")
            try:
                pdf_title = target.title() == 'IEEE Xplore Full-Text PDF'
            except (Error, AttributeError):
                pdf_title = False
            return 'IEEE_PDF_VIEWER_OPENED' if viewer.count() or pdf_title else (
                'IEEE_PDF_VIEWER_UNCONFIRMED')
        return 'IEEE_DOWNLOAD_NOT_RECEIVED' if clicked else 'IEEE_PDF_ACTION_UNAVAILABLE'
    finally:
        if use_cdp:
            pdf_observer.close()
        if responses:
            print(f'IEEE_PDF_FINAL_RESPONSE: {responses[-1]}')
        context.remove_listener('page', attach)
        owner.remove_listener('response', response_received)
        for popup in observed:
            popup.remove_listener('response', response_received)
