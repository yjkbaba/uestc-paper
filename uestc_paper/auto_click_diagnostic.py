"""One local pointer-click experiment; no PDF replay or final-file saving."""

import time
from urllib.parse import urlsplit

from playwright.sync_api import Error

from .browser import persistent_browser
from .config import Config
from .manual_checkpoint import ARTICLE, DOI, hold, result_pdf
from .publishers.ieee_cdp import CDPPDFObserver
from .publishers.ieee_pdf import location
from .resolver import resolve_metadata
from .uestc import enter_ieee, search_article


def pointer_click(action):
    """Exactly one real click, after actionability and read-only hit testing."""
    try:
        action.scroll_into_view_if_needed(timeout=5000)
        action.hover(timeout=5000)
        action.click(trial=True, timeout=5000)
        box = action.bounding_box()
        visible, enabled = action.is_visible(), action.is_enabled()
        print(f'AUTO_ACTION: visible={visible}; enabled={enabled}; bbox={box is not None}')
        if not box or not visible or not enabled:
            return 'AUTO_CLICK_TARGET_MISMATCH'
        hit = action.evaluate('''el => {
            const r = el.getBoundingClientRect();
            const top = el.ownerDocument.elementFromPoint(r.x+r.width/2, r.y+r.height/2);
            return top === el || el.contains(top);
        }''')
        print(f'AUTO_HIT_TARGET: matches={bool(hit)}')
        if not hit:
            return 'AUTO_CLICK_TARGET_MISMATCH'
        # No force, JS click, navigation fallback, or second pointer attempt.
        action.click(timeout=5000)
        return 'AUTO_LOCATOR_CLICK_DISPATCHED'
    except Error:
        return 'AUTO_CLICK_TIMING_FAILURE'


def checkpoint(context, scope, link):
    action = result_pdf(link)
    if action is None:
        print('AUTO_CLICK_TARGET_MISMATCH')
        return
    container = link.locator("xpath=ancestor::*[.//a[contains(@href, '/stamp/')]][1]")
    candidates = container.locator("a[href*='/stamp/']")
    visible = sum(candidates.nth(i).is_visible() for i in range(candidates.count()))
    index = container.evaluate('el => Array.from(el.parentElement.children).indexOf(el)')
    print(f'AUTO_TARGET: result_sibling_index={index}; PDF_candidates={candidates.count()}; '
          f'visible_candidates={visible}; intended_visible_candidates=1')
    categories = action.evaluate('''el => ({
        tag: ['A','BUTTON'].includes(el.tagName) ? el.tagName : 'OTHER',
        role: ['link','button'].includes(el.getAttribute('role')) ? el.getAttribute('role') : 'OTHER',
        title: /pdf/i.test(el.getAttribute('title') || '') ? 'PDF' : 'OTHER',
        aria: /pdf/i.test(el.getAttribute('aria-label') || '') ? 'PDF' : 'OTHER'
    })''')
    print(f'AUTO_CONTROL: {categories}; {location(action.get_attribute("href") or "")}')
    owner = scope if scope in context.pages else scope.page
    observers = [CDPPDFObserver(context, owner, location)]

    def attach(page):
        observers.append(CDPPDFObserver(context, page, location))

    context.on('page', attach)
    try:
        owner.bring_to_front()
        status = pointer_click(action)
        print(status)
        if status != 'AUTO_LOCATOR_CLICK_DISPATCHED':
            return
        deadline = time.monotonic() + 90
        seen = set()
        viewer_seen = False
        while time.monotonic() < deadline:
            live = [p for p in context.pages if not p.is_closed()]
            if not live:
                break
            for index, page in enumerate(live):
                for frame in [page] + [f for f in page.frames if f != page.main_frame]:
                    try:
                        key = (index, location(frame.url), len(page.frames))
                        if key not in seen:
                            seen.add(key)
                            print(f'AUTO_TRANSITION: index={index}; {key[1]}; frames={key[2]}')
                            if '/stamp/' in urlsplit(frame.url).path:
                                print('IEEE_STAMP_OPENED')
                        if frame.locator("pdf-viewer, embed[type='application/pdf']").count():
                            if not viewer_seen:
                                viewer_seen = True
                                print('IEEE_PDF_VIEWER_OPENED')
                                print('AUTO_VIEWER_FULL_PAPER_CONFIRMATION_PENDING')
                    except Error:
                        continue
            live[-1].wait_for_timeout(250)
        print('AUTO_OBSERVATION_COMPLETE')
        if not viewer_seen:
            print('AUTO_CLICK_TIMING_FAILURE: viewer_not_observed; cause_unconfirmed')
        # Keep the visible result and passive observers alive for human inspection.
        # A viewer element alone does not establish that the complete paper rendered.
        hold(context)
    finally:
        context.remove_listener('page', attach)
        for observer in observers:
            observer.close()


def main():
    config = Config.load(None)
    metadata = resolve_metadata(DOI)
    with persistent_browser(config) as context:
        page, status = enter_ieee(context, 600)
        if page is None:
            print(status)
        else:
            search_article(page, DOI, metadata.title, ARTICLE, context=context,
                           on_result=lambda scope, link: checkpoint(context, scope, link))
        hold(context)


if __name__ == '__main__':
    try:
        main()
    except (Error, OSError, KeyboardInterrupt):
        print('AUTO_DIAGNOSTIC_STOPPED')
