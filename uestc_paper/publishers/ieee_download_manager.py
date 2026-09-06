"""Browser download evidence correlated with the first observed PDF response."""

import re
from pathlib import Path

from playwright.sync_api import Error

from ..http import MAX_PDF_BYTES
from .ieee_response import PDFBody


class DownloadManager:
    def __init__(self, context, page_session, directory):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.session = (context.browser.new_browser_cdp_session() if context.browser
                        else page_session)
        self.owns_session = self.session is not page_session
        self.url = None
        self.guid = None
        self.pending = []
        self.progress = {}
        self.failure = None
        self.body = None
        self.session.on('Browser.downloadWillBegin', self.begin)
        self.session.on('Browser.downloadProgress', self.update)
        self.session.send('Browser.setDownloadBehavior', {
            'behavior': 'allowAndName', 'downloadPath': str(self.directory), 'eventsEnabled': True})
        print('IEEE_BROWSER_DOWNLOAD_MONITOR_READY')

    def select(self, url):
        self.url = url
        for event in self.pending:
            self.begin(event)
        self.pending.clear()

    def begin(self, event):
        if self.url is None:
            self.pending.append(event)
            return
        if self.guid is not None or event.get('url') != self.url:
            return
        guid = event.get('guid', '')
        if not re.fullmatch(r'[a-zA-Z0-9-]{1,80}', guid):
            self.failure = 'IEEE_DOWNLOAD_IDENTIFIER_INVALID'
            return
        self.guid = guid
        print('IEEE_BROWSER_DOWNLOAD_WILL_BEGIN')
        if guid in self.progress:
            self.update(self.progress[guid])

    def update(self, event):
        guid = event.get('guid')
        self.progress[guid] = event
        if guid != self.guid or self.guid is None:
            return
        state = event.get('state')
        state = state if state in {'inProgress', 'completed', 'canceled', 'interrupted'} else 'OTHER'
        sizes = [event.get(key) for key in ('receivedBytes', 'totalBytes')]
        sizes = [value if isinstance(value, (int, float)) and value >= 0 else None for value in sizes]
        print(f'IEEE_BROWSER_DOWNLOAD_PROGRESS: state={state}; receivedBytes={sizes[0]}; '
              f'totalBytes={sizes[1]}')
        if state in {'canceled', 'interrupted'}:
            self.failure = 'DOWNLOAD_CANCELED' if state == 'canceled' else 'DOWNLOAD_NETWORK_FAILED'
        elif state == 'completed':
            path = (self.directory / self.guid).resolve()
            if path.parent != self.directory or not path.is_file():
                self.failure = 'IEEE_COMPLETED_DOWNLOAD_FILE_MISSING'
            elif not 0 < path.stat().st_size <= MAX_PDF_BYTES:
                self.failure = 'IEEE_COMPLETED_DOWNLOAD_SIZE_INVALID'
            else:
                self.body = PDFBody(path.read_bytes())
                print('IEEE_PDF_BYTES_CAPTURED')

    def close(self):
        self.session.remove_listener('Browser.downloadWillBegin', self.begin)
        self.session.remove_listener('Browser.downloadProgress', self.update)
        if self.owns_session:
            try:
                self.session.detach()
            except Error:
                pass
