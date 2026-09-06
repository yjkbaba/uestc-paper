from types import SimpleNamespace

import pytest

from uestc_paper.native_save import _label, save_new_dialog


@pytest.mark.parametrize('case,expected', [
    ('none', 'NATIVE_SAVE_AS_NOT_DETECTED'),
    ('old', 'NATIVE_SAVE_AS_NOT_DETECTED'),
    ('edits', 'NATIVE_SAVE_AS_FILENAME_NOT_UNIQUE'),
    ('buttons', 'NATIVE_SAVE_AS_BUTTON_NOT_UNIQUE'),
    ('mismatch', 'NATIVE_SAVE_AS_PATH_MISMATCH'),
    ('remains', 'NATIVE_SAVE_AS_SAVE_UNCONFIRMED'),
    ('ok', 'NATIVE_SAVE_AS_SAVE_DISPATCHED'),
    ('unsupported', 'NATIVE_SAVE_AS_UNSUPPORTED'),
])
def test_bound_native_save_only_once(tmp_path, case, expected):
    clock, writes, clicks, factories = [0], [], [], []
    live = {2}
    observer = SimpleNamespace(detected=None if case == 'none' else 2,
                               before={2} if case == 'old' else {1}, snapshot=lambda: live)

    def invoke():
        clicks.append(True)
        if case != 'remains':
            live.clear()

    def factory(handle):
        assert handle == 2
        factories.append(handle)
        edit = SimpleNamespace(set_edit_text=lambda value: writes.append(value),
                               get_value=lambda: '' if case == 'mismatch' else writes[-1])
        return SimpleNamespace(category_valid=lambda: True,
                               filename_edits=lambda: [edit] * (2 if case == 'edits' else 1),
                               save_buttons=lambda: [SimpleNamespace(invoke=invoke)] * (
                                   2 if case == 'buttons' else 1))

    def pump(ms):
        clock[0] += ms/1000

    status, target = save_new_dialog(observer, tmp_path, pump, factory,
                                     'linux' if case == 'unsupported' else 'win32',
                                     lambda: clock[0])
    assert status == expected
    assert len(clicks) == int(case in {'ok', 'remains'})
    if case in {'none', 'old', 'unsupported'}:
        assert not factories and not writes
    if case == 'ok':
        assert target.is_absolute() and target.parent == tmp_path
        assert target.suffix == '.pdf'
        assert writes == [str(target)]
    else:
        assert target is None


def test_uia_labels_are_exact_and_localized():
    assert _label('文件名(N):', r'file name|filename|文件名')
    assert _label('保存(&S)', r'save|保存')
    assert _label('File name:', r'file name|filename|文件名')
    assert not _label('Password', r'file name|filename|文件名')
    assert not _label('Save to Google Drive', r'save|保存')
