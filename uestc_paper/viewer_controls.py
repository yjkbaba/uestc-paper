"""Secret-free evidence and conservative main-toolbar download selection."""

import json

EVIDENCE = '''el => {
    const safe = v => /^(download|下载|save|保存|save to drive|save to google drive)$/i.test(
        (v||'').trim()) ? v.trim() : ((v||'').trim() ? 'OTHER' : 'EMPTY');
    const ancestors=[]; let n=el;
    while(n && ancestors.length<20) {
        if(n.tagName) ancestors.push(n.tagName);
        n=n.parentElement || (n.getRootNode && n.getRootNode().host);
    }
    const icon=el.getAttribute('iron-icon') || '';
    return {tag:el.tagName, role:el.getAttribute('role') === 'button' ? 'button' : 'OTHER',
        aria:safe(el.getAttribute('aria-label')), title:safe(el.getAttribute('title')),
        text:safe(el.innerText), main_toolbar:ancestors.includes('VIEWER-TOOLBAR'),
        download_controls:ancestors.includes('VIEWER-DOWNLOAD-CONTROLS'),
        drive_controls:ancestors.includes('VIEWER-SAVE-TO-DRIVE-CONTROLS'),
        menu:ancestors.some(t => ['CR-ACTION-MENU','CR-MENU-SELECTOR'].includes(t)),
        download_icon: /(^|:)download$/.test(icon)};
}'''


def evidence(control, index, page_index, frame_index):
    data = control.evaluate(EVIDENCE)
    data.update(index=index, page_index=page_index, frame_index=frame_index,
                frame_category='PDF_VIEWER', visible=control.is_visible(),
                enabled=control.is_enabled(), bounding_box=control.bounding_box())
    print('VIEWER_DOWNLOAD_CANDIDATE: ' + json.dumps(data, ensure_ascii=True))
    return data


def select_candidate(records):
    eligible = [i for i, d in enumerate(records) if d['visible'] and d['enabled']
                and d['main_toolbar'] and not d['drive_controls'] and not d['menu']]
    exact = [i for i in eligible if records[i]['aria'].casefold() in {'download', '下载'}]
    if exact:
        eligible = exact
    standard = [i for i in eligible if records[i]['download_controls']
                and (records[i]['download_icon']
                     or records[i]['title'].casefold() in {'download', '下载'})]
    if standard:
        eligible = standard
    return eligible[0] if len(eligible) == 1 else None
