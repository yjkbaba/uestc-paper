from playwright.sync_api import Error

from test_uestc_portal import PortalContext, PortalPage, tick_clock
from uestc_paper.uestc import enter_ieee


def test_portal_marker_detached_frame_replaced(monkeypatch, capsys):
    tick_clock(monkeypatch)
    context = PortalContext()
    owner = context.new_page()
    owner.url = 'https://webvpn.uestc.edu.cn/'
    stale = PortalPage(context)
    stale.url = owner.url
    replacement = PortalPage(context)
    replacement.url = owner.url
    replacement.mode = 'portal'
    owner.frames = [stale]

    def detached(name):
        owner.frames = [replacement]
        raise Error('Frame was detached: NEVER_LOG')

    stale.get_by_text = detached
    result = enter_ieee(context, 80, on_portal_ready=lambda: True)
    assert result[1] == 'IEEE_POST_AUTH_DIRECT_SUCCESS'
    output = capsys.readouterr().out
    assert 'FRAME_DETACHED_TRANSIENT' in output and 'UESTC_WEBVPN_PORTAL_READY' in output
    assert 'NEVER_LOG' not in output


def test_resource_dispatched_old_frame_detached_new_application(monkeypatch, capsys):
    tick_clock(monkeypatch)
    context = PortalContext()
    owner = context.new_page()
    owner.url = 'https://webvpn.uestc.edu.cn/'
    old = PortalPage(context)
    old.url = owner.url
    old.mode = 'portal'
    owner.frames = [old]

    def dispatched():
        context.actions.append('resource')
        new_page = context.new_page()
        new_page.url = 'https://webvpn.uestc.edu.cn/'
        application = PortalPage(context)
        application.url = new_page.url
        application.mode = 'proxy'
        new_page.frames = [application]
        owner.frames = []
        raise Error('Frame was detached: NEVER_LOG')

    old.resource = dispatched
    page, status = enter_ieee(context, 80)
    assert status == 'IEEE_VIA_WEBVPN' and page.mode == 'proxy'
    assert context.actions.count('resource') == 1
    output = capsys.readouterr().out
    assert 'FRAME_DETACHED_TRANSIENT' in output and 'NEVER_LOG' not in output
    assert 'UESTC_DOMAIN_FALLBACK' not in output
