from uestc_paper.http import RetrievalError, public_url
from uestc_paper.oa import EuropePMCResolver
from uestc_paper.resolver import resolve_metadata


class FakeClient:
    def __init__(self, data):
        self.data = data

    def json(self, url):
        return self.data


def record(style="pdf", availability="Open access", doi="10.1234/abc"):
    return {"resultList": {"result": [{"doi": doi, "fullTextUrlList": {"fullTextUrl": [
        {"url": "https://europepmc.org/articles/PMC1?pdf=render", "documentStyle": style,
         "availability": availability}]}}]}}


def test_oa_found():
    assert EuropePMCResolver(FakeClient(record())).resolve("10.1234/abc").status == "OA_FOUND"


def test_no_html_or_subscription():
    for data in [record(style="html"), record(availability="Subscription required"),
                 record(doi="10.1234/other"), {"resultList": {"result": []}}]:
        assert EuropePMCResolver(FakeClient(data)).resolve("10.1234/abc").status == "OA_NOT_FOUND"


def test_network_failure():
    class BrokenClient:
        def json(self, url):
            raise RetrievalError("HTTP_429")
    result = EuropePMCResolver(BrokenClient()).resolve("10.1234/abc")
    assert result.status == "OA_TEMPORARILY_UNAVAILABLE"
    assert result.detail == "HTTP_429"


def test_forbidden_sources():
    for url in ["https://sci-hub.se/a.pdf", "file:///a.pdf", "https://user:pass@host/a"]:
        assert not public_url(url)


def test_metadata():
    result = resolve_metadata("10.1234/abc", FakeClient({"message": {
        "DOI": "10.1234/abc", "title": ["An article"], "publisher": "IEEE"}}))
    assert result.status == "METADATA_FOUND"
    assert result.title == "An article"
