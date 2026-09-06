import pytest

from test_ieee_download import Context, Locator, Page
from uestc_paper.uestc import enter_ieee, portal_ready


class Widget(Locator):
    def __init__(self, page):
        super().__init__(lambda *args: page.context.actions.append(args))
        self.page = page

    def locator(self, selector):
        if selector.startswith('xpath=ancestor::'):
            return self
        if selector == 'select':
            return Locator()
        raise AssertionError('Unexpected widget selector')

    def get_by_text(self, name):
        return Locator(lambda: None) if name.search('https') else Locator()

    def get_by_role(self, role, name=None):
        assert role == 'button'
        return Locator(self.page.resource)


class PortalPage(Page):
    def get_by_role(self, role, name=None, **kwargs):
        if self.mode == 'portal' and name and hasattr(name, 'search'):
            if name.search(self.context.resource_name):
                return Locator(self.resource) if self.context.has_resource else Locator()
        return super().get_by_role(role, name, **kwargs)

    def get_by_placeholder(self, name):
        if self.mode == 'portal' and self.context.has_widget:
            assert name.search('输入域名直接访问校内资源')
            return Widget(self)
        return Locator()


class PortalContext(Context):
    def __init__(self, resource_name='IEEE', has_resource=True, has_widget=True):
        super().__init__()
        self.resource_name = resource_name
        self.has_resource = has_resource
        self.has_widget = has_widget

    def new_page(self):
        page = PortalPage(self)
        self.pages.append(page)
        return page


def tick_clock(monkeypatch):
    import itertools
    monkeypatch.setattr('uestc_paper.uestc.time.monotonic', lambda: next(ticks))
    ticks = itertools.count(0, 1)


@pytest.mark.parametrize('label', ['IEEE', 'IEL', 'IEEE / IEL', 'IEEE Electronic Library'])
def test_official_list_first(monkeypatch, capsys, label):
    tick_clock(monkeypatch)
    context = PortalContext(resource_name=label)
    page, status = enter_ieee(context, 50)
    assert status == 'IEEE_VIA_WEBVPN'
    assert page.mode == 'proxy'
    assert context.actions == ['library', 'resource']
    output = capsys.readouterr().out
    assert 'UESTC_WEBVPN_PORTAL_READY' in output
    assert 'UESTC_LIBRARY_DATABASES_OPENED' in output
    assert 'UESTC_IEEE_RESOURCE_OPENED' in output
    assert 'UESTC_DOMAIN_FALLBACK' not in output
    assert 'click PDF' not in output


def test_portal_detection_requires_structure():
    context = PortalContext()
    page = context.new_page()
    assert not portal_ready(page)
    page.goto('https://vpn.uestc.edu.cn/')
    assert portal_ready(page)


def test_single_resources_marker_and_short_library(monkeypatch):
    tick_clock(monkeypatch)
    context = PortalContext()
    original = PortalPage.get_by_role

    def labels(self, name):
        if self.mode == 'portal' and name.search('校内常用资源'):
            return Locator(lambda: None)
        return Locator()

    def roles(self, role, name=None, **kwargs):
        if name and name.search('图书馆'):
            return Locator(lambda: self.context.actions.append('short library'))
        if name and '外文' in str(name):
            return Locator()
        return original(self, role, name, **kwargs)

    monkeypatch.setattr(PortalPage, 'get_by_text', labels)
    monkeypatch.setattr(PortalPage, 'get_by_role', roles)
    assert enter_ieee(context, 50)[1] == 'IEEE_VIA_WEBVPN'
    assert context.actions[0] == 'short library'


def test_no_resource_uses_https_domain_widget(monkeypatch, capsys):
    tick_clock(monkeypatch)
    context = PortalContext(has_resource=False)
    page, status = enter_ieee(context, 50)
    assert status == 'IEEE_VIA_WEBVPN'
    assert ('fill', 'ieeexplore.ieee.org') in context.actions
    assert context.actions[0] == 'library'
    assert 'UESTC_DOMAIN_FALLBACK' in capsys.readouterr().out


def test_unrecognized_routes_fail_explicitly(monkeypatch, capsys):
    tick_clock(monkeypatch)
    page, status = enter_ieee(PortalContext(has_resource=False, has_widget=False), 50)
    assert page is None and status == 'UESTC_ENTRY_UNRECOGNIZED'
    output = capsys.readouterr().out
    assert 'USER_ACTION_REQUIRED' in output and 'SUCCESS' not in output


def test_no_auth_fields_inspected(monkeypatch):
    tick_clock(monkeypatch)
    context = PortalContext()
    original = PortalPage.get_by_role

    def guarded(self, role, *args, **kwargs):
        assert role not in {'textbox'}
        return original(self, role, *args, **kwargs)

    monkeypatch.setattr(PortalPage, 'get_by_role', guarded)
    assert enter_ieee(context, 50)[1] == 'IEEE_VIA_WEBVPN'


def test_portal_tab_is_focused(monkeypatch):
    tick_clock(monkeypatch)
    context = PortalContext()
    enter_ieee(context, 50)
    assert context.focused is context.pages[0]


def test_resource_portal_in_frame(monkeypatch):
    tick_clock(monkeypatch)
    context = PortalContext()
    original = context.new_page

    def framed_page():
        owner = original()
        frame = PortalPage(context)
        frame.mode = 'portal'
        frame.url = 'https://vpn.uestc.edu.cn/resource-frame'
        owner.frames = [frame]
        owner.get_by_text = lambda name: Locator()
        owner.get_by_placeholder = lambda name: Locator()
        return owner

    context.new_page = framed_page
    page, status = enter_ieee(context, 50)
    assert status == 'IEEE_VIA_WEBVPN'
    assert page in context.pages[0].frames
