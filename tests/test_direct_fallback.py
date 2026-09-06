from contextlib import contextmanager

import pytest
from playwright.sync_api import TimeoutError

from test_ieee_download import Context, Download
from test_verify import make_pdf
from uestc_paper.config import Config
from uestc_paper.oa import OAResult
from uestc_paper.publishers.ieee import IEEEAdapter
from uestc_paper.publishers.ieee_response import PDFBody
from uestc_paper.resolver import Metadata
from uestc_paper.workflow import get_paper


@pytest.mark.parametrize('direct', ['invalid-536', 'valid', 'timeout'])
def test_production_get_validates_direct_before_fallback(tmp_path, monkeypatch, capsys, direct):
    source = make_pdf(tmp_path / 'fixture.pdf', doi='10.1109/test')
    context = Context(Download(source), direct_access=False)
    attempts, institutional = [], []
    original_attempt = IEEEAdapter._attempt
    from uestc_paper.publishers import ieee
    original_entry = ieee.enter_ieee
    original_verify = ieee.verify_pdf
    verified = []

    def attempt(self, page, captured, ctx, *, proxied=False):
        attempts.append(proxied)
        if not proxied:
            if direct == 'timeout':
                raise TimeoutError('synthetic navigation timeout')
            data = source.read_bytes() if direct == 'valid' else b'<html>'.ljust(536, b' ')
            captured.append((PDFBody(data), 'IEEE direct'))
            return 'DOWNLOAD_RECEIVED'
        return original_attempt(self, page, captured, ctx, proxied=True)

    def entry(*args, **kwargs):
        institutional.append(True)
        assert direct != 'valid', 'Valid direct PDF must bypass institution entry'
        assert not list((tmp_path / 'runtime').glob('paper-*/article.part'))
        assert not args[2](), 'Rejected candidate must be cleared from capture state'
        return original_entry(*args, **kwargs)

    def verify(path, doi, title):
        result = original_verify(path, doi, title)
        verified.append(result.status)
        return result

    @contextmanager
    def browser(_config):
        yield context

    monkeypatch.setattr('uestc_paper.workflow.persistent_browser', browser)
    monkeypatch.setattr('uestc_paper.workflow.resolve_metadata', lambda doi, client: Metadata(doi))
    monkeypatch.setattr('uestc_paper.workflow.EuropePMCResolver.resolve',
                        lambda self, doi: OAResult('OA_NOT_FOUND'))
    monkeypatch.setattr(IEEEAdapter, '_attempt', attempt)
    monkeypatch.setattr(ieee, 'enter_ieee', entry)
    monkeypatch.setattr(ieee, 'verify_pdf', verify)
    assert get_paper('10.1109/test', Config(tmp_path), timeout=1) == 0
    output = capsys.readouterr().out
    assert attempts.count(False) == 1
    assert context.visits.count('https://doi.org/10.1109/test') == 1
    assert 'RETRIEVAL_UNVERIFIED' not in output
    assert len(list((tmp_path / 'downloads').glob('*.pdf'))) == 1
    if direct == 'valid':
        assert verified == ['PDF_VERIFIED']
        assert not institutional and attempts == [False]
    else:
        assert institutional == [True] and attempts == [False, True]
        assert output.index('IEEE_DIRECT_RETRIEVAL_FAILED') < output.index('UESTC_WEBVPN_PORTAL_READY')
        assert 'SEARCH_VALUE_CONFIRMED' in output
        assert 'IEEE_SEARCH_MOUSE_DISPATCHED' in output
        assert 'IEEE_TARGET_RESULT_FOUND' in output
        if direct == 'invalid-536':
            assert verified == ['INVALID_PDF_MAGIC']
            assert 'size=536' in output
