import pytest
from pypdf import PdfWriter

from uestc_paper.verify import verify_pdf


def make_pdf(path, title="An example research article", doi="10.1234/abc", pages=1):
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=600, height=800)
    writer.add_metadata({"/Title": title, "/DOI": doi, "/Subject": "test " * 100})
    with path.open("wb") as output:
        writer.write(output)
    return path


def test_valid(tmp_path):
    result = verify_pdf(make_pdf(tmp_path / "ok.pdf"), "10.1234/abc")
    assert result.valid and result.pages == 1 and result.identity == "MATCH"


@pytest.mark.parametrize("content,status", [
    (b"<html>Login password</html>", "INVALID_PDF_MAGIC"),
    (b"random", "INVALID_PDF_MAGIC"), (b"%PDF-1.4", "INVALID_PDF_SIZE"),
    (b"%PDF" + b"broken" * 200, "PDF_PARSE_ERROR")])
def test_invalid(tmp_path, content, status):
    path = tmp_path / "bad.pdf"
    path.write_bytes(content)
    result = verify_pdf(path)
    assert not result.valid and result.status == status


def test_missing(tmp_path):
    assert verify_pdf(tmp_path / "missing.pdf").status == "FILE_MISSING"


def test_error_pdf(tmp_path):
    result = verify_pdf(make_pdf(tmp_path / "error.pdf", title="Access denied"), "10.1234/abc")
    assert result.status == "ERROR_OR_PREVIEW_PDF"
    assert not result.valid


def test_identity(tmp_path):
    path = make_pdf(tmp_path / "other.pdf", doi="10.1234/other")
    assert verify_pdf(path, "10.1234/abc").status == "DOI_MISMATCH"
    path = make_pdf(tmp_path / "unknown.pdf", doi="")
    assert verify_pdf(path, "10.1234/abc").identity == "UNKNOWN"


def test_no_pages(tmp_path):
    assert verify_pdf(make_pdf(tmp_path / "empty.pdf", pages=0)).status == "INVALID_PAGE_COUNT"
