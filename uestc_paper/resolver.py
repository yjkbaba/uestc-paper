"""DOI and metadata resolution."""

import re
from dataclasses import dataclass
from urllib.parse import quote, unquote, urlsplit


def normalize_doi(value: str) -> str:
    value = value.strip()
    if value.lower().startswith("doi:"):
        value = value[4:].strip()
    elif value.lower().startswith(("https://", "http://")):
        parts = urlsplit(value)
        if parts.netloc.lower() not in {"doi.org", "dx.doi.org"}:
            raise ValueError("Expected a DOI or doi.org URL; publisher URLs are not supported yet.")
        value = unquote(parts.path.lstrip("/"))
    if not re.fullmatch(r"10\.\d{4,9}/[^\s\x00-\x1f\x7f]+", value):
        raise ValueError("Invalid DOI. Use 10.1234/example, doi:10.1234/example or a doi.org URL.")
    return value.lower()


@dataclass(frozen=True)
class Metadata:
    doi: str
    title: str = ""
    publisher: str = ""
    url: str = ""
    status: str = "METADATA_UNAVAILABLE"


def resolve_metadata(doi: str, client=None) -> Metadata:
    from .http import HttpClient, RetrievalError

    client = client or HttpClient()
    try:
        data = client.json("https://api.crossref.org/works/" + quote(doi, safe=""))["message"]
        if normalize_doi(data["DOI"]) != doi:
            return Metadata(doi, status="METADATA_MISMATCH")
        return Metadata(doi, (data.get("title") or [""])[0], data.get("publisher", ""),
                        data.get("URL", ""), "METADATA_FOUND")
    except (RetrievalError, KeyError, ValueError, TypeError, IndexError):
        return Metadata(doi)
