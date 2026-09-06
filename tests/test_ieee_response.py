from types import SimpleNamespace

import pytest
from pypdf import PdfWriter
from playwright.sync_api import Error

from test_ieee_download import Context, Locator
from uestc_paper.config import Config
from uestc_paper.publishers.ieee import IEEEAdapter
from uestc_paper.publishers.ieee_pdf import location
from uestc_paper.publishers.ieee_response import PDFObserver
from uestc_paper.resolver import Metadata
from uestc_paper.workflow import _save_verified


class Response:
    url = 'https://webvpn.uestc.edu.cn/observed/file.pdf?token=NEVER_LOG'
    status = 200

    def __init__(self, page, mime, data):
        self.frame = SimpleNamespace(page=page)
        self.mime = mime
        self.data = data

    def header_value(self, name):
        assert name in {'content-type', 'content-length', 'content-disposition'}
        return {'content-type': self.mime, 'content-length': str(len(self.data))}.get(name)

    def body(self):
        return self.data


def test_html_then_pdf_without_download_event(capsys):
    context = Context()
    page = context.new_page()
    observer = PDFObserver(context, True, location)
    observer.response(Response(page, 'text/html', b'<html>STAMP</html>'))
    assert observer.capture() is None
    observer.response(Response(page, 'application/pdf', b'%PDF bytes'))
    assert observer.capture().data == b'%PDF bytes'
    output = capsys.readouterr().out
    assert 'IEEE_PDF_RESPONSE_OBSERVED' in output and 'IEEE_PDF_BYTES_CAPTURED' in output
    assert 'NEVER_LOG' not in output


@pytest.mark.parametrize('tag,attr', [('iframe', 'src'), ('embed', 'src'), ('object', 'data')])
def test_stamp_dom_attributes_and_pdf_response(tag, attr, capsys):
    context = Context()
    page = context.new_page()
    page.url = 'https://webvpn.uestc.edu.cn/stamp/stamp.jsp'
    observer = PDFObserver(context, True, location)
    element = Locator(lambda: None)
    element.get_attribute = lambda name: Response.url if name == attr else None
    page.locator = lambda selector: element if selector == f'{tag}[{attr}]' else Locator()
    observer.inspect_embeds(page)
    assert observer.capture() is None  # DOM evidence alone cannot become PDF bytes.
    observer.response(Response(page, 'application/pdf', b'%PDF data'))
    assert observer.capture() is not None
    output = capsys.readouterr().out
    assert f'IEEE_PDF_EMBED_FOUND: type={tag}' in output
    assert 'NEVER_LOG' not in output


@pytest.mark.parametrize('valid', [True, False])
def test_response_bytes_use_verifier_before_final_save(tmp_path, valid):
    config = Config(tmp_path)
    config.setup()
    source = tmp_path / 'source.part'
    if valid:
        writer = PdfWriter()
        writer.add_blank_page(width=600, height=800)
        writer.add_metadata({'/DOI': '10.1109/test', '/Subject': 'synthetic ' * 100})
        writer.write(source)
    else:
        source.write_bytes(b'<html>login page</html>')
    context = Context()
    page = context.new_page()
    observer = PDFObserver(context, True, location)
    observer.response(Response(page, 'application/pdf', source.read_bytes()))
    temporary = config.runtime / 'response.part'
    result = IEEEAdapter()._receive_file(observer.capture(), temporary, 'UESTC WebVPN / IEEE')
    assert _save_verified(temporary, Metadata('10.1109/test'), config, result.route) is valid
    assert len(list(config.downloads.glob('*.pdf'))) == int(valid)


def test_nonproxy_and_failed_pdf_response_not_captured():
    context = Context()
    page = context.new_page()
    observer = PDFObserver(context, True, location)
    response = Response(page, 'application/pdf', b'%PDF')
    response.status = 403
    observer.response(response)
    response.status = 200
    response.url = 'https://ieeexplore.ieee.org/file.pdf'
    observer.response(response)
    assert observer.capture() is None


def test_body_failure_never_replays_resource():
    context = Context()
    page = context.new_page()
    observer = PDFObserver(context, True, location)
    response = Response(page, 'application/pdf', b'%PDF')

    def unavailable():
        raise Error('Body unavailable')

    response.body = unavailable
    observer.response(response)
    assert observer.capture() is None
    assert len(context.pages) == 1 and not context.visits


def test_pdf_click_response_is_received_without_download_callback():
    context = Context()
    page = context.new_page()
    page.url = 'https://webvpn.uestc.edu.cn/document/123/'
    response = Response(page, 'application/pdf', b'%PDF body')
    response.request = SimpleNamespace(is_navigation_request=lambda: False)

    def click():
        page.callbacks['response'](response)

    page.get_by_role = lambda role, **kwargs: Locator(click) if role == 'link' else Locator()
    captured = []
    adapter = IEEEAdapter()
    adapter.direct_seconds = .02
    assert adapter._attempt(page, captured, context, proxied=True) == 'DOWNLOAD_RECEIVED'
    assert captured[0][0].data == b'%PDF body'



def test_download_failure_does_not_log_arbitrary_error(tmp_path, capsys):
    download = SimpleNamespace(failure=lambda: 'https://example.test/?token=NEVER_LOG')
    result = IEEEAdapter()._receive_file(download, tmp_path / 'file.part', 'IEEE')
    assert result.status == 'DOWNLOAD_FAILED'
    assert 'NEVER_LOG' not in capsys.readouterr().out
    assert not (tmp_path / 'file.part').exists()
