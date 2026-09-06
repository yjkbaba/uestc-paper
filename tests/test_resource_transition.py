import pytest
from playwright.sync_api import Error, TimeoutError as PlaywrightTimeout

from test_uestc_portal import PortalContext, PortalPage, tick_clock
from uestc_paper.uestc import enter_ieee


@pytest.mark.parametrize('route', ['same-tab', 'new-tab', 'frame'])
def test_delayed_resource_bootstrap_scans_all_scopes(monkeypatch, capsys, route):
    tick_clock(monkeypatch)
    context = PortalContext()
    pending = []
    polls = []

    def resource(self):
        context.actions.append('resource')
        target = self if route == 'same-tab' else context.new_page()
        target.url = 'https://webvpn.uestc.edu.cn/intermediary?token=NEVER_LOG'
        pending.append(target)

    def wait(self, milliseconds):
        if not pending:
            return
        polls.append(1)
        if len(polls) == 10:  # exceeds the previous premature eight-second fallback
            target = pending[0]
            if route == 'frame':
                frame = PortalPage(context)
                frame.mode = 'proxy'
                frame.url = 'https://webvpn.uestc.edu.cn/application?token=NEVER_LOG'
                target.frames.append(frame)
            else:
                target.mode = 'proxy'

    monkeypatch.setattr(PortalPage, 'resource', resource)
    monkeypatch.setattr(PortalPage, 'wait_for_timeout', wait)
    page, status = enter_ieee(context, 80)
    assert status == 'IEEE_VIA_WEBVPN' and page.mode == 'proxy'
    assert context.actions.count('resource') == 1
    output = capsys.readouterr().out
    assert 'UESTC_DOMAIN_FALLBACK' not in output and 'NEVER_LOG' not in output


def test_resource_race_and_timeout_do_not_reclick(monkeypatch, capsys):
    tick_clock(monkeypatch)
    context = PortalContext(has_widget=True)

    def resource(self):
        context.actions.append('resource')

        def navigating(selector):
            raise Error('Execution context was destroyed; NEVER_LOG')

        self.locator = navigating

    monkeypatch.setattr(PortalPage, 'resource', resource)
    page, status = enter_ieee(context, 80)
    assert page is None and status == 'UESTC_ENTRY_UNRECOGNIZED'
    assert context.actions.count('resource') == 1
    output = capsys.readouterr().out
    assert 'UESTC_DOMAIN_FALLBACK' not in output and 'NEVER_LOG' not in output


def test_click_navigation_timeout_still_observes_app_without_reclick(monkeypatch, capsys):
    tick_clock(monkeypatch)
    context = PortalContext()
    original = PortalPage.resource

    def click_dispatched(self):
        original(self)
        raise PlaywrightTimeout('Navigation waiting timed out: NEVER_LOG')

    monkeypatch.setattr(PortalPage, 'resource', click_dispatched)
    page, status = enter_ieee(context, 80)
    assert status == 'IEEE_VIA_WEBVPN' and page.mode == 'proxy'
    assert context.actions.count('resource') == 1
    output = capsys.readouterr().out
    assert 'UESTC_RESOURCE_CLICK_UNCONFIRMED' in output and 'NEVER_LOG' not in output
