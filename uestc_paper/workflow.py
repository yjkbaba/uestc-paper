"""One DOI, OA first, verified output only."""

import hashlib
import shutil
import tempfile
import uuid
from pathlib import Path

from .native_browser import persistent_browser
from .http import HttpClient, RetrievalError
from .oa import EuropePMCResolver
from .publishers.ieee import IEEEAdapter
from .resolver import normalize_doi, resolve_metadata
from .session import institution_session
from .verify import verify_pdf


def _save_verified(path, metadata, config, route) -> bool:
    result = verify_pdf(path, metadata.doi, metadata.title)
    print(f"Verification: {result.status}; pages={result.pages}; size={result.size}; "
          f"identity={result.identity}")
    if not result.valid or result.identity != "MATCH":
        print("CANDIDATE_UNVERIFIED: no final file saved.")
        return False
    digest = hashlib.sha256(metadata.doi.encode()).hexdigest()[:16]
    destination = config.downloads / f"{digest}-{uuid.uuid4().hex[:8]}.pdf"
    with destination.open("xb") as output:
        try:
            with path.open("rb") as source:
                shutil.copyfileobj(source, output)
        except OSError:
            output.close()
            destination.unlink(missing_ok=True)
            raise
    path.unlink()
    print(f"SAVED ({route}): {destination}")
    print("SUCCESS")
    return True


def get_paper(identifier, config, *, no_browser=False, timeout=300) -> int:
    try:
        doi = normalize_doi(identifier)
    except ValueError as exc:
        print(f"INVALID_DOI: {exc}")
        return 2
    print(f"DOI_NORMALIZED: {doi}")
    config.setup()
    client = HttpClient()
    print("METADATA_LOOKUP")
    metadata = resolve_metadata(doi, client)
    print(metadata.status)
    print("OA_LOOKUP: Europe PMC (coverage is limited)")
    oa = EuropePMCResolver(client).resolve(doi)
    print(oa.status)
    if oa.status in {"OA_LOOKUP_FAILED", "OA_TEMPORARILY_UNAVAILABLE"}:
        print(f"OA lookup incomplete: {oa.detail}. No OA retry; normal institutional UI may follow.")
    with tempfile.TemporaryDirectory(prefix="paper-", dir=config.runtime) as directory:
        temporary = Path(directory) / "article.part"
        if oa.status == "OA_FOUND":
            print("OA_DOWNLOAD")
            try:
                client.download(oa.pdf_url, temporary)
                if _save_verified(temporary, metadata, config, "OA / Europe PMC"):
                    return 0
                print("OA_VERIFICATION_FAILED")
            except RetrievalError as exc:
                print(f"OA_DOWNLOAD_FAILED: {exc}")
                if exc.temporarily_unavailable:
                    print("OA_TEMPORARILY_UNAVAILABLE")
                print("No OA retry. Institutional fallback uses the publisher's normal visible UI.")
            temporary.unlink(missing_ok=True)
        print(f"Institution session: {institution_session(config)}")
        print(f"INSTITUTION_SESSION_{institution_session(config)}")
        adapter = IEEEAdapter()
        resolution = adapter.resolve(metadata)
        print(resolution.status)
        if resolution.status != "PUBLISHER_RESOLVED":
            print("UNAVAILABLE: V0.1 institutional retrieval supports IEEE only.")
            return 2
        if no_browser:
            print("MANUAL_ACTION_REQUIRED: browser disabled for this invocation.")
            return 2
        print("VISIBLE_BROWSER: authentication and entitlement require manual confirmation.")
        with persistent_browser(config) as context:
            result = adapter.download(context, resolution, temporary, timeout)
            print(result.status)
            if result.status == "DOWNLOAD_RECEIVED":
                if _save_verified(temporary, metadata, config, result.route):
                    print('E2E_SUCCESS')
                    return 0
        print('RETRIEVAL_UNVERIFIED: allowed retrieval routes ended without a verified PDF.')
        return 2
