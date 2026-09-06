"""Read the first normal Chromium PDF response; never replay a request."""

import base64
import time
import re
from urllib.parse import urlsplit

from playwright.sync_api import Error

from ..http import MAX_PDF_BYTES
from .ieee_response import PDFBody, PDFObserver, mime_category


class CDPPDFObserver(PDFObserver):
    def __init__(self, context, page, location, download_directory=None):
        super().__init__(context, True, location)
        self.request_id = None
        self.body = None
        self.candidates = {}
        self.processed = set()
        self.resources = set()
        self.outcome = None
        self.failure = None
        self.aborted_at = None
        self.handoff = False
        self.manager = None
        self.session = context.new_cdp_session(page)
        self.session.on('Network.responseReceived', self.received)
        self.session.on('Network.loadingFinished', self.finished)
        self.session.on('Network.loadingFailed', self.failed)
        self.session.send('Network.enable', {'maxTotalBufferSize': MAX_PDF_BYTES * 2,
                                             'maxResourceBufferSize': MAX_PDF_BYTES})
        if download_directory is not None:
            from .ieee_download_manager import DownloadManager
            self.manager = DownloadManager(context, self.session, download_directory)

    def response(self, response):
        # CDP is the sole body source in this diagnostic, including after failure.
        pass

    def received(self, event):
        response = event.get('response', {})
        request_id = event.get('requestId')
        if (self.body is not None or request_id in self.candidates or
                urlsplit(response.get('url', '')).hostname != 'webvpn.uestc.edu.cn' or
                mime_category(response.get('mimeType')) != 'PDF' or
                response.get('status') not in {200, 206}):
            return
        headers = {k.lower(): v for k, v in response.get('headers', {}).items()
                   if k.lower() in {'content-length', 'content-range', 'content-disposition'}}
        raw_range = str(headers.get('content-range', ''))
        match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', raw_range)
        span = tuple(map(int, match.groups())) if match else None
        key = (response['url'], response['status'], raw_range)
        if key in self.resources:
            return
        self.resources.add(key)
        length = str(headers.get('content-length', ''))
        info = {'number': len(self.candidates) + 1, 'status': int(response['status']),
                'length': int(length) if length.isascii() and length.isdigit() else None,
                'range_present': 'content-range' in headers, 'span': span,
                'disposition': 'content-disposition' in headers}
        self.candidates[request_id] = info
        if self.request_id is None:
            self.request_id = request_id
            if self.manager:
                self.manager.select(response['url'])
        self.seen.add('PDF_CANDIDATE')
        print('IEEE_PDF_RESPONSE_OBSERVED')
        self.features(info)
        if span:
            print(f'IEEE_PDF_RANGE: start={span[0]}; end={span[1]}; total={span[2]}')

    def features(self, info, data=None):
        signature = 'OTHER'
        if data is not None:
            sample = data.lstrip()[:40].lower()
            signature = ('PDF_MAGIC' if data.startswith(b'%PDF') else
                         'HTML_LIKE' if sample.startswith((b'<', b'<!doctype')) else
                         'JSON_LIKE' if sample.startswith((b'{', b'[')) else 'OTHER')
        print(f'IEEE_PDF_CANDIDATE: number={info["number"]}; status={info["status"]}; '
              f'body_bytes={len(data) if data is not None else None}; '
              f'content_length={info["length"]}; content_range={info["range_present"]}; '
              f'content_disposition={info["disposition"]}; signature={signature}')

    def finished(self, event):
        request_id = event.get('requestId')
        if request_id not in self.candidates or request_id in self.processed or self.body is not None:
            return
        self.processed.add(request_id)
        info = self.candidates[request_id]
        try:
            result = self.session.send('Network.getResponseBody', {'requestId': request_id})
            data = result['body']
            if result.get('base64Encoded'):
                data = base64.b64decode(data, validate=True)
            elif isinstance(data, str):
                data = data.encode('utf-8')
            if not isinstance(data, bytes):
                raise TypeError()
            self.features(info, data)
            span = info['span']
            if info['status'] == 206 or info['range_present']:
                if not span or not (span[0] == 0 and span[1] + 1 == span[2] == len(data)):
                    print('IEEE_PDF_RANGE_OBSERVED: full_candidate=False')
                    return
            if not 512 <= len(data) <= MAX_PDF_BYTES or not data.startswith(b'%PDF'):
                print('IEEE_PDF_CANDIDATE_REJECTED')
                return
            self.body = PDFBody(data)
            print('IEEE_PDF_BYTES_CAPTURED')
        except Error:
            print('IEEE_PDF_CANDIDATE_BODY_UNAVAILABLE')
        except (KeyError, ValueError, TypeError):
            print('IEEE_PDF_CANDIDATE_REJECTED')

    def failed(self, event):
        request_id = event.get('requestId')
        if request_id not in self.candidates or request_id in self.processed:
            return
        self.processed.add(request_id)
        error = event.get('errorText', '')
        category = ('ABORTED' if error == 'net::ERR_ABORTED' else
                    'NETWORK_FAILED' if error in {'net::ERR_FAILED', 'net::ERR_CONNECTION_RESET',
                                                 'net::ERR_TIMED_OUT'} else 'OTHER')
        blocked = event.get('blockedReason')
        blocked = blocked if blocked in {'other', 'csp', 'mixed-content', 'origin', 'inspector',
                                         'subresource-filter', 'content-type',
                                         'coep-frame-resource-needs-coep-header',
                                         'corp-not-same-origin', 'corp-not-same-site'} else (
                                             'OTHER' if blocked else 'NONE')
        cors = 'PRESENT' if event.get('corsErrorStatus') else 'NONE'
        print(f'IEEE_CDP_LOADING_FAILED: error_category={category}; '
              f'canceled={event.get("canceled") is True}; blocked_reason={blocked}; cors={cors}')
        if category == 'ABORTED' and self.manager:
            self.aborted_at = time.monotonic()
        else:
            self.outcome = 'IEEE_CDP_LOADING_FAILED'

    def capture(self, captured=None):
        if self.manager:
            if self.aborted_at is not None and self.manager.guid and not self.handoff:
                self.handoff = True
                print('IEEE_PDF_DOWNLOAD_HANDOFF')
                print(f'IEEE_PLAYWRIGHT_DOWNLOAD_OBSERVED: {bool(captured)}')
            if self.manager.failure:
                self.outcome = self.manager.failure
            if self.manager.body:
                return self.manager.body
            if (self.aborted_at is not None and not self.manager.guid and
                    time.monotonic() - self.aborted_at >= 5):
                self.outcome = 'IEEE_PDF_ABORT_WITHOUT_DOWNLOAD'
        return self.body

    def close(self):
        if self.manager:
            self.manager.close()
        try:
            self.session.detach()
        except Error:
            pass
