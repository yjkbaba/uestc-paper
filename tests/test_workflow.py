from pathlib import Path

from pypdf import PdfWriter

from uestc_paper.cli import main
from uestc_paper.config import Config
from uestc_paper.http import RetrievalError
from uestc_paper.oa import OAResult
from uestc_paper.resolver import Metadata
from uestc_paper.workflow import get_paper


def prepare(monkeypatch, oa_status="OA_FOUND"):
    monkeypatch.setattr("uestc_paper.workflow.resolve_metadata",
                        lambda doi, client: Metadata(doi, status="METADATA_FOUND"))
    monkeypatch.setattr("uestc_paper.workflow.EuropePMCResolver.resolve",
                        lambda self, doi: OAResult(oa_status, "https://example.org/a.pdf"))


def test_oa_end_to_end(tmp_path, monkeypatch, capsys):
    prepare(monkeypatch)

    def download(self, url, path):
        writer = PdfWriter()
        writer.add_blank_page(width=600, height=800)
        writer.add_metadata({"/DOI": "10.1234/abc", "/Subject": "synthetic " * 100})
        with Path(path).open("wb") as stream:
            writer.write(stream)

    monkeypatch.setattr("uestc_paper.workflow.HttpClient.download", download)
    monkeypatch.setattr("uestc_paper.workflow.persistent_browser",
                        lambda config: (_ for _ in ()).throw(AssertionError("OA must run first")))
    assert main(["--home", str(tmp_path), "get", "doi:10.1234/ABC"]) == 0
    assert len(list((tmp_path / "downloads").glob("*.pdf"))) == 1
    assert "SAVED (OA" in capsys.readouterr().out
    assert not list((tmp_path / "runtime").glob("paper-*"))


def test_reject_html(tmp_path, monkeypatch, capsys):
    prepare(monkeypatch)
    monkeypatch.setattr("uestc_paper.workflow.HttpClient.download",
                        lambda self, url, path: path.write_bytes(b"<html>Login</html>"))
    assert get_paper("10.1234/abc", Config(tmp_path)) == 2
    assert not list((tmp_path / "downloads").glob("*.pdf"))
    assert "INVALID_PDF_MAGIC" in capsys.readouterr().out


def test_missing_oa_ieee_no_browser(tmp_path, monkeypatch, capsys):
    prepare(monkeypatch, "OA_NOT_FOUND")
    assert get_paper("10.1109/test", Config(tmp_path), no_browser=True) == 2
    output = capsys.readouterr().out
    assert "OA_NOT_FOUND" in output and "MANUAL_ACTION_REQUIRED" in output


def test_failed_oa_is_not_absence(tmp_path, monkeypatch, capsys):
    prepare(monkeypatch, "OA_LOOKUP_FAILED")
    assert get_paper("10.1109/test", Config(tmp_path), no_browser=True) == 2
    assert "OA_NOT_FOUND" not in capsys.readouterr().out


def test_bad_doi(tmp_path, capsys):
    assert main(["--home", str(tmp_path), "get", "not a doi"]) == 2
    assert "INVALID_DOI" in capsys.readouterr().out


def test_rate_limit_allows_manual_fallback(tmp_path, monkeypatch, capsys):
    prepare(monkeypatch)

    def limited(*args):
        raise RetrievalError("HTTP_429")

    monkeypatch.setattr("uestc_paper.workflow.HttpClient.download", limited)
    assert get_paper("10.1109/test", Config(tmp_path), no_browser=True) == 2
    output = capsys.readouterr().out
    assert "OA_TEMPORARILY_UNAVAILABLE" in output
    assert "PUBLISHER_RESOLVED" in output
    assert not list((tmp_path / "runtime").glob("paper-*"))
