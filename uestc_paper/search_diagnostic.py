"""Single proxied IEEE search experiment; never click a result."""

import re
import time

from playwright.sync_api import Error

from .manual_search_checkpoint import category
from .publishers.ieee_target import canonical_article_id
from .uestc import is_ieee

DOI = '10.1109/LED.2024.3497584'
ARTICLE = '10752539'


def select_main(records):
    selected = [i for i, d in enumerate(records) if d['visible'] and d['enabled']
                and d['search_type'] and d['in_form'] and not d['within']]
    return selected[0] if len(selected) == 1 else None


def scopes(context):
    for pi, page in enumerate(list(context.pages)):
        if page.is_closed():
            continue
        for fi, frame in enumerate(list(page.frames)):
            try:
                if is_ieee(frame, proxied=True):
                    yield pi, fi, page, frame
            except Error:
                continue


def matches(frame):
    links = frame.locator("a[href*='/document/'], a[href*='arnumber=']")
    return sum(links.nth(i).is_visible() and canonical_article_id(
        links.nth(i).get_attribute('href') or '') == ARTICLE
        for i in range(min(links.count(), 100)))


def run(context):
    records, controls = [], []
    for pi, fi, page, frame in scopes(context):
        inputs = frame.locator("input[type='search'], input[type='text'], input:not([type])")
        for i in range(inputs.count()):
            box = inputs.nth(i)
            if not box.is_visible():
                continue
            placeholder = category(box.get_attribute('placeholder'))
            aria = category(box.get_attribute('aria-label'))
            structure = box.evaluate('''el => ({search_type:el.type==='search',
                in_form:!!el.closest('form'), within:!!el.closest('xpl-search-within-migr')})''')
            structure['within'] |= 'WITHIN_RESULTS' in (placeholder, aria)
            record = dict(structure, visible=True, enabled=box.is_enabled())
            records.append(record)
            controls.append((page, frame, box, pi, fi, i))
            print(f'SEARCH_INPUT: index={i}; frame_index={fi}; page_index={pi}; '
                  f'placeholder_category={placeholder}; aria_category={aria}; '
                  f'bounding_box={box.bounding_box()}; visible=True; enabled={record["enabled"]}; '
                  f'scope_category={"WITHIN_RESULTS" if record["within"] else "FORM_SEARCH" if record["search_type"] and record["in_form"] else "OTHER"}')
    selected = select_main(records)
    if selected is None:
        print('IEEE_MAIN_SEARCH_AMBIGUOUS')
        return
    page, frame, box, pi, fi, i = controls[selected]
    print(f'SEARCHBOX_SELECTED: index={i}; frame_index={fi}; page_index={pi}; '
          'rule=UNIQUE_FORM_SEARCH_OUTSIDE_WITHIN_RESULTS')
    before = box.input_value()
    print('SEARCH_VALUE_BEFORE: ' + (before if before in {DOI, ARTICLE, ''} else 'OTHER'))
    try:
        box.fill(DOI, timeout=5000)
        after = box.input_value()
        print('SEARCH_VALUE_AFTER: ' + (after if after == DOI else 'EMPTY' if not after else 'OTHER'))
        if after != DOI:
            print('IEEE_SEARCH_FILL_FAILED')
            return
    except Error:
        print('IEEE_SEARCH_FILL_FAILED')
        return
    print('SEARCH_VALUE_CONFIRMED')
    baseline = matches(frame)
    print(f'SEARCH_BASELINE: matching_arnumber_links={baseline}')
    form = box.locator('xpath=ancestor::form[1]')
    buttons = form.get_by_role('button', name=re.compile(r'^search$', re.I))
    visible = [buttons.nth(j) for j in range(buttons.count())
               if buttons.nth(j).is_visible() and buttons.nth(j).is_enabled()]
    method = 'BUTTON' if len(visible) == 1 else 'ENTER'
    print(f'SEARCH_SUBMIT_METHOD: {method}')
    navigated = [False]
    def navigation(_frame):
        navigated[0] = True
    page.on('framenavigated', navigation)
    try:
        try:
            if method == 'BUTTON':
                visible[0].click(timeout=5000)
            else:
                box.press('Enter', timeout=5000)
            print('IEEE_SEARCH_SUBMIT_DISPATCHED')
        except Error:
            print('IEEE_SEARCH_SUBMIT_UNCONFIRMED')
        deadline = time.monotonic() + 60
        loading_seen = False
        previous = None
        while time.monotonic() < deadline:
            for pi, fi, _, current in scopes(context):
                try:
                    count = matches(current)
                    loading_controls = current.locator('[role="progressbar"], [aria-busy="true"]')
                    loading = any(loading_controls.nth(j).is_visible()
                                  for j in range(loading_controls.count()))
                    loading_seen |= loading
                    zeros = current.get_by_text(re.compile(r'^No (?:search )?results(?: found)?[.!]?$', re.I))
                    zero = any(zeros.nth(j).is_visible() for j in range(zeros.count()))
                    cards = current.locator('xpl-results-item').count()
                    evidence = (pi, fi, navigated[0], loading_seen, loading_seen and not loading,
                                zero, cards, count)
                    if evidence != previous:
                        print(f'SEARCH_OBSERVATION: page_index={pi}; frame_index={fi}; '
                              f'navigation={navigated[0]}; loading_appeared={loading_seen}; '
                              f'loading_cleared={loading_seen and not loading}; zero_result={zero}; '
                              f'result_card_count={cards}; matching_arnumber_links={count}')
                        previous = evidence
                    if count:
                        print('IEEE_TARGET_RESULT_FOUND')
                        return
                    if zero and loading_seen and not loading:
                        print('IEEE_SEARCH_NO_RESULT')
                        return
                except Error:
                    continue
            live = [p for p in context.pages if not p.is_closed()]
            if not live:
                break
            live[-1].wait_for_timeout(250)
        print('IEEE_SEARCH_OBSERVATION_INCONCLUSIVE')
    finally:
        page.remove_listener('framenavigated', navigation)
