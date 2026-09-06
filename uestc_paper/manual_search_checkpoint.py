"""Pause before any search input/submit for manual IEEE search ground truth."""

import re
import time

from playwright.sync_api import Error

from .browser import BrowserError
from .manual_viewer_download import main as native_main
from .uestc import is_ieee


def category(value):
    value = value or ''
    if re.search(r'within|in results|在.*结果', value, re.I):
        return 'WITHIN_RESULTS'
    if re.search(r'search|搜索', value, re.I):
        return 'SEARCH_SCOPE_UNCONFIRMED'
    return 'OTHER' if value else 'EMPTY'


def ready(context, _portal):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        for pi, page in enumerate(list(context.pages)):
            if page.is_closed():
                continue
            for fi, frame in enumerate(list(page.frames)):
                try:
                    if not is_ieee(frame, proxied=True):
                        continue
                    boxes = frame.get_by_role('searchbox')
                    visible = [i for i in range(boxes.count()) if boxes.nth(i).is_visible()
                               and boxes.nth(i).is_enabled()]
                    if not visible:
                        continue
                    print(f'MANUAL_SEARCH_PAGE: page_index={pi}; frame_index={fi}; '
                          f'searchbox_count={boxes.count()}; selected_index=NONE')
                    for i in visible:
                        box = boxes.nth(i)
                        value = box.input_value()
                        value = value if value.lower() in {'10.1109/led.2024.3497584',
                                                          '10752539', ''} else 'OTHER'
                        print(f'MANUAL_SEARCHBOX: index={i}; '
                              f'placeholder_category={category(box.get_attribute("placeholder"))}; '
                              f'aria_category={category(box.get_attribute("aria-label"))}; '
                              f'value_before_manual_input={value}')
                    page.bring_to_front()
                    print('MANUAL_IEEE_SEARCH_READY')
                    print('No automatic fill, submit, result click or PDF action will follow.')
                    return
                except Error:
                    continue
        live = [p for p in context.pages if not p.is_closed()]
        if not live:
            break
        live[-1].wait_for_timeout(250)
    print('MANUAL_SEARCH_PAGE_NOT_READY')


if __name__ == '__main__':
    try:
        native_main(portal_checkpoint=ready)
    except (Error, BrowserError, OSError, KeyboardInterrupt):
        print('MANUAL_SEARCH_DIAGNOSTIC_STOPPED')
