"""Bounded public HTTP requests, deliberately independent of browser credentials."""

import json
import re
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_PDF_BYTES = 100 * 1024 * 1024


class RetrievalError(Exception):
    """Contains only a safe operational status, never a response or redirect URL."""

    def __init__(self, status: str):
        allowed = {"UNSAFE_REDIRECT", "UNSAFE_URL", "NETWORK_ERROR", "NETWORK_TIMEOUT",
                   "METADATA_TOO_LARGE", "INVALID_METADATA", "HTML_NOT_PDF",
                   "INVALID_PDF_MAGIC", "PDF_TOO_LARGE", "DOWNLOAD_IO_ERROR"}
        super().__init__(status if status in allowed or re.fullmatch(r"HTTP_\d{3}", status)
                         else "RETRIEVAL_ERROR")

    @property
    def temporarily_unavailable(self) -> bool:
        return str(self) in {"HTTP_403", "HTTP_429", "NETWORK_ERROR", "NETWORK_TIMEOUT"} or (
            str(self).startswith("HTTP_5"))


def public_url(url: str) -> bool:
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
        return (parts.scheme == "https" and bool(host) and not parts.username
                and not parts.password and not any(x in host for x in
                    ("sci-hub", "scihub", "libgen", "annas-archive")))
    except ValueError:
        return False


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not public_url(newurl):
            raise RetrievalError("UNSAFE_REDIRECT")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class HttpClient:
    def __init__(self, timeout: float = 30):
        self.timeout = timeout
        self.opener = build_opener(SafeRedirect())

    def _open(self, url: str):
        if not public_url(url):
            raise RetrievalError("UNSAFE_URL")
        try:
            return self.opener.open(Request(url, headers={"User-Agent": "uestc-paper/0.1"}),
                                    timeout=self.timeout)
        except HTTPError as exc:
            raise RetrievalError(f"HTTP_{exc.code}") from None
        except TimeoutError:
            raise RetrievalError("NETWORK_TIMEOUT") from None
        except URLError as exc:
            code = "NETWORK_TIMEOUT" if isinstance(exc.reason, TimeoutError) else "NETWORK_ERROR"
            raise RetrievalError(code) from None
        except (OSError, ValueError, HTTPException):
            raise RetrievalError("NETWORK_ERROR") from None

    def json(self, url: str) -> dict:
        try:
            with self._open(url) as response:
                raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise RetrievalError("METADATA_TOO_LARGE")
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise RetrievalError("INVALID_METADATA")
            return result
        except TimeoutError:
            raise RetrievalError("NETWORK_TIMEOUT") from None
        except (OSError, HTTPException):
            raise RetrievalError("NETWORK_ERROR") from None
        except ValueError:
            raise RetrievalError("INVALID_METADATA") from None

    def download(self, url: str, destination: Path) -> None:
        try:
            with self._open(url) as response, destination.open("xb") as output:
                if "html" in response.headers.get("Content-Type", "").lower():
                    raise RetrievalError("HTML_NOT_PDF")
                size = 0
                while chunk := response.read(64 * 1024):
                    if size == 0 and not chunk.startswith(b"%PDF"):
                        raise RetrievalError("INVALID_PDF_MAGIC")
                    size += len(chunk)
                    if size > MAX_PDF_BYTES:
                        raise RetrievalError("PDF_TOO_LARGE")
                    output.write(chunk)
        except TimeoutError:
            raise RetrievalError("NETWORK_TIMEOUT") from None
        except HTTPException:
            raise RetrievalError("NETWORK_ERROR") from None
        except OSError:
            raise RetrievalError("DOWNLOAD_IO_ERROR") from None
