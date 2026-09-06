import pytest

from test_ieee_download import Context, Download, Locator, Page
from uestc_paper.publishers.ieee import IEEEAdapter
from uestc_paper.resolver import Metadata


class PDFControl(Locator):
    def __init__(self, page):
        super().__init__(lambda: None)
        self.page = page

    def get_attribute(self, name, **kwargs):
        assert name == 'href'
        return '/stamp/stamp.jsp?arnumber=123'

    def scroll_into_view_if_needed(self, **kwargs):
        pass

    def hover(self, **kwargs):
        pass

    def bounding_box(self):
        return dict(x=10, y=10, width=20, height=20)

    def evaluate(self, expression):
        return True

    def click(self, **kwargs):
        if not kwargs.get('trial'):
            self.page.context.actions.append('result-pdf-click')
            self.page.url = 'https://vpn.uestc.edu.cn/stamp/stamp.jsp'


class ResultLink(Locator):
    def __init__(self, page):
        super().__init__(page.article)
        self.page = page

    def locator(self, selector):
        if selector.startswith('xpath=ancestor::'):
            return self
        if selector == "a[href*='/document/']":
            return Locator(lambda: None)
        assert selector == "a[href*='/stamp/']"
        return PDFControl(self.page) if self.page.context.card_pdf else Locator()


class ResultPage(Page):
    def locator(self, selector):
        if '/document/' in selector and self.mode == 'proxy' and self.searched:
            return ResultLink(self)
        return super().locator(selector)

    def article(self):
        self.context.actions.append('article-detail-click')
        super().article()


@pytest.mark.parametrize('card_pdf', [True, False])
def test_production_result_pdf_precedes_article_detail(tmp_path, monkeypatch, card_pdf):
    from uestc_paper.publishers.base import DownloadResult
    viewer_calls = []

    def viewer_download(*args):
        viewer_calls.append(True)
        return DownloadResult('IEEE_PDF_VIEWER_OPENED')

    monkeypatch.setattr('uestc_paper.publishers.ieee_viewer_download.download_viewer', viewer_download)
    monkeypatch.setattr('test_ieee_download.Page', ResultPage)
    monkeypatch.setattr(
        'uestc_paper.viewer_download_diagnostic.viewer_control',
        lambda context: any('/stamp/' in page.url for page in context.pages))
    source = tmp_path / 'download.part'
    source.write_bytes(b'%PDF synthetic')
    context = Context(Download(source), direct_access=False)
    context.card_pdf = card_pdf
    adapter = IEEEAdapter()
    adapter.direct_seconds = .001
    result = adapter.download(context, adapter.resolve(Metadata('10.1109/test')),
                              tmp_path / 'target.part', timeout=1)
    assert ('result-pdf-click' in context.actions) is card_pdf
    assert ('article-detail-click' in context.actions) is not card_pdf
    assert context.actions.count('result-pdf-click') == int(card_pdf)
    assert result.status == ('IEEE_PDF_VIEWER_OPENED' if card_pdf else 'DOWNLOAD_RECEIVED')
    assert bool(viewer_calls) is card_pdf
