"""One automatic viewer download under native Chrome download behavior."""

import time
import uuid
from pathlib import Path

from playwright.sync_api import Error, TimeoutError

from .auto_click_diagnostic import pointer_click
from .browser import BrowserError
from .manual_checkpoint import result_pdf
from .manual_viewer_download import main as native_main
from .viewer_download_diagnostic import save_completed, viewer_control

SUCCESS = 'AUTO_VIEWER_DOWNLOAD_DEFAULT_BEHAVIOR_SUCCESS'
FAILED = 'AUTO_VIEWER_DOWNLOAD_DEFAULT_BEHAVIOR_FAILED'


def download_once(page, control, temporary, metadata, output):
    try:
        control.scroll_into_view_if_needed(timeout=5000)
        control.click(trial=True, timeout=5000)
        with page.expect_download(timeout=120000) as event:
            control.click(timeout=5000)
            print('IEEE_VIEWER_DOWNLOAD_DISPATCHED')
        download = event.value
        print('DOWNLOAD_RECEIVED')
        failure = download.failure()
        if failure:
            print('DOWNLOAD_CANCELED' if 'cancel' in failure.lower()
                  else 'DOWNLOAD_FAILED_UNCLASSIFIED')
            return False
        download.save_as(temporary)
        print('DOWNLOAD_COMPLETED_TEMPORARY')
        return save_completed(temporary, metadata, output)
    except TimeoutError:
        print('DOWNLOAD_ACTION_OR_EVENT_TIMEOUT')
        return False
    except (Error, OSError):
        print('DOWNLOAD_OR_SAVE_FAILED')
        return False


def checkpoint(context, scope, link, config, metadata):
    action = result_pdf(link)
    if action is None:
        print('AUTO_CLICK_TARGET_MISMATCH')
        print(FAILED)
        return
    status = pointer_click(action)
    print(status)
    if status != 'AUTO_LOCATOR_CLICK_DISPATCHED':
        print(FAILED)
        return
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        found = viewer_control(context)
        if found:
            print('IEEE_PDF_VIEWER_OPENED')
            print('VIEWER_DOWNLOAD_CONTROL_FOUND')
            directory = config.runtime / 'download-capture' / uuid.uuid4().hex
            directory.mkdir(parents=True)
            ok = download_once(found[0], found[1], directory / 'article.pdf',
                               metadata, Path('D:/文件'))
            print(SUCCESS if ok else FAILED)
            return
        live = [p for p in context.pages if not p.is_closed()]
        if not live:
            break
        live[-1].wait_for_timeout(250)
    print('PDF_VIEWER_DOWNLOAD_CONTROL_INACCESSIBLE')
    print(FAILED)


if __name__ == '__main__':
    try:
        native_main(result_checkpoint=checkpoint)
    except (Error, BrowserError, OSError, KeyboardInterrupt):
        print(FAILED)
