from contextlib import contextmanager
import json
from types import SimpleNamespace

from uestc_paper.browser import browser_choice, configure_download_preferences, persistent_browser
from uestc_paper.config import Config
from uestc_paper.session import institution_session


def test_runtime_choice(tmp_path):
    executable = tmp_path / "chromium"
    executable.touch()
    fake = SimpleNamespace(chromium=SimpleNamespace(executable_path=str(executable)))
    assert browser_choice(fake) == (None, executable)


def test_visible_persistent_context(tmp_path, monkeypatch):
    config = Config(tmp_path)
    captured = {}

    class Context:
        def close(self):
            captured["closed"] = True

    class Chromium:
        def launch_persistent_context(self, directory, **kwargs):
            captured.update(kwargs)
            captured["directory"] = directory
            return Context()

    @contextmanager
    def fake_playwright():
        yield SimpleNamespace(chromium=Chromium())

    monkeypatch.setattr("playwright.sync_api.sync_playwright", fake_playwright)
    monkeypatch.setattr("uestc_paper.browser.browser_choice", lambda p: (None, tmp_path))
    with persistent_browser(config):
        assert captured["headless"] is False
        assert captured["directory"] == str(config.profile)
        assert captured["accept_downloads"] is True
    assert captured["closed"]
    assert not (config.runtime / "browser.lock").exists()
    assert '"password_manager_enabled": false' in (
        config.profile / "Default" / "Preferences").read_text()


def test_session_never_assumes_active(tmp_path):
    config = Config(tmp_path)
    assert institution_session(config) == "MISSING"
    path = config.profile / "Default" / "Network" / "Cookies"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"synthetic non-secret state")
    assert institution_session(config) == "UNKNOWN"


def test_download_preferences_preserve_viewer_and_unrelated_settings(tmp_path):
    config = Config(tmp_path)
    path = config.profile / 'Default' / 'Preferences'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'plugins': {'always_open_pdf_externally': False},
                                'unrelated': {'value': 17},
                                'download': {'prompt_for_download': True}}))
    configure_download_preferences(config)
    result = json.loads(path.read_text())
    assert result['download']['prompt_for_download'] is False
    assert result['download']['default_directory'] == str(
        (config.runtime / 'download-capture').resolve())
    assert result['plugins'] == {'always_open_pdf_externally': False}
    assert result['unrelated'] == {'value': 17}
