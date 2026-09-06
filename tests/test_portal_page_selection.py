from test_uestc_portal import PortalContext, PortalPage, tick_clock
from test_ieee_download import Locator
from uestc_paper.uestc import enter_ieee, portal_ready


def test_existing_webvpn_is_third_page(monkeypatch, capsys):
    tick_clock(monkeypatch)
    context = PortalContext()
    blank = context.new_page()
    blank.url = 'about:blank'
    ieee = context.new_page()
    ieee.url = 'https://ieeexplore.ieee.org/stamp/stamp.jsp?token=DO_NOT_LOG'
    portal = context.new_page()
    portal.mode = 'portal'
    portal.url = 'https://webvpn.uestc.edu.cn/resource?token=DO_NOT_LOG'
    retries = []
    result = enter_ieee(context, 50, on_portal_ready=lambda: retries.append(context) or True)
    assert result[1] == 'IEEE_POST_AUTH_DIRECT_SUCCESS'
    assert retries == [context]
    assert len(context.pages) == 3  # do not open another VPN or close working pages
    output = capsys.readouterr().out
    assert 'WebVPN candidate: PAGE[2]' in output
    assert 'UESTC_WEBVPN_PORTAL_READY' in output
    assert 'DO_NOT_LOG' not in output and 'stamp.jsp' not in output


def test_webvpn_host_without_marker_is_not_ready():
    page = PortalContext().new_page()
    page.url = 'https://webvpn.uestc.edu.cn/'
    assert not portal_ready(page)


def test_authenticated_modern_portal_precedes_legacy(monkeypatch, capsys):
    tick_clock(monkeypatch)
    context = PortalContext()
    legacy = context.new_page()
    legacy.url = 'https://vpn.uestc.edu.cn/'
    legacy.mode = 'portal'
    modern = context.new_page()
    modern.url = 'https://webvpn.uestc.edu.cn/'
    modern.mode = 'portal'
    focused = []
    legacy.bring_to_front = lambda: focused.append('legacy')
    modern.bring_to_front = lambda: focused.append('modern')
    assert enter_ieee(context, 50, on_portal_ready=lambda: True)[1] == (
        'IEEE_POST_AUTH_DIRECT_SUCCESS')
    assert focused == ['modern']
    assert len(context.pages) == 2 and not context.visits
    assert 'WAITING_FOR_USER_AUTH' not in capsys.readouterr().out


def test_main_frame_before_child_frames(monkeypatch):
    tick_clock(monkeypatch)
    context = PortalContext()
    page = context.new_page()
    page.mode = 'portal'
    page.url = 'https://webvpn.uestc.edu.cn/'

    class UnneededFrame:
        url = 'https://webvpn.uestc.edu.cn/frame'

        def get_by_text(self, *args):
            raise AssertionError('main frame already has a portal marker')

    page.frames = [UnneededFrame()]
    assert enter_ieee(context, 50, on_portal_ready=lambda: True)[1] == 'IEEE_POST_AUTH_DIRECT_SUCCESS'


def test_child_frame_when_main_has_no_marker(monkeypatch):
    tick_clock(monkeypatch)
    context = PortalContext()
    page = context.new_page()
    page.url = 'https://webvpn.uestc.edu.cn/'
    frame = PortalPage(context)
    frame.url = 'https://webvpn.uestc.edu.cn/frame'
    frame.mode = 'portal'
    page.frames = [frame]
    page.get_by_text = lambda name: Locator()
    assert enter_ieee(context, 50, on_portal_ready=lambda: True)[1] == 'IEEE_POST_AUTH_DIRECT_SUCCESS'
