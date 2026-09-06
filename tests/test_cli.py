import pytest

from uestc_paper.cli import main


def test_help(capsys):
    with pytest.raises(SystemExit) as result:
        main(["--help"])
    assert result.value.code == 0
    assert "get" in capsys.readouterr().out


def test_setup(tmp_path):
    assert main(["--home", str(tmp_path), "setup"]) == 0
    assert (tmp_path / "runtime" / ".gitignore").read_text() == "*\n"


def test_login_unknown(tmp_path, monkeypatch, capsys):
    from contextlib import contextmanager
    from types import SimpleNamespace

    visited = []

    @contextmanager
    def browser(config):
        yield SimpleNamespace(new_page=lambda: SimpleNamespace(
            goto=lambda url, **kwargs: visited.append(url)))

    monkeypatch.setattr("uestc_paper.browser.persistent_browser", browser)
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    assert main(["--home", str(tmp_path), "login"]) == 2
    assert visited == ["https://vpn.uestc.edu.cn"]
    assert "LOGIN_STATE_UNKNOWN" in capsys.readouterr().out


def test_status(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("uestc_paper.browser.runtime_status", lambda: "BROWSER_MISSING")
    assert main(["--home", str(tmp_path), "status"]) == 0
    output = capsys.readouterr().out
    assert "Browser runtime: BROWSER_MISSING" in output
    assert "Browser profile: MISSING" in output
    assert "Institution session: MISSING" in output
