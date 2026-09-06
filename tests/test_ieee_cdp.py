import base64
from types import SimpleNamespace

import pytest
from pypdf import PdfWriter

from uestc_paper.publishers.ieee_cdp import CDPPDFObserver
from uestc_paper.publishers.ieee_pdf import location
from uestc_paper.publishers.ieee import IEEEAdapter
from uestc_paper.config import Config
from uestc_paper.resolver import Metadata
from uestc_paper.workflow import _save_verified


class Session:
    def __init__(self, encoded):
        self.calls = []
        self.encoded = encoded

    def on(self, *args):
        pass

    def send(self, name, args):
        self.calls.append((name, args))
        return {'body': base64.b64encode(b'%PDF' + b'x' * 600).decode() if self.encoded else '%PDF' + 'x' * 600,
                'base64Encoded': self.encoded}

    def detach(self):
        pass


def response(request_id='first'):
    return {'requestId': request_id, 'response': {
        'url': 'https://webvpn.uestc.edu.cn/resource?token=NEVER_LOG',
        'mimeType': 'application/pdf', 'status': 200}}


@pytest.mark.parametrize('encoded', [False, True])
def test_first_pdf_finished_reads_body_once(encoded, capsys):
    session = Session(encoded)
    context = SimpleNamespace(new_cdp_session=lambda page: session)
    observer = CDPPDFObserver(context, object(), location)
    observer.received(response())
    observer.received(response('second'))
    observer.finished({'requestId': 'second'})
    assert observer.capture() is None
    observer.finished({'requestId': 'first'})
    observer.finished({'requestId': 'first'})
    assert observer.capture().data == b'%PDF' + b'x' * 600
    assert [name for name, _ in session.calls] == ['Network.enable', 'Network.getResponseBody']
    assert 'NEVER_LOG' not in capsys.readouterr().out


def test_first_loading_failed_stops_and_redacts(capsys):
    session = Session(False)
    observer = CDPPDFObserver(SimpleNamespace(new_cdp_session=lambda page: session), None, location)
    observer.received(response())
    observer.failed({'requestId': 'first', 'errorText': 'secret URL NEVER_LOG',
                     'canceled': True, 'blockedReason': 'NEVER_LOG',
                     'corsErrorStatus': {'corsError': 'NEVER_LOG'}})
    observer.received(response('second'))
    observer.finished({'requestId': 'first'})
    assert observer.outcome == 'IEEE_CDP_LOADING_FAILED'
    assert observer.capture() is None
    assert len(session.calls) == 1
    assert 'NEVER_LOG' not in capsys.readouterr().out


@pytest.mark.parametrize('valid', [True, False])
def test_cdp_bytes_require_verifier_before_save(tmp_path, valid):
    source = tmp_path / 'source.part'
    if valid:
        writer = PdfWriter()
        writer.add_blank_page(width=600, height=800)
        writer.add_metadata({'/DOI': '10.1109/test', '/Subject': 'fixture ' * 100})
        writer.write(source)
    else:
        source.write_bytes(b'%PDF malformed ' * 100)
    session = Session(True)
    session.send = lambda name, args: {'body': base64.b64encode(source.read_bytes()).decode(),
                                      'base64Encoded': True}
    observer = CDPPDFObserver(SimpleNamespace(new_cdp_session=lambda page: session), None, location)
    observer.received(response())
    observer.finished({'requestId': 'first'})
    config = Config(tmp_path)
    config.setup()
    temporary = config.runtime / 'body.part'
    IEEEAdapter()._receive_file(observer.capture(), temporary, 'UESTC WebVPN / IEEE')
    assert _save_verified(temporary, Metadata('10.1109/test'), config, 'UESTC WebVPN / IEEE') is valid
    assert len(list(config.downloads.glob('*.pdf'))) == int(valid)
