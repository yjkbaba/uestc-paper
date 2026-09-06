from types import SimpleNamespace

import pytest
from pypdf import PdfWriter

from test_ieee_cdp import Session, response
from uestc_paper.publishers.ieee_cdp import CDPPDFObserver
from uestc_paper.publishers.ieee_pdf import location
from uestc_paper.publishers.ieee import IEEEAdapter
from uestc_paper.config import Config
from uestc_paper.resolver import Metadata
from uestc_paper.workflow import _save_verified


def observer(tmp_path):
    session = Session(False)
    context = SimpleNamespace(browser=SimpleNamespace(new_browser_cdp_session=lambda: session),
                              new_cdp_session=lambda page: session)
    return CDPPDFObserver(context, None, location, tmp_path / 'capture')


def abort(capture):
    capture.received(response())
    capture.failed({'requestId': 'first', 'errorText': 'net::ERR_ABORTED', 'canceled': True})


def begin(capture):
    capture.manager.begin({'url': response()['response']['url'], 'guid': 'safe-guid'})


def test_abort_with_download_handoff(tmp_path, capsys):
    capture = observer(tmp_path)
    abort(capture)
    begin(capture)
    capture.capture([])
    assert capture.handoff and not capture.failure
    output = capsys.readouterr().out
    assert 'IEEE_PDF_DOWNLOAD_HANDOFF' in output and 'NEVER_LOG' not in output


def test_abort_without_download(tmp_path, monkeypatch):
    capture = observer(tmp_path)
    abort(capture)
    monkeypatch.setattr('uestc_paper.publishers.ieee_cdp.time.monotonic',
                        lambda: capture.aborted_at + 6)
    capture.capture([])
    assert capture.outcome == 'IEEE_PDF_ABORT_WITHOUT_DOWNLOAD'


def test_browser_download_canceled(tmp_path):
    capture = observer(tmp_path)
    abort(capture)
    begin(capture)
    capture.manager.update({'guid': 'safe-guid', 'state': 'canceled', 'receivedBytes': 0,
                            'totalBytes': 10})
    assert capture.capture([]) is None
    assert capture.outcome == 'DOWNLOAD_CANCELED'


@pytest.mark.parametrize('valid', [True, False])
def test_completed_browser_file_requires_verifier(tmp_path, valid):
    capture = observer(tmp_path)
    abort(capture)
    begin(capture)
    source = capture.manager.directory / 'safe-guid'
    if valid:
        writer = PdfWriter()
        writer.add_blank_page(width=600, height=800)
        writer.add_metadata({'/DOI': '10.1109/test', '/Subject': 'fixture ' * 100})
        writer.write(source)
    else:
        source.write_bytes(b'<html>not PDF</html>')
    capture.manager.update({'guid': 'safe-guid', 'state': 'completed',
                            'receivedBytes': source.stat().st_size})
    config = Config(tmp_path)
    config.setup()
    temporary = config.runtime / 'verified.part'
    IEEEAdapter()._receive_file(capture.capture([]), temporary, 'UESTC WebVPN / IEEE')
    assert source.exists()  # Never remove the manager file before verification.
    assert _save_verified(temporary, Metadata('10.1109/test'), config, 'IEEE') is valid
    assert len(list(config.downloads.glob('*.pdf'))) == int(valid)
