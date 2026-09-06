from contextlib import contextmanager
import logging
from pathlib import Path
from urllib.error import URLError

import pytest

from uestc_paper.browser import BrowserError, persistent_browser
from uestc_paper.config import Config
from uestc_paper.http import HttpClient, RetrievalError
from uestc_paper.oa import EuropePMCResolver, OAResult
from uestc_paper.publishers.base import DownloadResult
from uestc_paper.resolver import Metadata
from uestc_paper.verify import verify_pdf
from uestc_paper.workflow import get_paper


@pytest.mark.parametrize("code", ["HTTP_429", "HTTP_403", "NETWORK_TIMEOUT", "NETWORK_ERROR"])
@pytest.mark.parametrize("phase", ["lookup", "download"])
def test_oa_failure_reaches_normal_ieee_ui(tmp_path, monkeypatch, capsys, code, phase):
    config = Config(tmp_path)
    config.setup()
    old = config.downloads / "existing.pdf"
    old.write_bytes(b"existing correct file sentinel")
    calls = []
    monkeypatch.setattr("uestc_paper.workflow.resolve_metadata",
                        lambda doi, client: Metadata(doi, status="METADATA_FOUND"))

    def broken_json(self, url):
        calls.append("lookup")
        raise RetrievalError(code)

    def broken_download(self, url, path):
        calls.append("download")
        path.write_bytes(b"partial unverified data")
        raise RetrievalError(code)

    if phase == "lookup":
        monkeypatch.setattr(HttpClient, "json", broken_json)
    else:
        monkeypatch.setattr(EuropePMCResolver, "resolve", lambda self, doi:
                            OAResult("OA_FOUND", "https://example.org/a.pdf?token=SENTINEL"))
        monkeypatch.setattr(HttpClient, "download", broken_download)

    @contextmanager
    def browser(config):
        calls.append("visible browser")
        yield object()

    def manual(self, context, resolution, destination, timeout):
        assert not destination.exists()
        calls.append("IEEE UI")
        return DownloadResult("MANUAL_ACTION_REQUIRED")

    monkeypatch.setattr("uestc_paper.workflow.persistent_browser", browser)
    monkeypatch.setattr("uestc_paper.workflow.IEEEAdapter.download", manual)
    assert get_paper("10.1109/test", config) == 2
    output = capsys.readouterr().out
    assert "OA_TEMPORARILY_UNAVAILABLE" in output
    assert "SUCCESS" not in output and "SENTINEL" not in output
    assert "OA_NOT_FOUND" not in output
    assert calls == [phase, "visible browser", "IEEE UI"]
    assert old.read_bytes() == b"existing correct file sentinel"
    assert list(config.downloads.glob("*.pdf")) == [old]
    assert not list(config.runtime.glob("paper-*"))


@pytest.mark.parametrize("error", [TimeoutError("secret"), URLError(TimeoutError("secret"))])
def test_timeout_sanitized(monkeypatch, error):
    client = HttpClient()

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(client.opener, "open", fail)
    with pytest.raises(RetrievalError, match="^NETWORK_TIMEOUT$"):
        client.json("https://example.org/?token=SENTINEL")


def test_arbitrary_exception_text_not_logged():
    assert str(RetrievalError("Cookie: SENTINEL; Authorization: SENTINEL")) == "RETRIEVAL_ERROR"


@pytest.mark.parametrize("variable", ["DEBUG", "PWDEBUG"])
def test_protocol_debug_disabled(tmp_path, monkeypatch, variable):
    monkeypatch.setenv(variable, "1")
    with pytest.raises(BrowserError, match="DEBUG_LOGGING_DISABLED"):
        with persistent_browser(Config(tmp_path)):
            pytest.fail("must not launch with protocol logging enabled")


def test_parser_diagnostics_suppressed(tmp_path, monkeypatch, caplog):
    path = tmp_path / "bad.pdf"
    path.write_bytes(b"%PDF" + b"x" * 600)
    original = logging.root.manager.disable

    def broken_reader(*args, **kwargs):
        logging.getLogger("pypdf.reader").error("signed URL token SENTINEL")
        raise ValueError("SENTINEL")

    monkeypatch.setattr("uestc_paper.verify.PdfReader", broken_reader)
    assert verify_pdf(path).status == "PDF_PARSE_ERROR"
    assert "SENTINEL" not in caplog.text
    assert logging.root.manager.disable == original


def test_save_collision_does_not_overwrite(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from uestc_paper.verify import VerificationResult
    from uestc_paper.workflow import _save_verified

    config = Config(tmp_path)
    config.setup()
    monkeypatch.setattr("uestc_paper.workflow.verify_pdf", lambda *args:
                        VerificationResult(True, "PDF_VERIFIED", 700, 1, "MATCH"))
    monkeypatch.setattr("uestc_paper.workflow.uuid.uuid4", lambda: SimpleNamespace(hex="12345678"))
    first = config.runtime / "first.part"
    first.write_bytes(b"first verified PDF sentinel")
    metadata = Metadata("10.1109/test")
    assert _save_verified(first, metadata, config, "test")
    second = config.runtime / "second.part"
    second.write_bytes(b"second file")
    with pytest.raises(FileExistsError):
        _save_verified(second, metadata, config, "test")
    assert next(Path(config.downloads).glob("*.pdf")).read_bytes() == b"first verified PDF sentinel"
