from types import SimpleNamespace

import pytest

from uestc_paper.publishers.ieee_result import open_result_pdf


@pytest.mark.parametrize('scenario,expected', [
    ('late-ready', 'IEEE_PDF_VIEWER_OPENED'),
    ('no-evidence', 'IEEE_PDF_VIEWER_TIMEOUT'),
    ('stamp-only', 'IEEE_PDF_VIEWER_NOT_READY'),
])
def test_unconfirmed_click_passively_observes_full_window(monkeypatch, scenario, expected):
    clock, clicks = [0], []
    monkeypatch.setattr('uestc_paper.publishers.ieee_result.time.monotonic', lambda: clock[0])

    def click(control):
        clicks.append(control)
        return 'AUTO_CLICK_TIMING_FAILURE'

    monkeypatch.setattr('uestc_paper.auto_click_diagnostic.pointer_click', click)
    monkeypatch.setattr('uestc_paper.viewer_download_diagnostic.viewer_control',
                        lambda context: scenario == 'late-ready' and clock[0] >= 110)

    class Page:
        url = 'https://webvpn.uestc.edu.cn/resource/'

        def is_closed(self):
            return False

        @property
        def frames(self):
            if scenario == 'no-evidence' or clock[0] < 100:
                return []
            return [SimpleNamespace(url='https://webvpn.uestc.edu.cn/stamp/',
                                    locator=lambda _: SimpleNamespace(count=lambda: 1))]

        def wait_for_timeout(self, ms):
            assert ms == 1000
            clock[0] += 1

    page = Page()
    context = SimpleNamespace(pages=[page])
    assert open_result_pdf(context, page, 'single-control', []) == expected
    assert clicks == ['single-control']
    assert clock[0] == (110 if scenario == 'late-ready' else 120)
