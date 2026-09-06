"""Local manual PDF-click ground truth; never automatically click a PDF."""

import re
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import Error

from .browser import persistent_browser
from .config import Config
from .publishers.ieee_cdp import CDPPDFObserver
from .publishers.ieee_pdf import location
from .publishers.ieee_target import canonical_article_id
from .resolver import resolve_metadata
from .uestc import enter_ieee, search_article
from .verify import verify_pdf

DOI = '10.1109/led.2024.3497584'
ARTICLE = '10752539'


def result_pdf(link):
    container = link.locator("xpath=ancestor::*[.//a[contains(@href, '/stamp/')]][1]")
    if container.count() != 1:
        return None
    identities = set()
    articles = container.locator("a[href*='/document/']")
    for i in range(min(articles.count(), 60)):
        number = canonical_article_id(articles.nth(i).get_attribute('href') or '')
        if number:
            identities.add(number)
    if identities != {ARTICLE}:
        return None
    links = container.locator("a[href*='/stamp/']")
    matches = [links.nth(i) for i in range(min(links.count(), 20))
               if canonical_article_id(links.nth(i).get_attribute('href') or '') == ARTICLE
               and links.nth(i).is_visible()]
    return matches[0] if len(matches) == 1 else None


def checkpoint(context, scope, link, metadata, config):
    action = result_pdf(link)
    if action is None:
        print('MANUAL_PDF_ICON_NOT_IDENTIFIED')
        hold(context)
        return None
    owner = scope if scope in context.pages else scope.page
    observer = CDPPDFObserver(context, owner, location)
    observers = [observer]

    def observe_popup(page):
        observers.append(CDPPDFObserver(context, page, location))

    context.on('page', observe_popup)
    action.scroll_into_view_if_needed(timeout=5000)
    action.evaluate("el => el.style.outline = '3px solid #16a34a'")
    owner.bring_to_front()
    print('MANUAL_PDF_GROUND_TRUTH_READY')
    print('Click the outlined PDF icon once. Browser remains open until you close it.')
    seen = set()
    viewer_seen = False
    verified = False
    result_reported = False
    try:
        while any(not p.is_closed() for p in context.pages):
            for index, page in enumerate(list(context.pages)):
                if page.is_closed():
                    continue
                for frame in [page] + [f for f in page.frames if f != page.main_frame]:
                    try:
                        signature = (index, frame.url, len(page.frames))
                        if signature not in seen:
                            seen.add(signature)
                            print(f'MANUAL_PAGE_TRANSITION: index={index}; {location(frame.url)}; '
                                  f'frame_count={len(page.frames)}')
                            if '/stamp/' in urlsplit(frame.url).path:
                                print('IEEE_STAMP_OPENED')
                        viewer = frame.locator("pdf-viewer, embed[type='application/pdf']")
                        if viewer.count() and not viewer_seen:
                            viewer_seen = True
                            print('IEEE_PDF_VIEWER_OPENED')
                        if any(o.seen for o in observers) or '/stamp/' in urlsplit(frame.url).path:
                            denied = frame.get_by_role('heading', name=re.compile(
                                r'^(purchase|subscription required|institutional sign.in|sign in)$',
                                re.I))
                            if denied.count() and denied.first.is_visible() and not result_reported:
                                print('MANUAL_PDF_ACCESS_FAILED')
                                result_reported = True
                    except Error:
                        continue
            for observed in observers:
                if observed.body is not None and not verified:
                    path = Path(config.runtime) / 'manual-candidate.part'
                    path.write_bytes(observed.body.data)
                    result = verify_pdf(path, DOI, metadata.title)
                    print(f'MANUAL_VERIFICATION: {result.status}; pages={result.pages}; '
                          f'size={result.size}; identity={result.identity}')
                    verified = result.valid and result.identity == 'MATCH'
                    if not verified:
                        path.unlink(missing_ok=True)
                        observed.body = None
            if viewer_seen and verified and not result_reported:
                print('MANUAL_PDF_VIEWER_SUCCESS')
                result_reported = True
            live = [p for p in context.pages if not p.is_closed()]
            if live:
                live[-1].wait_for_timeout(250)
    finally:
        context.remove_listener('page', observe_popup)
        for observed in observers:
            observed.close()


def hold(context):
    while any(not p.is_closed() for p in context.pages):
        live = [p for p in context.pages if not p.is_closed()]
        try:
            live[-1].wait_for_timeout(250)
        except Error:
            pass


def main():
    config = Config.load(None)
    metadata = resolve_metadata(DOI)
    with persistent_browser(config) as context:
        page, status = enter_ieee(context, 600)
        if page is None:
            print(status)
            hold(context)
            return
        search_article(page, DOI, metadata.title, ARTICLE, context=context,
                       on_result=lambda scope, link: checkpoint(
                           context, scope, link, metadata, config))
        hold(context)


if __name__ == '__main__':
    try:
        main()
    except (Error, OSError, KeyboardInterrupt):
        print('MANUAL_DIAGNOSTIC_STOPPED')
