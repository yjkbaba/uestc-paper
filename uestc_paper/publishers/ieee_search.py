"""Production IEEE search using the manually validated main-form submission."""

import re
import time

from playwright.sync_api import Error

from .ieee_target import TargetResult, canonical_article_id


def _scopes(context):
    from ..uestc import is_ieee
    for pi, page in enumerate(list(context.pages)):
        if page.is_closed():
            continue
        # Include Page for existing adapters, plus refreshed child frames.
        for fi, scope in enumerate([page] + [f for f in page.frames if f != page.main_frame]):
            try:
                if is_ieee(scope, proxied=True):
                    yield pi, fi, page, scope
            except Error:
                continue


def _main_inputs(scopes):
    candidates = []
    for pi, fi, owner, scope in scopes:
        try:
            inputs = scope.locator("input[type='search'], input[type='text'], input:not([type])")
            for i in range(inputs.count()):
                box = inputs.nth(i)
                if not box.is_visible() or not box.is_enabled():
                    continue
                structure = box.evaluate('''el => ({search_type:el.type==='search',
                    in_form:!!el.closest('form'), within:!!el.closest('xpl-search-within-migr')})''')
                labels = ' '.join(box.get_attribute(k) or '' for k in ('placeholder', 'aria-label'))
                within = structure['within'] or bool(re.search(r'within|in results|在.*结果', labels, re.I))
                if structure['search_type'] and structure['in_form'] and not within:
                    candidates.append((pi, fi, i, owner, box))
        except Error:
            continue
    return candidates


def search_article(page, doi, title, article_id, timeout=60, context=None, on_result=None):
    from ..uestc import is_ieee
    if not is_ieee(page, proxied=True):
        return TargetResult('IEEE_SEARCH_CONTROL_NOT_FOUND')
    owner = page if hasattr(page, 'frames') else page.page
    context = context or owner.context
    # DOI identity is case-insensitive; reproduce the successful IEEE query spelling.
    query = doi.upper()
    deadline = time.monotonic() + timeout
    submitted = False
    clicked = False
    navigation_seen = [False]
    attached = []
    loading_seen = set()
    zero_since = None
    last_counts = None

    def navigation(_frame):
        navigation_seen[0] = True

    try:
        while time.monotonic() < deadline:
            current = list(_scopes(context))
            matches = []
            finished_zero = False
            cards = 0
            for pi, fi, owner, scope in current:
                try:
                    if article_id and canonical_article_id(scope.url) == article_id:
                        print('IEEE_TARGET_ARTICLE_OPENED')
                        return TargetResult('IEEE_TARGET_ARTICLE_OPENED', scope)
                    links = scope.locator("a[href*='/document/'], a[href*='arnumber=']")
                    for i in range(min(links.count(), 100)):
                        link = links.nth(i)
                        if article_id and canonical_article_id(link.get_attribute('href') or '') == article_id and link.is_visible():
                            matches.append((scope, link))
                    cards += scope.locator('xpl-results-item').count()
                    if submitted:
                        indicators = scope.locator('[role="progressbar"], [aria-busy="true"]')
                        loading = any(indicators.nth(i).is_visible() for i in range(indicators.count()))
                        if loading:
                            loading_seen.add((pi, fi))
                        zeros = scope.get_by_text(re.compile(r'^No (?:search )?results(?: found)?[.!]?$', re.I))
                        zero = any(zeros.nth(i).is_visible() for i in range(zeros.count()))
                        complete = not loading and ((pi, fi) in loading_seen or
                            (navigation_seen[0] and scope.evaluate('document.readyState') == 'complete'))
                        finished_zero |= zero and complete
                except Error:
                    continue
            counts = (cards, len(matches))
            if counts != last_counts:
                print(f'IEEE_SEARCH_RESULTS: result_card_count={cards}; matching_arnumber_links={len(matches)}')
                last_counts = counts
            # Target evidence across all current scopes always takes precedence over zero UI.
            if matches and not clicked:
                scope, link = matches[0]
                print('IEEE_TARGET_RESULT_FOUND')
                if on_result is not None:
                    return on_result(scope, link)
                # Preserve the existing result-click continuation, without changing PDF logic.
                link.click(timeout=5000)
                clicked = True
            elif submitted and not clicked:
                if finished_zero:
                    zero_since = zero_since or time.monotonic()
                    if time.monotonic() - zero_since >= 0.5:
                        print('IEEE_SEARCH_NO_RESULT')
                        return TargetResult('IEEE_SEARCH_NO_RESULT')
                else:
                    zero_since = None
            if not submitted and not clicked:
                inputs = _main_inputs(current)
                if len(inputs) > 1:
                    return TargetResult('IEEE_MAIN_SEARCH_AMBIGUOUS')
                if len(inputs) == 1:
                    pi, fi, index, owner, box = inputs[0]
                    print(f'SEARCHBOX_SELECTED: page_index={pi}; frame_index={fi}; index={index}; '
                          'rule=UNIQUE_FORM_SEARCH_OUTSIDE_WITHIN_RESULTS')
                    try:
                        box.fill(query, timeout=5000)
                        if box.input_value() != query:
                            return TargetResult('IEEE_SEARCH_FILL_FAILED')
                    except Error:
                        return TargetResult('IEEE_SEARCH_FILL_FAILED')
                    print(f'SEARCH_VALUE_CONFIRMED: {query}')
                    form = box.locator('xpath=ancestor::form[1]')
                    buttons = form.get_by_role('button', name=re.compile(r'^search$', re.I))
                    buttons = [buttons.nth(i) for i in range(buttons.count())
                               if buttons.nth(i).is_visible() and buttons.nth(i).is_enabled()]
                    if len(buttons) != 1:
                        return TargetResult('IEEE_SEARCH_BUTTON_NOT_UNIQUE')
                    try:
                        bounds = buttons[0].bounding_box()
                    except Error:
                        bounds = None
                    valid_box = bool(bounds and bounds['width'] > 0 and bounds['height'] > 0)
                    print(f'IEEE_SEARCH_BUTTON: associated_visible_enabled_count=1; '
                          f'bounding_box_valid={valid_box}')
                    if not valid_box:
                        return TargetResult('IEEE_SEARCH_BUTTON_NOT_ACTIONABLE')
                    try:
                        hit = buttons[0].evaluate('''el => {
                            const r = el.getBoundingClientRect();
                            const top = el.ownerDocument.elementFromPoint(
                                r.x+r.width/2, r.y+r.height/2);
                            return top === el || el.contains(top);
                        }''')
                    except Error:
                        hit = False
                    print(f'IEEE_SEARCH_MOUSE_HITTEST: passed={bool(hit)}')
                    if not hit:
                        return TargetResult('IEEE_SEARCH_MOUSE_HITTEST_FAILED')
                    print(f'IEEE_SEARCH_PRE_SUBMIT: matching_target_links={len(matches)}')
                    owner.on('framenavigated', navigation)
                    attached.append(owner)
                    submitted = True  # Never retry a possibly dispatched submission.
                    print('SEARCH_SUBMIT_METHOD: BUTTON')
                    try:
                        owner.mouse.move(bounds['x'] + bounds['width']/2,
                                         bounds['y'] + bounds['height']/2)
                        owner.mouse.down()
                        owner.mouse.up()
                        print('IEEE_SEARCH_MOUSE_DISPATCHED')
                    except Error:
                        print('IEEE_SEARCH_SUBMIT_UNCONFIRMED')
                    deadline = time.monotonic() + timeout
            live = [p for p in context.pages if not p.is_closed()]
            if not live:
                break
            live[-1].wait_for_timeout(1000)
        status = ('IEEE_TARGET_ARTICLE_UNCONFIRMED' if clicked else
                  'IEEE_SEARCH_OBSERVATION_INCONCLUSIVE' if submitted else
                  'IEEE_SEARCH_CONTROL_NOT_FOUND')
        print(status)
        return TargetResult(status)
    finally:
        for owner in attached:
            owner.remove_listener('framenavigated', navigation)
