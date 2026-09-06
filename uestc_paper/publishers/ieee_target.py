"""IEEE article identity, independent of WebVPN URL encoding."""

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlsplit


def canonical_article_id(url):
    parts = urlsplit(url)
    match = re.search(r"/document/(\d+)(?:/|$)", parts.path)
    if match:
        return match.group(1)
    values = parse_qs(parts.query).get("arnumber", [])
    return values[0] if len(values) == 1 and re.fullmatch(r"\d{1,20}", values[0]) else ""


@dataclass(frozen=True)
class TargetResult:
    status: str
    page: object = None

    def __bool__(self):
        return self.status == "IEEE_TARGET_ARTICLE_OPENED"
