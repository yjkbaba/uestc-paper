from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from pypdf import PdfWriter

from uestc_paper.config import Config
from uestc_paper.oa import OAResult
from uestc_paper.publishers.ieee import IEEEAdapter
from uestc_paper.resolver import Metadata
from uestc_paper.uestc import enter_ieee, is_ieee, search_article
from uestc_paper.workflow import get_paper
from test_verify import make_pdf


class Locator:
    def __init__(self, action=None):
        self.action = action
        self.first = self

    def count(self):
        return int(self.action is not None)

    def nth(self, index):
        return self

    def is_visible(self):
        return bool(self.count())

    def is_enabled(self):
        return True

    def bounding_box(self):
        return dict(x=0, y=0, width=20, height=20)

    def evaluate(self, expression):
        assert 'elementFromPoint' in expression
        return True

    def click(self, **kwargs):
        self.action()

    def fill(self, value, **kwargs):
        self.action('fill', value)

    def press(self, value, **kwargs):
        self.action('press', value)

    def get_attribute(self, name, **kwargs):
        assert name == 'href'
        return '/observed-resource/document/123/'

    def locator(self, selector):
        return Locator()  # Default fixtures have no result-card PDF control.


class SearchInput(Locator):
    def __init__(self, page):
        super().__init__(page.search)
        self.page = page

    def evaluate(self, expression):
        return dict(search_type=True, in_form=True, within=False)

    def get_attribute(self, name, **kwargs):
        return ''

    def input_value(self):
        self.page.context.actions.append(('read-back', self.page.search_value))
        return self.page.search_value

    def locator(self, selector):
        assert selector == 'xpath=ancestor::form[1]'
        return self

    def get_by_role(self, role, name=None):
        assert role == 'button'
        return Locator(lambda: self.page.search('button', 'Search'))


class Page:
    def __init__(self, context):
        self.context = context
        self.callbacks = {}
        self.mode = 'direct'
        self.url = 'about:blank'
        self.searched = False
        self.frames = []
        self.main_frame = None
        self.mouse_actions = []
        self.mouse = SimpleNamespace(
            move=lambda x, y: self.mouse_actions.append(('move', x, y)),
            down=lambda: self.mouse_actions.append(('down',)),
            up=self.mouse_up)

    def mouse_up(self):
        self.mouse_actions.append(('up',))
        self.search('button', 'Search')

    def bring_to_front(self):
        self.context.focused = self

    def on(self, event, callback):
        self.callbacks[event] = callback

    def remove_listener(self, event, callback):
        self.callbacks.pop(event, None)

    def goto(self, url, **kwargs):
        self.context.visits.append(url)
        if 'vpn.uestc' in url:
            self.mode = 'portal'
            self.url = 'https://vpn.uestc.edu.cn/'
        else:
            self.url = 'https://ieeexplore.ieee.org/document/123/'

    def is_closed(self):
        return False

    def wait_for_timeout(self, milliseconds):
        pass

    def get_by_text(self, name):
        if self.mode == 'portal' and any(t in str(name) for t in ('图书馆', '校内')):
            return Locator(lambda: None)
        return Locator()

    def get_by_role(self, role, name=None, **kwargs):
        label = str(name)
        if role == 'link' and '外文' in label and self.mode == 'portal':
            return Locator(lambda: self.context.actions.append('library'))
        if role == 'searchbox' and self.mode == 'proxy':
            return Locator(self.search)
        if role == 'link' and 'PDF' in label and self.mode in {'direct', 'proxy'}:
            if self.context.direct_access or self.mode == 'proxy':
                return Locator(lambda: self.callbacks['download'](self.context.download))
        if role == 'link' and 'IEEE' in label and self.mode == 'portal':
            return Locator(self.resource)
        return Locator()

    def get_by_placeholder(self, name):
        return Locator()

    def get_by_label(self, name):
        return Locator()

    def locator(self, selector):
        if selector == "input[type='search'], input[type='text'], input:not([type])":
            return SearchInput(self) if self.mode == 'proxy' else Locator()
        if selector == "input[type='search']":
            return Locator()
        assert 'input' not in selector and 'password' not in selector
        if selector == 'xpl-root' and self.mode == 'proxy':
            return Locator(lambda: None)
        if '/document/' in selector and self.mode == 'proxy' and self.searched:
            return Locator(self.article)
        return Locator()

    def resource(self):
        self.context.actions.append('resource')
        self.mode = 'proxy'
        self.url = 'https://vpn.uestc.edu.cn/observed-resource/home'

    def search(self, operation, value):
        self.context.actions.append((operation, value))
        if operation == 'fill':
            self.search_value = value
        if operation in {'press', 'button'}:
            self.searched = True

    def evaluate(self, expression):
        assert expression == 'document.readyState'
        return 'complete'

    def article(self):
        self.url = 'https://vpn.uestc.edu.cn/observed-resource/document/123/'


class Context:
    def __init__(self, download=None, direct_access=True):
        self.download = download
        self.direct_access = direct_access
        self.pages = []
        self.callback = None
        self.listeners = []
        self.visits = []
        self.actions = []

    def on(self, event, callback):
        self.listeners.append(callback)
        self.callback = self.listeners[0]

    def remove_listener(self, event, callback):
        self.listeners.remove(callback)
        self.callback = self.listeners[0] if self.listeners else None

    def new_page(self):
        page = Page(self)
        self.pages.append(page)
        for callback in list(self.listeners):
            callback(page)
        return page


class Download:
    def __init__(self, source):
        self.source = source

    def failure(self):
        return None

    def path(self):
        return self.source

    def save_as(self, destination):
        Path(destination).write_bytes(self.source.read_bytes())


def test_direct_pdf_never_opens_vpn(tmp_path, capsys):
    source = make_pdf(tmp_path / 'synthetic.part', doi='10.1109/test')
    context = Context(Download(source))
    adapter = IEEEAdapter()
    result = adapter.download(context, adapter.resolve(Metadata('10.1109/test')),
                              tmp_path / 'target.part', timeout=1)
    assert result.status == 'DOWNLOAD_RECEIVED'
    assert result.route == 'IEEE direct'
    assert len(context.visits) == 1
    assert 'IEEE_DIRECT_DOWNLOAD_ATTEMPT' in capsys.readouterr().out
    assert context.callback is None


def test_entitlement_failure_automatically_uses_resource(tmp_path, capsys):
    source = tmp_path / 'synthetic.part'
    source.write_bytes(b'%PDF synthetic')
    context = Context(Download(source), direct_access=False)
    adapter = IEEEAdapter()
    adapter.direct_seconds = .01
    result = adapter.download(context, adapter.resolve(Metadata('10.1109/test')),
                              tmp_path / 'target.part', timeout=1)
    assert result.status == 'DOWNLOAD_RECEIVED'
    assert result.route == 'UESTC WebVPN / IEEE'
    assert context.visits[1] == 'https://vpn.uestc.edu.cn/'
    assert len(context.visits) == 2
    assert context.actions == ['library', 'resource', ('fill', '10.1109/TEST'),
                               ('read-back', '10.1109/TEST'), ('button', 'Search')]
    output = capsys.readouterr().out
    assert 'WAITING_FOR_USER_AUTH' in output and 'IEEE_VIA_UESTC_OPENED' in output
    assert 'UESTC_AUTHENTICATED' not in output  # no unsupported login assertion


def test_auth_timeout_no_credential_inspection():
    context = Context()
    page, status = enter_ieee(context, timeout=0)
    assert page is None and status == 'UESTC_AUTH_OR_ENTRY_TIMEOUT'
    assert context.actions == []
    assert context.visits == ['https://vpn.uestc.edu.cn/']


def test_normal_ieee_url_is_not_a_proxy():
    context = Context()
    page = context.new_page()
    page.goto('https://ieeexplore.ieee.org/document/123/')
    assert not is_ieee(page, proxied=True)
    assert not search_article(page, '10.1109/test', '', '123', timeout=0)
    assert context.actions == []


@pytest.mark.parametrize('valid', [True, False])
def test_unknown_session_automatic_event_runs_verifier(tmp_path, monkeypatch, capsys, valid):
    source = tmp_path / 'fixture.part'
    if valid:
        writer = PdfWriter()
        writer.add_blank_page(width=600, height=800)
        writer.add_metadata({'/DOI': '10.1109/test', '/Subject': 'synthetic ' * 100})
        writer.write(source)
    else:
        source.write_bytes(b'%PDF broken' * 100)
    context = Context(Download(source))

    @contextmanager
    def browser(config):
        yield context

    monkeypatch.setattr('uestc_paper.workflow.persistent_browser', browser)
    monkeypatch.setattr('uestc_paper.workflow.institution_session', lambda config: 'UNKNOWN')
    monkeypatch.setattr('uestc_paper.workflow.resolve_metadata', lambda doi, client: Metadata(doi))
    monkeypatch.setattr('uestc_paper.workflow.EuropePMCResolver.resolve',
                        lambda self, doi: OAResult('OA_NOT_FOUND'))
    assert get_paper('10.1109/test', Config(tmp_path)) == (0 if valid else 2)
    output = capsys.readouterr().out
    assert 'INSTITUTION_SESSION_UNKNOWN' in output
    assert 'IEEE_DIRECT_DOWNLOAD_ATTEMPT' in output
    assert ('PDF_VERIFIED' if valid else 'PDF_PARSE_ERROR') in output
    assert len(list((tmp_path / 'downloads').glob('*.pdf'))) == int(valid)
