"""Independent PDF verification."""

import re
import logging
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from .http import MAX_PDF_BYTES


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    status: str
    size: int = 0
    pages: int = 0
    identity: str = "UNKNOWN"


def _words(value: str) -> str:
    return " ".join(re.findall(r"\w+", value.lower()))


def verify_pdf(path: Path, doi: str | None = None, title: str = "") -> VerificationResult:
    path = Path(path)
    if not path.is_file():
        return VerificationResult(False, "FILE_MISSING")
    previous_logging_level = logging.root.manager.disable
    try:
        # Third-party parser diagnostics can include arbitrary document contents.
        # Expose only our structured result during this synchronous verification.
        logging.disable(logging.CRITICAL)
        size = path.stat().st_size
        with path.open("rb") as stream:
            if stream.read(4) != b"%PDF":
                return VerificationResult(False, "INVALID_PDF_MAGIC", size)
        if not 512 <= size <= MAX_PDF_BYTES:
            return VerificationResult(False, "INVALID_PDF_SIZE", size)
        with path.open("rb") as stream:
            reader = PdfReader(stream, strict=True)
            if reader.is_encrypted:
                return VerificationResult(False, "ENCRYPTED_PDF", size)
            pages = len(reader.pages)
            if not 1 <= pages <= 1000:
                return VerificationResult(False, "INVALID_PAGE_COUNT", size, pages)
            metadata = reader.metadata or {}
            # Header evidence only: reference-list DOIs must not establish article identity.
            first_page = (reader.pages[0].extract_text() or "")[:20000]
            meta_text = " ".join(str(value) for value in metadata.values())
            text = meta_text + "\n" + first_page
            error = re.compile(r"^\s*(access denied|403 forbidden|404 not found|"
                               r"sign in to access|log in to access|article preview|"
                               r"preview only|this is a preview|error\s*[:\d])", re.I)
            if any(error.search(value) for value in
                   (first_page, str(metadata.get("/Title", "")))):
                return VerificationResult(False, "ERROR_OR_PREVIEW_PDF", size, pages)
            identity = "UNKNOWN"
            found = re.findall(r"10\.\d{4,9}/[^\s<>\"]+", text.lower())
            found = [value.rstrip(".,;") for value in found]
            if doi and doi.lower() in found:
                identity = "MATCH"
            elif title and len(_words(title)) >= 15 and _words(title) in _words(text):
                identity = "MATCH"
            elif doi and found:
                return VerificationResult(False, "DOI_MISMATCH", size, pages, "MISMATCH")
            status = "PDF_VERIFIED" if identity == "MATCH" else "PDF_IDENTITY_UNCONFIRMED"
            return VerificationResult(True, status, size, pages, identity)
    except Exception:
        # Parser errors may contain document contents; do not expose them in operational logs.
        return VerificationResult(False, "PDF_PARSE_ERROR")
    finally:
        logging.disable(previous_logging_level)
