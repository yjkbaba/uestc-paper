"""One native Viewer download; no download overrides or URL replay."""

import shutil
import os
import sys
import time
import uuid
from types import SimpleNamespace

from playwright.sync_api import Error

from ..uestc import is_webvpn_url
from ..verify import verify_pdf
from ..viewer_controls import evidence
from .base import DownloadResult


def download_viewer(context, destination, resolution, completion_seconds=120):
    from ..viewer_download_diagnostic import viewer_control
    from ..viewer_click_observation import Files

    pages = [p for p in context.pages if not p.is_closed() and is_webvpn_url(p.url)]
    found = viewer_control(SimpleNamespace(pages=pages))
    if not found:
        return DownloadResult('PDF_VIEWER_DOWNLOAD_CONTROL_INACCESSIBLE')
    page, control = found
    data = evidence(control, 0, pages.index(page), -1)
    # Enforce exact Download identity even if a future diagnostic selector is relaxed.
    names = {data['aria'].casefold(), data['title'].casefold()}
    if not (data['visible'] and data['enabled'] and data['main_toolbar']
            and not data['drive_controls'] and not data['menu']
            and names & {'download', '下载'}):
        return DownloadResult('VIEWER_DOWNLOAD_AMBIGUOUS')
    print('VIEWER_DOWNLOAD_CONTROL_FOUND')
    directory = destination.parent.parent / 'download-capture'
    directory.mkdir(parents=True, exist_ok=True)
    files = Files([directory])
    downloads, attached = [], []
    max_bytes = 0
    native_target = None

    def receive(download):
        if not downloads:
            downloads.append(download)
            print('DOWNLOAD_RECEIVED: source=Playwright')

    def attach(p):
        p.on('download', receive)
        attached.append(p)

    for p in pages:
        attach(p)
    context.on('page', attach)
    try:
        try:
            box = control.bounding_box()
            if not box or not control.is_visible() or not control.is_enabled():
                return DownloadResult('VIEWER_MOUSE_HITTEST_FAILED')
            # Hit test in the control's own frame, including open Viewer shadow roots.
            hit = control.evaluate('''el => {
                const r = el.getBoundingClientRect();
                let top = el.ownerDocument.elementFromPoint(r.x+r.width/2, r.y+r.height/2);
                while (top && top.shadowRoot) {
                    const next = top.shadowRoot.elementFromPoint(r.x+r.width/2, r.y+r.height/2);
                    if (!next || next === top) break;
                    top = next;
                }
                for (let n=top; n; n=n.parentElement || n.getRootNode().host) {
                    if (n === el) return true;
                }
                return false;
            }''')
        except Error:
            return DownloadResult('VIEWER_MOUSE_HITTEST_FAILED')
        print(f'VIEWER_MOUSE_HITTEST: passed={bool(hit)}; bounding_box=True')
        if not hit:
            return DownloadResult('VIEWER_MOUSE_HITTEST_FAILED')
        native_observer = None
        if sys.platform == 'win32':
            from ..native_save_as import SaveAsObservation
            try:
                native_observer = SaveAsObservation()
            except OSError:
                return DownloadResult('NATIVE_SAVE_AS_DETECTION_UNAVAILABLE')
        try:
            page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
            page.mouse.down()
            print('VIEWER_MOUSE_DOWN_COMPLETED')
            page.mouse.up()
            print('VIEWER_MOUSE_UP_COMPLETED')
            print('VIEWER_MOUSE_CLICK_DISPATCHED')
        except Error:
            print('VIEWER_MOUSE_INPUT_UNCONFIRMED')
        if native_observer is not None:
            try:
                native_status = native_observer.observe(page.wait_for_timeout, files)
            except OSError:
                return DownloadResult('NATIVE_SAVE_AS_DETECTION_UNAVAILABLE')
            if os.environ.get('UESTC_PAPER_NATIVE_SAVE_AS_DIAGNOSTIC') == '1':
                return DownloadResult(native_status)
            if native_status == 'NATIVE_SAVE_AS_DETECTED':
                from ..native_save import save_new_dialog
                native_status, native_target = save_new_dialog(
                    native_observer, directory, page.wait_for_timeout)
                if native_target is None:
                    return DownloadResult(native_status)
                completion_seconds = 180
            else:
                return DownloadResult(native_status)
        else:
            print('NATIVE_SAVE_AS_UNSUPPORTED')
        deadline = time.monotonic() + completion_seconds
        checked, stable = set(), {}
        while time.monotonic() < deadline:
            files.poll()
            max_bytes = max([max_bytes] + [s[0] for s in files.changed.values()])
            candidates = []
            for source, fingerprint in files.changed.items():
                if native_target is not None and source != native_target:
                    continue
                if source.suffix.lower() == '.crdownload' or not source.is_file():
                    continue
                if source.with_name(source.name + '.crdownload').exists():
                    continue
                if (source, fingerprint) in checked:
                    continue
                if stable.get(source, (None,))[0] != fingerprint:
                    stable[source] = (fingerprint, time.monotonic())
                    continue
                if time.monotonic() - stable[source][1] >= 1:
                    candidates.append((source, fingerprint))
            for source, fingerprint in candidates:
                checked.add((source, fingerprint))
                print('DOWNLOAD_FILE_COMPLETED')
                temporary = directory / f'viewer-candidate-{uuid.uuid4().hex}.part'
                shutil.copyfile(source, temporary)
                result = verify_pdf(temporary, resolution.doi)  # DOI match, not title-only.
                print(f'VIEWER_VERIFICATION: {result.status}; pages={result.pages}; '
                      f'size={result.size}; identity={result.identity}')
                if result.valid and result.identity == 'MATCH':
                    print('PDF_VERIFIED')
                    shutil.copyfile(temporary, destination)
                    temporary.unlink()
                    return DownloadResult('DOWNLOAD_RECEIVED', destination,
                                          'UESTC / IEEE / Chromium viewer download')
                temporary.unlink(missing_ok=True)
                return DownloadResult('PDF_VERIFICATION_FAILED')
            page.wait_for_timeout(250)
        return DownloadResult('DOWNLOAD_INCOMPLETE' if files.changed or downloads
                              else 'VIEWER_MOUSE_CLICK_NOT_CONFIRMED')
    finally:
        partial = any(p.suffix.lower() == '.crdownload' for p in files.changed)
        final_bytes = max([0] + [s[0] for p, s in files.changed.items()
                                if p.suffix.lower() != '.crdownload' and p.exists()])
        print(f'VIEWER_DOWNLOAD_FILES: crdownload_seen={partial}; '
              f'max_bytes={max_bytes}; final_bytes={final_bytes}')
        context.remove_listener('page', attach)
        for p in attached:
            p.remove_listener('download', receive)
