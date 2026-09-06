from types import SimpleNamespace

from test_ieee_cdp import Session, response
from uestc_paper.publishers.ieee_cdp import CDPPDFObserver
from uestc_paper.publishers.ieee_pdf import location


def test_invalid_first_candidate_then_valid_full_candidate(capsys):
    session = Session(False)
    bodies = {'first': '{' + 'x' * 535, 'second': '%PDF' + 'x' * 600}
    calls = []

    def send(name, args):
        if name == 'Network.getResponseBody':
            calls.append(args['requestId'])
            return {'body': bodies[args['requestId']], 'base64Encoded': False}

    session.send = send
    observer = CDPPDFObserver(SimpleNamespace(new_cdp_session=lambda page: session), None, location)
    observer.received(response())
    observer.finished({'requestId': 'first'})
    assert observer.capture() is None and observer.failure is None
    second = response('second')
    second['response']['url'] += '&resource=2'
    observer.received(second)
    observer.finished({'requestId': 'second'})
    observer.finished({'requestId': 'second'})
    assert observer.capture().data.startswith(b'%PDF')
    assert calls == ['first', 'second']
    output = capsys.readouterr().out
    assert 'IEEE_PDF_CANDIDATE_REJECTED' in output and 'signature=JSON_LIKE' in output
    assert 'NEVER_LOG' not in output


def test_middle_range_not_rejected_as_bad_magic(capsys):
    session = Session(False)
    session.send = lambda *args: {'body': 'x' * 100, 'base64Encoded': False}
    observer = CDPPDFObserver(SimpleNamespace(new_cdp_session=lambda page: session), None, location)
    event = response()
    event['response'].update(status=206, headers={'Content-Range': 'bytes 100-199/1000'})
    observer.received(event)
    observer.finished({'requestId': 'first'})
    assert observer.capture() is None and observer.failure is None
    output = capsys.readouterr().out
    assert 'start=100; end=199; total=1000' in output
    assert 'IEEE_PDF_CANDIDATE_REJECTED' not in output
