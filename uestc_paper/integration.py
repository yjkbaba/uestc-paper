"""Explicit local institutional-only diagnostics; not the default retrieval workflow."""

import argparse
import tempfile
import uuid
from pathlib import Path

from playwright.sync_api import Error

from .browser import BrowserError, persistent_browser
from .config import Config
from .publishers.ieee import IEEEAdapter
from .resolver import normalize_doi, resolve_metadata
from .uestc import enter_ieee, search_article
from .workflow import _save_verified


def run(doi, article_number, config, timeout):
    doi = normalize_doi(doi)
    if not doi.startswith('10.1109/') or not article_number.isdigit():
        raise ValueError('IEEE DOI and an explicitly supplied numeric article number are required.')
    print('INTEGRATION_START_INSTITUTIONAL: local diagnostic; default OA workflow unchanged.')
    print(f'DOI_NORMALIZED: {doi}; arnumber={article_number}')
    metadata = resolve_metadata(doi)
    config.setup()
    with tempfile.TemporaryDirectory(prefix='integration-', dir=config.runtime) as directory:
        temporary = Path(directory) / 'article.part'
        with persistent_browser(config) as context:
            captured = []
            attached = []

            def attach(page):
                def receive(download):
                    captured.append((download, 'UESTC WebVPN / IEEE'))
                page.on('download', receive)
                attached.append((page, receive))

            for page in context.pages:
                attach(page)
            context.on('page', attach)
            phase = 'UESTC_PORTAL'
            try:
                portal, status = enter_ieee(context, timeout)
                if portal is None:
                    print(status)
                    return 2
                phase = 'IEEE_TARGET_SEARCH'
                target = search_article(portal, doi, metadata.title, article_number, context=context)
                if not target:
                    print(target.status)
                    return 2
                adapter = IEEEAdapter()
                adapter.use_cdp = True
                adapter.download_directory = config.runtime / 'download-capture' / uuid.uuid4().hex
                adapter.direct_seconds = 90  # Allow the one browser-managed download to finish.
                phase = 'IEEE_PDF_DIAGNOSTICS'
                status = adapter._attempt(target.page, captured, context, proxied=True)
                print(status)
                if status != 'DOWNLOAD_RECEIVED' or not captured:
                    return 2
                result = adapter._receive_file(captured[0][0], temporary, captured[0][1])
                if result.status != 'DOWNLOAD_RECEIVED':
                    print(result.status)
                    return 2
                return 0 if _save_verified(temporary, metadata, config, result.route) else 2
            except Error as exc:
                reason = 'BROWSER_ACTION_FAILED'
                for phrase, label in (
                    ('Execution context was destroyed', 'NAVIGATION_CONTEXT_CHANGED'),
                    ('has been closed', 'BROWSER_OR_PAGE_CLOSED'),
                    ('detached', 'FRAME_DETACHED'),
                    ('Timeout', 'BROWSER_TIMEOUT'),
                    ('strict mode violation', 'AMBIGUOUS_CONTROL'),
                ):
                    if phrase in str(exc):
                        reason = label
                        break
                print(f'INTEGRATION_FAILED: phase={phase}; reason={reason}')
                return 2
            finally:
                context.remove_listener('page', attach)
                for page, handler in attached:
                    page.remove_listener('download', handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('doi')
    parser.add_argument('--article-number', required=True,
                        help='Article number previously observed for this requested DOI')
    parser.add_argument('--wait-seconds', type=int, default=300)
    args = parser.parse_args()
    if not 1 <= args.wait_seconds <= 3600:
        parser.error('wait-seconds must be between 1 and 3600')
    try:
        return run(args.doi, args.article_number, Config.load(None), args.wait_seconds)
    except (Error, BrowserError, OSError):
        print('INTEGRATION_BROWSER_OR_RUNTIME_FAILED')
        return 2
    except ValueError:
        print('INVALID_IEEE_IDENTIFIER')
        return 2
    except (KeyboardInterrupt, EOFError):
        print('CANCELLED')
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
