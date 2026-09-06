"""One viewer click with passive evidence after timeout; no download overrides."""

import json
import shutil
import time
import uuid
from pathlib import Path

from playwright.sync_api import Error, TimeoutError

from .viewer_download_diagnostic import save_completed


class Files:
    def __init__(self, directories):
        self.directories = set(directories)
        self.before = self.snapshot()
        self.changed = {}

    def snapshot(self):
        found = {}
        for directory in self.directories:
            if not directory.is_dir():
                continue
            for p in directory.iterdir():
                if p.suffix.lower() not in {'.pdf', '.crdownload', '.jsp'}:
                    continue
                try:
                    if p.is_file():
                        s = p.stat()
                        found[p] = (s.st_size, s.st_mtime_ns)
                except OSError:
                    continue
        return found

    def poll(self):
        for p, fingerprint in self.snapshot().items():
            if fingerprint != self.before.get(p) and fingerprint != self.changed.get(p):
                self.changed[p] = fingerprint
                print(f'DOWNLOAD_FILE_EVIDENCE: extension={p.suffix.lower()}; '
                      f'bytes={fingerprint[0]}')


class Monitor:
    def __init__(self, context, page, directories):
        self.context = context
        self.files = Files(directories)
        self.downloads, self.attached, self.guids = [], [], set()
        self.cdp_evidence = False
        self.session = (context.browser.new_browser_cdp_session() if context.browser
                        else context.new_cdp_session(page))
        self.session.on('Browser.downloadWillBegin', self.begin)
        self.session.on('Browser.downloadProgress', self.progress)
        for p in context.pages:
            self.attach(p)
        context.on('page', self.attach)
        print('PASSIVE_DOWNLOAD_OBSERVERS_READY: Playwright; Browser_events; filesystem')

    def attach(self, page):
        page.on('download', self.receive)
        self.attached.append(page)

    def receive(self, download):
        self.downloads.append(download)
        print('PLAYWRIGHT_DOWNLOAD_OBSERVED')

    def begin(self, event):
        self.guids.add(event.get('guid'))
        self.cdp_evidence = True
        print('BROWSER_DOWNLOAD_WILL_BEGIN')

    def progress(self, event):
        if event.get('guid') not in self.guids:
            return
        self.cdp_evidence = True
        state = event.get('state')
        state = state if state in {'inProgress', 'completed', 'canceled'} else 'OTHER'
        sizes = [event.get(k) for k in ('receivedBytes', 'totalBytes')]
        sizes = [s if isinstance(s, (int, float)) and s >= 0 else None for s in sizes]
        print(f'BROWSER_DOWNLOAD_PROGRESS: state={state}; receivedBytes={sizes[0]}; '
              f'totalBytes={sizes[1]}')

    @property
    def evidence(self):
        return bool(self.downloads or self.cdp_evidence or self.files.changed)

    def close(self):
        self.context.remove_listener('page', self.attach)
        for p in self.attached:
            p.remove_listener('download', self.receive)
        self.session.remove_listener('Browser.downloadWillBegin', self.begin)
        self.session.remove_listener('Browser.downloadProgress', self.progress)
        self.session.detach()


def click_and_observe(control, monitor, pump, seconds=30, clock=time.monotonic):
    unconfirmed = False
    try:
        # One normal pointer call; no trial click obscuring which call timed out.
        control.click(timeout=5000)
        print('VIEWER_DOWNLOAD_CLICK_CONFIRMED')
    except TimeoutError:
        unconfirmed = True
        print('VIEWER_DOWNLOAD_CLICK_UNCONFIRMED')
    except Error:
        unconfirmed = True
        print('VIEWER_DOWNLOAD_CLICK_UNCONFIRMED: browser_action_error')
    deadline = clock() + seconds
    while clock() < deadline:
        monitor.files.poll()
        pump()
    monitor.files.poll()
    if unconfirmed:
        state = ('VIEWER_DOWNLOAD_CLICK_DISPATCHED_AFTER_TIMEOUT' if monitor.evidence
                 else 'VIEWER_DOWNLOAD_CLICK_NOT_CONFIRMED')
    else:
        state = ('VIEWER_DOWNLOAD_EVIDENCE_OBSERVED' if monitor.evidence
                 else 'VIEWER_DOWNLOAD_NO_EVIDENCE')
    print(state)
    return state


def run(context, page, control, config, metadata, output):
    directories = {Path.home() / 'Downloads', output, config.runtime}
    preferences = config.profile / 'Default' / 'Preferences'
    if preferences.is_file():
        # Read only the configured download directory; never log profile contents.
        directory = json.loads(preferences.read_text(encoding='utf-8')).get(
            'download', {}).get('default_directory')
        if directory:
            directories.add(Path(directory))
    print(f'DOWNLOAD_DIRECTORIES_OBSERVED: count={len(directories)}')
    monitor = Monitor(context, page, directories)
    try:
        def pump():
            live = [p for p in context.pages if not p.is_closed()]
            if live:
                live[-1].wait_for_timeout(250)
            else:
                time.sleep(0.25)

        state = click_and_observe(control, monitor, pump)
        if not monitor.evidence:
            return state
        # Only new/changed files, never the previously verified manual download.
        # Retain originals; the existing verifier decides whether content is valid.
        deadline = time.monotonic() + 90
        checked = set()
        while time.monotonic() < deadline:
            monitor.files.poll()
            for source, fingerprint in list(monitor.files.changed.items()):
                if source.suffix.lower() == '.crdownload' or (source, fingerprint) in checked:
                    continue
                if not source.is_file():
                    continue
                checked.add((source, fingerprint))
                directory = config.runtime / 'download-capture' / uuid.uuid4().hex
                directory.mkdir(parents=True)
                temporary = directory / 'candidate.pdf'
                shutil.copyfile(source, temporary)
                if save_completed(temporary, metadata, output):
                    return state
            pump()
        print('NO_VERIFIED_COMPLETED_FILE_OBSERVED')
        return state
    finally:
        monitor.close()
