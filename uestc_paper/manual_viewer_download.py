"""One manual viewer download with native Chrome download behavior preserved."""

import os
import subprocess
import time

from playwright.sync_api import Error, sync_playwright

from .auto_click_diagnostic import pointer_click
from .browser import BrowserError, browser_choice, configure_download_preferences
from .config import Config
from .manual_checkpoint import ARTICLE, DOI, hold, result_pdf
from .resolver import resolve_metadata
from .uestc import enter_ieee, search_article
from .viewer_download_diagnostic import viewer_control


def checkpoint(context, scope, link):
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
            print('MANUAL_VIEWER_DOWNLOAD_READY')
            print('Confirm full paper rendering, then manually click Download exactly once.')
            print('Report completed or failed; a downloaded file still requires offline verification.')
            # No toolbar action, CDP download manager, or network-body observer.
            hold(context)
            return
        live = [p for p in context.pages if not p.is_closed()]
        if not live:
            return
        live[-1].wait_for_timeout(250)
    print('MANUAL_VIEWER_NOT_READY')


def main(result_checkpoint=None, portal_checkpoint=None):
    if os.environ.get('DEBUG') or os.environ.get('PWDEBUG'):
        raise BrowserError('DEBUG_LOGGING_DISABLED')
    config = Config.load(None)
    metadata = resolve_metadata(DOI)
    lock = config.runtime / 'browser.lock'
    with lock.open('x') as handle:
        try:
            with sync_playwright() as playwright:
                _, executable = browser_choice(playwright)
                if executable is None:
                    raise BrowserError('BROWSER_MISSING')
                configure_download_preferences(config)
                port_file = config.profile / 'DevToolsActivePort'
                previous = port_file.stat().st_mtime_ns if port_file.exists() else None
                # Keep the existing profile/preferences intact. The debug endpoint is local only.
                process = subprocess.Popen([
                    str(executable), '--user-data-dir=' + str(config.profile),
                    '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0',
                    'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                deadline = time.monotonic() + 30
                port = None
                while time.monotonic() < deadline and process.poll() is None:
                    if port_file.exists() and port_file.stat().st_mtime_ns != previous:
                        lines = port_file.read_text(encoding='utf-8').splitlines()
                        if lines and lines[0].isdigit():
                            port = int(lines[0])
                            break
                    time.sleep(0.1)
                if port is None:
                    raise BrowserError('NATIVE_BROWSER_ATTACH_UNAVAILABLE')
                browser = playwright.chromium.connect_over_cdp(
                    f'http://127.0.0.1:{port}', no_defaults=True)
                context = browser.contexts[0]
                print('NATIVE_DOWNLOAD_BEHAVIOR: no_defaults=True; no custom download manager')
                page, status = enter_ieee(context, 600)
                if page is None:
                    print(status)
                elif portal_checkpoint is not None:
                    portal_checkpoint(context, page)
                else:
                    search_article(page, DOI, metadata.title, ARTICLE, context=context,
                                   on_result=lambda scope, link: (
                                       result_checkpoint(context, scope, link, config, metadata)
                                       if result_checkpoint else checkpoint(context, scope, link)))
                hold(context)
        finally:
            handle.close()
            lock.unlink(missing_ok=True)


if __name__ == '__main__':
    try:
        main()
    except (Error, BrowserError, OSError, KeyboardInterrupt):
        print('MANUAL_VIEWER_DIAGNOSTIC_STOPPED')
