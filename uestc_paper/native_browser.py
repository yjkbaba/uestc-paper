"""Visible dedicated Chromium, preserving Chrome's native download behavior."""

import os
import subprocess
import time
from contextlib import contextmanager

from playwright.sync_api import Error, sync_playwright

from .browser import BrowserError, _disable_password_saving, browser_choice


@contextmanager
def persistent_browser(config):
    if os.environ.get('DEBUG') or os.environ.get('PWDEBUG'):
        raise BrowserError('DEBUG_LOGGING_DISABLED')
    config.setup()
    lock = config.runtime / 'browser.lock'
    try:
        handle = lock.open('x')
    except FileExistsError:
        raise BrowserError('PROFILE_IN_USE') from None
    process = None
    try:
        with handle, sync_playwright() as playwright:
            _, executable = browser_choice(playwright)
            if executable is None:
                raise BrowserError('BROWSER_MISSING')
            _disable_password_saving(config)
            port_file = config.profile / 'DevToolsActivePort'
            previous = port_file.stat().st_mtime_ns if port_file.exists() else None
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
                time.sleep(.1)
            if port is None:
                raise BrowserError('NATIVE_BROWSER_ATTACH_UNAVAILABLE')
            # accept_downloads=True on a launched context forces allowAndName internally.
            # no_defaults leaves downloads accepted by Chrome's own configured behavior.
            browser = playwright.chromium.connect_over_cdp(
                f'http://127.0.0.1:{port}', no_defaults=True,
                artifacts_dir=str(config.runtime / 'download-capture'))
            print('NATIVE_DOWNLOAD_BEHAVIOR: Chrome default; no download override')
            try:
                yield browser.contexts[0]
            finally:
                session = browser.new_browser_cdp_session()
                try:
                    session.send('Browser.close')
                except Error:
                    pass
    except Error:
        raise BrowserError('BROWSER_ACTION_FAILED') from None
    finally:
        if process is not None:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=10)
        handle.close()
        lock.unlink(missing_ok=True)
