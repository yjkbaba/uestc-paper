"""Lawful open-access resolution."""

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode

from .http import HttpClient, RetrievalError, public_url
from .resolver import normalize_doi


@dataclass(frozen=True)
class OAResult:
    status: str
    pdf_url: str | None = None
    source: str = "Europe PMC"
    detail: str = ""


class OAResolver(Protocol):
    def resolve(self, doi: str) -> OAResult: ...


class EuropePMCResolver:
    """Single DOI lookup; only explicitly Open access, PDF-style locations qualify."""

    def __init__(self, client: HttpClient | None = None):
        self.client = client or HttpClient()

    def resolve(self, doi: str) -> OAResult:
        params = urlencode({"query": f'DOI:"{doi}"', "format": "json",
                            "resultType": "core", "pageSize": "1"})
        try:
            data = self.client.json("https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
                                    + params)
            records = data["resultList"]["result"]
            for record in records:
                if normalize_doi(record.get("doi", "")) != doi:
                    continue
                for location in record.get("fullTextUrlList", {}).get("fullTextUrl", []):
                    url = location.get("url", "")
                    if (location.get("documentStyle", "").lower() == "pdf"
                            and location.get("availability", "").lower() == "open access"
                            and public_url(url)):
                        return OAResult("OA_FOUND", url)
            return OAResult("OA_NOT_FOUND")
        except RetrievalError as exc:
            status = "OA_TEMPORARILY_UNAVAILABLE" if exc.temporarily_unavailable else "OA_LOOKUP_FAILED"
            return OAResult(status, detail=str(exc))
        except (ValueError, KeyError, TypeError, AttributeError):
            return OAResult("OA_LOOKUP_FAILED", detail="INVALID_METADATA")
