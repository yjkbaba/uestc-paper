"""Observe normal browser PDF resources without exposing authenticated URLs."""

from dataclasses import dataclass
from urllib.parse import urlsplit

from playwright.sync_api import Error

from ..http import MAX_PDF_BYTES
from ..uestc import is_webvpn_url


def mime_category(value):
    mime = (value or '').split(';')[0].strip().lower()
    if mime in {'application/pdf', 'application/x-pdf', 'application/acrobat'}:
        return 'PDF'
    return 'HTML' if mime in {'text/html', 'application/xhtml+xml'} else 'OTHER'


@dataclass
class PDFBody:
    data: bytes


class PDFObserver:
    def __init__(self, context, proxied, location):
        self.context = context
        self.proxied = proxied
        self.location = location
        self.pending = []
        self.seen = set()
        self.embeds = set()

    def response(self, response):
        try:
            category = mime_category(response.header_value('content-type'))
            length = response.header_value('content-length') or ''
            length = int(length) if length.isascii() and length.isdigit() else None
            disposition = response.header_value('content-disposition') is not None
            page = response.frame.page
            index = self.context.pages.index(page) if page in self.context.pages else -1
            print(f'IEEE_RESPONSE: page_index={index}; {self.location(response.url)}; '
                  f'status={response.status}; content_type={category}; '
                  f'disposition_present={disposition}; content_length={length}')
            allowed = (is_webvpn_url(response.url) if self.proxied else
                       urlsplit(response.url).hostname == 'ieeexplore.ieee.org')
            if category == 'PDF' and allowed and response.status == 200:
                print('IEEE_PDF_RESPONSE_OBSERVED')
                if response.url not in self.seen and (length is None or length <= MAX_PDF_BYTES):
                    self.seen.add(response.url)
                    self.pending.append(response)
        except Error:
            print('IEEE_RESPONSE_METADATA_UNAVAILABLE')

    def capture(self, captured=None):
        while self.pending:
            response = self.pending.pop(0)
            try:
                data = response.body()
            except Error as exc:
                print('IEEE_PDF_RESPONSE_BODY_UNAVAILABLE: ' +
                      ('TIMEOUT' if 'Timeout' in str(exc) else
                       'RESOURCE_BODY_UNAVAILABLE' if 'No resource with given identifier' in str(exc)
                       else 'BROWSER_BODY_UNAVAILABLE'))
                return None
            if 0 < len(data) <= MAX_PDF_BYTES:
                print('IEEE_PDF_BYTES_CAPTURED')
                return PDFBody(data)
        return None

    def inspect_embeds(self, target):
        scopes = [target] + list(getattr(target, 'frames', []))
        for scope in scopes:
            try:
                for selector, attribute in (('iframe[src]', 'src'), ('embed[src]', 'src'),
                                            ('object[data]', 'data'),
                                            ("a[href*='.pdf']", 'href')):
                    group = scope.locator(selector)
                    for i in range(min(group.count(), 20)):
                        value = group.nth(i).get_attribute(attribute)
                        key = (scope.url, selector, value)
                        if value and key not in self.embeds:
                            self.embeds.add(key)
                            print(f'IEEE_PDF_EMBED_FOUND: type={selector.split("[")[0]}; '
                                  f'{self.location(value)}')
            except Error:
                # The observed frame can navigate while STAMP initializes.
                continue
