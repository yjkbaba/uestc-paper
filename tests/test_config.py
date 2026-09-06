from uestc_paper.config import Config


def test_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("UESTC_PAPER_HOME", str(tmp_path))
    config = Config.load()
    assert config.profile == tmp_path / "runtime" / "browser-profile"
    assert config.downloads == tmp_path / "downloads"
    assert Config.load(str(tmp_path / "explicit")).root == tmp_path / "explicit"
