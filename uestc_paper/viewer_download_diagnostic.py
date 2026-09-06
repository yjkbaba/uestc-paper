"""Single standard Chromium viewer download, with verified final output only."""

import re
import time
import uuid
from pathlib import Path
from types import SimpleNamespace

from playwright.sync_api import Error

from .auto_click_diagnostic import pointer_click
from .browser import BrowserError, persistent_browser
from .config import Config
from .manual_checkpoint import ARTICLE, DOI, hold, result_pdf
from .publishers.ieee_download_manager import DownloadManager
from .resolver import resolve_metadata
from .uestc import enter_ieee, search_article
from .workflow import _save_verified
from .viewer_controls import evidence as control_evidence, select_candidate

DOWNLOAD_NAME = re.compile(r'^(download|下载|save|保存)(\s.*)?$', re.I)


class ViewerDownloadManager(DownloadManager):
    """The first download after the isolated viewer action; never request its URL."""

    def begin(self, event):
        if self.url is None:
            self.url = event.get('url')
        super().begin(event)


def viewer_control(context):
    all_matches, records = [], []
    for index, page in enumerate(list(context.pages)):
        if page.is_closed():
            continue
        for frame_index, frame in enumerate(list(page.frames)):
            try:
                viewer = frame.locator('pdf-viewer')
                if not viewer.count():
                    continue
                # Role selectors pierce open shadow roots, without accessing closed roots.
                controls = viewer.get_by_role('button', name=DOWNLOAD_NAME)
                matches = [controls.nth(i) for i in range(controls.count())
                           if controls.nth(i).is_visible() and controls.nth(i).is_enabled()]
                print(f'VIEWER_TOOLBAR: page_index={index}; viewer=True; '
                      f'visible_download_controls={len(matches)}')
                for candidate_index, control in enumerate(matches):
                    records.append(control_evidence(control, candidate_index, index, frame_index))
                    all_matches.append((page, control))
            except Error:
                continue
    selected = select_candidate(records)
    if selected is not None:
        print(f'VIEWER_DOWNLOAD_SELECTED: candidate={selected}; rule=MAIN_TOOLBAR_DOWNLOAD')
        return all_matches[selected]
    if records:
        print('VIEWER_DOWNLOAD_AMBIGUOUS')
    return None


def save_completed(path, metadata, output):
    # Existing verifier and exclusive-file saving remain the final gate.
    output.mkdir(parents=True, exist_ok=True)
    if _save_verified(path, metadata, SimpleNamespace(downloads=output),
                      'UESTC / IEEE / Chromium viewer download'):
        print('PDF_VERIFIED')
        print('E2E_SUCCESS')
        return True
    print('PDF_VERIFICATION_FAILED')
    return False


def download_once(context, page, control, config, metadata, output):
    directory = config.runtime / 'download-capture' / uuid.uuid4().hex
    session = context.new_cdp_session(page)
    manager = ViewerDownloadManager(context, session, directory)
    captured, attached = [], []

    def attach(p):
        def receive(download):
            captured.append(download)
            print('DOWNLOAD_RECEIVED: source=Playwright')
        p.on('download', receive)
        attached.append((p, receive))

    for p in context.pages:
        attach(p)
    context.on('page', attach)
    try:
        control.scroll_into_view_if_needed(timeout=5000)
        control.click(trial=True, timeout=5000)
        # Exactly one actual download action. No request replay or secondary save action.
        control.click(timeout=5000)
        print('IEEE_VIEWER_DOWNLOAD_DISPATCHED')
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            if manager.body is not None:
                print('DOWNLOAD_RECEIVED: source=Browser; state=completed')
                return save_completed(directory / manager.guid, metadata, output)
            if manager.failure:
                print(manager.failure)
                return False
            if captured:
                download = captured[0]
                failure = download.failure()
                if failure:
                    category = ('DOWNLOAD_CANCELED' if 'cancel' in failure.lower()
                                else 'DOWNLOAD_NETWORK_FAILED')
                    print(category)
                    return False
                temporary = directory / 'viewer-download.part'
                download.save_as(temporary)
                print('VIEWER_DOWNLOAD_COMPLETED')
                return save_completed(temporary, metadata, output)
            page.wait_for_timeout(250)
        print('VIEWER_DOWNLOAD_TIMEOUT')
        return False
    except Error:
        print('VIEWER_DOWNLOAD_ACTION_FAILED')
        return False
    finally:
        context.remove_listener('page', attach)
        for p, handler in attached:
            p.remove_listener('download', handler)
        manager.close()
        session.detach()


def checkpoint(context, scope, link, config, metadata, output):
    action = result_pdf(link)
    if action is None:
        print('AUTO_CLICK_TARGET_MISMATCH')
        return
    status = pointer_click(action)
    print(status)
    if status != 'AUTO_LOCATOR_CLICK_DISPATCHED':
        return
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        found = viewer_control(context)
        if found:
            print('IEEE_PDF_VIEWER_OPENED')
            print('VIEWER_DOWNLOAD_CONTROL_FOUND')
            download_once(context, found[0], found[1], config, metadata, output)
            return
        live = [p for p in context.pages if not p.is_closed()]
        if not live:
            break
        live[-1].wait_for_timeout(250)
    print('PDF_VIEWER_DOWNLOAD_CONTROL_INACCESSIBLE')


def main():
    config = Config.load(None)
    metadata = resolve_metadata(DOI)
    output = Path('D:/文件')
    with persistent_browser(config) as context:
        page, status = enter_ieee(context, 600)
        if page is None:
            print(status)
        else:
            search_article(page, DOI, metadata.title, ARTICLE, context=context,
                           on_result=lambda scope, link: checkpoint(
                               context, scope, link, config, metadata, output))
        hold(context)


if __name__ == '__main__':
    try:
        main()
    except (Error, BrowserError, OSError, KeyboardInterrupt):
        print('VIEWER_DIAGNOSTIC_STOPPED')
