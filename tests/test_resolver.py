import pytest

from uestc_paper.resolver import normalize_doi


@pytest.mark.parametrize("value", ["10.1234/AbC", " doi:10.1234/AbC ",
                                   "https://doi.org/10.1234/AbC",
                                   "https://doi.org/10.1234%2FAbC?source=test"])
def test_normalize(value):
    assert normalize_doi(value) == "10.1234/abc"


@pytest.mark.parametrize("value", ["", "title", "10.xxxx/xxxxx", "10.123/abc",
                                   "10.1234/", "10.1234/a b", "10.1234/a\nX",
                                   "https://example.com/10.1234/abc"])
def test_malformed(value):
    with pytest.raises(ValueError, match="DOI"):
        normalize_doi(value)
