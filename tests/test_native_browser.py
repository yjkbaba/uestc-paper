from contextlib import contextmanager
from types import SimpleNamespace

from uestc_paper.config import Config
from uestc_paper.native_browser import persistent_browser


def test_native_context_has_no_download_behavior_override(tmp_path, monkeypatch):
    config = Config(tmp_path)
    calls = []
    context = object()

    class Chromium:
        def connect_over_cdp(self, endpoint, **kwargs):
            assert endpoint == 'http://127.0.0.1:12345'
            assert kwargs['no_defaults'] is True
            assert kwargs['artifacts_dir'] == str(config.runtime / 'download-capture')
            return SimpleNamespace(contexts=[context], new_browser_cdp_session=lambda:
                                   SimpleNamespace(send=lambda method: calls.append(method)))

    @contextmanager
    def playwright():
        yield SimpleNamespace(chromium=Chromium())

    def popen(args, **kwargs):
        assert '--headless' not in args
        assert '--user-data-dir=' + str(config.profile) in args
        assert '--remote-debugging-address=127.0.0.1' in args
        (config.profile / 'DevToolsActivePort').write_text('12345\n')
        return SimpleNamespace(poll=lambda: None, wait=lambda **kw: 0)

    monkeypatch.setattr('uestc_paper.native_browser.sync_playwright', playwright)
    monkeypatch.setattr('uestc_paper.native_browser.browser_choice', lambda p: (None, tmp_path))
    monkeypatch.setattr('uestc_paper.native_browser.subprocess.Popen', popen)
    with persistent_browser(config) as actual:
        assert actual is context
    assert calls == ['Browser.close']
    assert not (config.runtime / 'browser.lock').exists()


def test_verified_output_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv('UESTC_PAPER_OUTPUT', str(tmp_path / 'verified'))
    assert Config(tmp_path).downloads == tmp_path / 'verified'
