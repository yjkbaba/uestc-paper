"""Exact target-result PDF navigation, without article-page/global PDF selection."""

import time
from types import SimpleNamespace
from urllib.parse import urlsplit

from playwright.sync_api import Error

from .ieee_target import canonical_article_id


def result_pdf(link, article_id):
    if not article_id:
        return None
    container = link.locator("xpath=ancestor::*[.//a[contains(@href, '/stamp/')]][1]")
    if container.count() != 1:
        return None
    identities = set()
    articles = container.locator("a[href*='/document/']")
    for i in range(min(articles.count(), 60)):
        number = canonical_article_id(articles.nth(i).get_attribute('href') or '')
        if number:
            identities.add(number)
    if identities != {article_id}:
        return None
    links = container.locator("a[href*='/stamp/']")
    matches = [links.nth(i) for i in range(min(links.count(), 20))
               if canonical_article_id(links.nth(i).get_attribute('href') or '') == article_id
               and links.nth(i).is_visible()]
    return matches[0] if len(matches) == 1 and matches[0].is_enabled() else None


def open_result_pdf(context, scope, control, captured, seconds=120):
    # Reuse the already validated pointer action and frozen Viewer detection.
    from ..auto_click_diagnostic import pointer_click
    from ..viewer_download_diagnostic import viewer_control
    from ..uestc import is_webvpn_url
    owner = scope if scope in context.pages else scope.page
    before = list(context.pages)
    status = pointer_click(control)
    if status != 'AUTO_LOCATOR_CLICK_DISPATCHED':
        print('IEEE_TARGET_RESULT_PDF_CLICK_UNCONFIRMED')
        # No second click or article-detail retry after a possibly dispatched action.
    else:
        print('IEEE_TARGET_RESULT_PDF_CLICKED')
    started = time.monotonic()
    deadline = started + seconds
    stamp_seen = False
    viewer_frame_seen = False
    while time.monotonic() < deadline:
        pages = [p for p in context.pages if not p.is_closed()
                 and (p is owner or p not in before)]
        for page in pages:
            try:
                if urlsplit(page.url).hostname == 'ieeexplore.ieee.org':
                    return 'IEEE_PDF_PROXY_ESCAPE'
                if is_webvpn_url(page.url) and '/stamp/' in urlsplit(page.url).path:
                    if not stamp_seen:
                        print('IEEE_STAMP_OPENED')
                        stamp_seen = True
            except Error:
                continue
            # Refresh frame snapshots each poll; no Frame survives into the next poll.
            for frame in list(page.frames):
                try:
                    if is_webvpn_url(frame.url) and '/stamp/' in urlsplit(frame.url).path:
                        if not stamp_seen:
                            print('IEEE_STAMP_OPENED')
                            stamp_seen = True
                    if frame.locator('pdf-viewer').count() and not viewer_frame_seen:
                        print('IEEE_PDF_VIEWER_FRAME_OBSERVED')
                        viewer_frame_seen = True
                except Error:
                    continue
        # Exclude any pre-existing direct IEEE viewer from this result's evidence.
        if pages and viewer_control(SimpleNamespace(pages=pages)):
            print(f'IEEE_VIEWER_WAIT_SECONDS: {time.monotonic() - started:.2f}')
            print('IEEE_PDF_VIEWER_OPENED')
            return 'DOWNLOAD_RECEIVED' if captured else 'IEEE_PDF_VIEWER_OPENED'
        if captured:
            return 'DOWNLOAD_RECEIVED'
        if not pages:
            return 'IEEE_PAGE_CLOSED'
        try:
            pages[-1].wait_for_timeout(1000)
        except Error:
            continue  # Page/frame navigation race; next poll uses fresh context pages.
    print(f'IEEE_VIEWER_WAIT_SECONDS: {time.monotonic() - started:.2f}')
    return ('IEEE_PDF_VIEWER_NOT_READY' if stamp_seen or viewer_frame_seen
            else 'IEEE_PDF_VIEWER_TIMEOUT')
