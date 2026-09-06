import io
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from uestc_paper.http import HttpClient, RetrievalError, SafeRedirect


class Response(io.BytesIO):
    def __init__(self, content, content_type="application/pdf"):
        super().__init__(content)
        self.headers = {"Content-Type": content_type}


def test_html_response_rejected(tmp_path, monkeypatch):
    client = HttpClient()
    monkeypatch.setattr(client, "_open", lambda url: Response(b"<html>Login</html>", "text/html"))
    with pytest.raises(RetrievalError, match="HTML_NOT_PDF"):
        client.download("https://example.org/file.pdf", tmp_path / "paper.part")


def test_magic_response_rejected(tmp_path, monkeypatch):
    client = HttpClient()
    monkeypatch.setattr(client, "_open", lambda url: Response(b"HTML despite PDF MIME"))
    with pytest.raises(RetrievalError, match="INVALID_PDF_MAGIC"):
        client.download("https://example.org/file.pdf", tmp_path / "paper.part")


def test_limit(tmp_path, monkeypatch):
    monkeypatch.setattr("uestc_paper.http.MAX_PDF_BYTES", 20)
    client = HttpClient()
    monkeypatch.setattr(client, "_open", lambda url: Response(b"%PDF" + b"x" * 30))
    with pytest.raises(RetrievalError, match="PDF_TOO_LARGE"):
        client.download("https://example.org/a.pdf", tmp_path / "paper.part")


def test_safe_errors_no_url_or_response(monkeypatch):
    client = HttpClient()

    def fail(*args, **kwargs):
        raise HTTPError("https://example.org/?token=secret", 429, "secret", {}, None)

    monkeypatch.setattr(client.opener, "open", fail)
    with pytest.raises(RetrievalError) as result:
        client.json("https://example.org/")
    assert str(result.value) == "HTTP_429"


def test_redirect_guard():
    with pytest.raises(RetrievalError, match="UNSAFE_REDIRECT"):
        SafeRedirect().redirect_request(Request("https://example.org"), None, 302, "", {},
                                        "https://sci-hub.se/a.pdf")
