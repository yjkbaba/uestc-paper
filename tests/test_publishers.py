import pytest

from uestc_paper.publishers.ieee import IEEEAdapter
from uestc_paper.resolver import Metadata


@pytest.mark.parametrize("doi,url,expected", [
    ("10.1109/test", "", True),
    ("10.1234/test", "https://ieeexplore.ieee.org/document/123", True),
    ("10.1234/test", "https://ieeexplore.ieee.org.evil.test/a", False),
    ("10.11090/test", "", False), ("10.1016/test", "", False)])
def test_matches(doi, url, expected):
    assert IEEEAdapter().matches(Metadata(doi, url=url)) is expected


def test_resolution():
    adapter = IEEEAdapter()
    assert adapter.resolve(Metadata("10.1109/test")).landing_url == "https://doi.org/10.1109/test"
    assert adapter.resolve(Metadata("10.1234/test")).status == "PUBLISHER_UNSUPPORTED"
