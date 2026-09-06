"""Normal IEEE UI downloads; only authentication remains manual."""

from urllib.parse import quote, urlsplit

from playwright.sync_api import Error, TimeoutError as PlaywrightTimeout

from .base import DownloadResult, PublisherAdapter, PublisherResolution
from .ieee_target import canonical_article_id
from .ieee_pdf import attempt
from .ieee_response import PDFBody
from .ieee_result import result_pdf, open_result_pdf
from ..http import MAX_PDF_BYTES
from ..uestc import enter_ieee, is_ieee, is_webvpn_url, search_article
from ..verify import verify_pdf


class IEEEAdapter(PublisherAdapter):
    direct_seconds = 12

    def matches(self, metadata) -> bool:
        return (metadata.doi.lower().startswith("10.1109/") or
                urlsplit(metadata.url).hostname == "ieeexplore.ieee.org")

    def resolve(self, metadata) -> PublisherResolution:
        if not self.matches(metadata):
            return PublisherResolution("PUBLISHER_UNSUPPORTED")
        return PublisherResolution("PUBLISHER_RESOLVED",
                                   "https://doi.org/" + quote(metadata.doi, safe="/"),
                                   metadata.doi, metadata.title)

    def _attempt(self, page, captured, context, *, proxied=False) -> str:
        return attempt(page, captured, context, self.direct_seconds, proxied,
                       getattr(self, 'use_cdp', False), getattr(self, 'download_directory', None))

    def _receive_file(self, download, destination, route):
        if isinstance(download, PDFBody):
            destination.write_bytes(download.data)
            # The caller must use the existing identity/structure verifier before final save.
            return DownloadResult('DOWNLOAD_RECEIVED', destination, route)
        failure = download.failure()
        if failure:
            reason = ('DOWNLOAD_CANCELED' if failure in {'canceled', 'net::ERR_ABORTED'} else
                      'DOWNLOAD_NETWORK_FAILED' if failure in {'net::ERR_FAILED',
                      'net::ERR_CONNECTION_RESET', 'net::ERR_TIMED_OUT'} else
                      'DOWNLOAD_ACCESS_CHANGED' if failure == 'net::ERR_ACCESS_DENIED' else
                      'DOWNLOAD_UNKNOWN_FAILURE')
            print(f'IEEE_DOWNLOAD_FAILURE: {reason}')
            return DownloadResult("DOWNLOAD_FAILED")
        source = download.path()
        if source is None or source.stat().st_size > MAX_PDF_BYTES:
            return DownloadResult("INVALID_DOWNLOAD_SIZE")
        download.save_as(str(destination))
        with destination.open("rb") as stream:
            if stream.read(4) != b"%PDF":
                return DownloadResult("INVALID_PDF_MAGIC")
        print("PDF_DOWNLOADED")
        return DownloadResult("DOWNLOAD_RECEIVED", destination, route)

    def download(self, context, resolution, destination, timeout=300) -> DownloadResult:
        if resolution.status != "PUBLISHER_RESOLVED" or not resolution.landing_url:
            return DownloadResult("PUBLISHER_UNSUPPORTED")
        captured, attached = [], []
        article_id = ""
        phase = "DIRECT_IEEE"

        def receive(download, page):
            if phase != 'DIRECT_IEEE' and not is_webvpn_url(page.url):
                return  # Ignore late direct-route events after moving to institutional access.
            if not captured:
                print("IEEE_DOWNLOAD_STARTED")
                route = "UESTC WebVPN / IEEE" if is_webvpn_url(page.url) else "IEEE direct"
                captured.append((download, route))

        def attach(page):
            def handler(download):
                receive(download, page)
            page.on("download", handler)
            attached.append((page, handler))

        context.on("page", attach)
        try:
            page = context.new_page()
            try:
                page.goto(resolution.landing_url, wait_until="domcontentloaded", timeout=30000)
                print("IEEE_DIRECT_OPENED" if is_ieee(page) else "IEEE_ARTICLE_NOT_CONFIRMED")
                article_id = canonical_article_id(page.url)
                status = self._attempt(page, captured, context)
            except Error as exc:
                status = ('IEEE_DIRECT_TIMEOUT' if isinstance(exc, PlaywrightTimeout)
                          else 'IEEE_DIRECT_BROWSER_ACTION_FAILED')
            article_id = canonical_article_id(page.url) or article_id
            if not article_id:
                # Popup URLs from the normal PDF click can carry arnumber.
                ids = {canonical_article_id(p.url) for p, _ in attached
                       if is_ieee(p) and canonical_article_id(p.url)}
                if len(ids) == 1:
                    article_id = ids.pop()
            print(f"IEEE_ARTICLE_IDENTIFIER: arnumber={article_id or 'UNKNOWN'}")
            print(status)
            if captured:
                try:
                    result = self._receive_file(captured[0][0], destination, captured[0][1])
                    verification = verify_pdf(destination, resolution.doi, resolution.title)
                    print(f'IEEE_DIRECT_VERIFICATION: {verification.status}; '
                          f'pages={verification.pages}; size={verification.size}; '
                          f'identity={verification.identity}')
                    if (result.status == 'DOWNLOAD_RECEIVED' and verification.valid
                            and verification.identity == 'MATCH'):
                        print('PDF_VERIFIED')
                        print('IEEE_ACCESS_GRANTED')
                        return result
                except Error:
                    print('IEEE_DIRECT_DOWNLOAD_UNAVAILABLE')
            destination.unlink(missing_ok=True)
            captured.clear()
            if status in {"IEEE_AUTOMATION_BLOCKED", "CANCELLED"}:
                return DownloadResult(status)
            print('IEEE_DIRECT_RETRIEVAL_FAILED: continuing institutional fallback; no direct retry.')
            print("INSTITUTION_AUTH_REQUIRED")
            phase = "UESTC_PORTAL"
            proxy_page, status = enter_ieee(context, timeout, lambda: bool(captured))
            if captured:
                return self._receive_file(captured[0][0], destination, captured[0][1])
            if proxy_page is None:
                return DownloadResult(status)
            phase = "PROXIED_TARGET_SEARCH"

            def result_route(scope, link):
                try:
                    action = result_pdf(link, article_id)
                except Error:
                    action = None
                if action is None:
                    print('IEEE_TARGET_RESULT_PDF_UNAVAILABLE: article-detail fallback')
                    # The same known result is already present: preserve existing detail navigation.
                    return search_article(scope, resolution.doi, resolution.title, article_id,
                                          context=context)
                print('IEEE_TARGET_RESULT_PDF_FOUND')
                result_status = open_result_pdf(context, scope, action, captured)
                print(result_status)
                if captured:
                    return self._receive_file(captured[0][0], destination, captured[0][1])
                if result_status == 'IEEE_PDF_VIEWER_OPENED':
                    from .ieee_viewer_download import download_viewer
                    return download_viewer(context, destination, resolution)
                return DownloadResult(result_status)

            target = search_article(proxy_page, resolution.doi, resolution.title, article_id,
                                    context=context, on_result=result_route)
            if isinstance(target, DownloadResult):
                return target
            if not target:
                return DownloadResult(target.status)
            status = self._attempt(target.page, captured, context, proxied=True)
            print(status)
            if captured:
                return self._receive_file(captured[0][0], destination, captured[0][1])
            return DownloadResult(status)
        except Error as exc:
            print(f"FAILED_PHASE: {phase}")
            return DownloadResult("IEEE_BROWSER_TIMEOUT" if isinstance(exc, PlaywrightTimeout)
                                  else "IEEE_BROWSER_ACTION_FAILED")
        finally:
            context.remove_listener("page", attach)
            for page, handler in attached:
                page.remove_listener("download", handler)
