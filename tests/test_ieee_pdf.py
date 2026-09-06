import pytest

from test_ieee_download import Context, Locator, Page
from uestc_paper.publishers.ieee_pdf import attempt, location


@pytest.mark.parametrize('popup_host,heading,expected', [
    ('ieeexplore.ieee.org', 'Purchase', 'IEEE_PDF_PROXY_ESCAPE'),
    ('webvpn.uestc.edu.cn', 'Purchase', 'IEEE_PROXY_ACCESS_REQUIRED'),
    ('webvpn.uestc.edu.cn', 'Sign in', 'IEEE_INSTITUTION_SIGNIN_REQUIRED'),
    ('webvpn.uestc.edu.cn', '', 'IEEE_PDF_VIEWER_OPENED'),
])
def test_pdf_popup_outcomes(popup_host, heading, expected, capsys):
    context = Context()

    class Popup(Page):
        def title(self):
            return 'IEEE Xplore Full-Text PDF' if not heading else 'IEEE Xplore'

        def get_by_role(self, role, name=None, **kwargs):
            if role == 'heading' and heading and name.search(heading):
                return Locator(lambda: None)
            return Locator()

    class Article(Page):
        def get_by_role(self, role, name=None, **kwargs):
            if role == 'link':
                action = Locator(self.open_pdf)
                action.get_attribute = lambda name: 'https://ieeexplore.ieee.org/stamp/stamp.jsp'
                return action
            return Locator()

        def open_pdf(self):
            popup = Popup(context)
            popup.url = f'https://{popup_host}/stamp/stamp.jsp?secret=NEVER_LOG'
            context.pages.append(popup)
            for callback in context.listeners:
                callback(popup)

    article = Article(context)
    article.url = 'https://webvpn.uestc.edu.cn/document/123/?secret=NEVER_LOG'
    context.pages.append(article)
    assert attempt(article, [], context, .02, True) == expected
    output = capsys.readouterr().out
    assert 'IEEE_PDF_CLICK: popup' in output
    assert f'host={popup_host}; path_type=STAMP' in output
    assert 'NEVER_LOG' not in output and 'secret=' not in output
    assert not context.listeners


def test_location_never_emits_path_or_query():
    assert location('https://webvpn.uestc.edu.cn/SECRET/stamp/stamp.jsp?token=SECRET') == (
        'host=webvpn.uestc.edu.cn; path_type=STAMP')


def test_rewritten_frame_link_preferred_over_direct_popup():
    context = Context()
    captured = []
    clicked = []

    class PDFPage(Page):
        def get_by_role(self, role, name=None, **kwargs):
            if role != 'link':
                return Locator()
            action = Locator(lambda: (clicked.append(self.url), captured.append('download')))
            action.get_attribute = lambda name: self.url + '/stamp/stamp.jsp'
            return action

    article = PDFPage(context)
    article.url = 'https://webvpn.uestc.edu.cn/document/123/'
    # The observed rewritten frame link is chosen; no URL is synthesized for navigation.
    frame = PDFPage(context)
    frame.url = 'https://webvpn.uestc.edu.cn/observed-proxy'
    article.frames = [frame]
    original = article.get_by_role

    def direct_link(*args, **kwargs):
        action = original(*args, **kwargs)
        action.get_attribute = lambda name: 'https://ieeexplore.ieee.org/stamp/stamp.jsp'
        return action

    article.get_by_role = direct_link
    context.pages.append(article)
    assert attempt(article, captured, context, .02, True) == 'DOWNLOAD_RECEIVED'
    assert clicked == [frame.url]


def test_direct_download_event_is_not_saved_as_proxy():
    class Download:
        url = 'https://ieeexplore.ieee.org/stamp/file.pdf?token=DO_NOT_LOG'

    context = Context()
    page = context.new_page()
    page.url = 'https://webvpn.uestc.edu.cn/document/123/'
    captured = [(Download(), 'UESTC WebVPN / IEEE')]
    assert attempt(page, captured, context, .02, True) == 'IEEE_PDF_PROXY_ESCAPE'
    assert not captured
