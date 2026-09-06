from types import SimpleNamespace

from playwright.sync_api import TimeoutError

from uestc_paper.auto_viewer_default import download_once


def test_default_download_waits_before_single_real_click_and_never_retries(tmp_path):
    calls = []

    class Pending:
        def __enter__(self):
            calls.append('listen')
            return self

        def __exit__(self, *args):
            raise TimeoutError('redacted')

    control = SimpleNamespace(
        scroll_into_view_if_needed=lambda **kw: None,
        click=lambda **kw: calls.append('trial' if kw.get('trial') else 'click'))
    page = SimpleNamespace(expect_download=lambda **kw: Pending())
    assert not download_once(page, control, tmp_path / 'candidate', None, tmp_path)
    assert calls == ['trial', 'listen', 'click']
    assert not (tmp_path / 'candidate').exists()
