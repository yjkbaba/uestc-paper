"""UIA Save only in the exact newly detected Chrome Save As window."""

import re
import ctypes
import sys
import time
import uuid
from ctypes import wintypes
from pathlib import Path


def _chrome_process(pid):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return False
    try:
        path = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(path))
        return bool(kernel.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size))
                    and Path(path.value).name.lower() in {'chrome.exe', 'msedge.exe'})
    finally:
        kernel.CloseHandle(handle)


def _label(value, expected):
    value = value.replace('&', '').strip()
    return bool(re.fullmatch(r'(?:' + expected + r')(?:\s*\([a-z]\))?\s*[:：]?', value, re.I))


class UIASaveDialog:
    def __init__(self, handle):
        from pywinauto import Desktop
        self.window = Desktop(backend='uia').window(handle=handle)

    def category_valid(self):
        return (self.window.window_text().strip().casefold() in {'save as', '另存为'}
                and _chrome_process(self.window.process_id()))

    def filename_edits(self):
        return [c for c in self.window.descendants(control_type='Edit')
                if _label(c.element_info.name, r'file name|filename|文件名')
                and c.is_visible() and c.is_enabled()]

    def save_buttons(self):
        return [c for c in self.window.descendants(control_type='Button')
                if _label(c.element_info.name, r'save|保存')
                and c.is_visible() and c.is_enabled()]


def save_new_dialog(observer, directory, pump, ui_factory=UIASaveDialog,
                    platform=None, clock=time.monotonic):
    if (platform or sys.platform) != 'win32':
        return 'NATIVE_SAVE_AS_UNSUPPORTED', None
    handle = observer.detected

    def still_new():
        return (handle is not None and handle not in observer.before
                and handle in observer.snapshot())

    if not still_new():
        return 'NATIVE_SAVE_AS_NOT_DETECTED', None
    target = (directory / f'{uuid.uuid4().hex}.pdf').resolve()
    directory.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.with_suffix('.pdf.crdownload').exists():
        return 'NATIVE_SAVE_AS_PATH_CONFLICT', None
    try:
        dialog = ui_factory(handle)
        if not dialog.category_valid():
            return 'NATIVE_SAVE_AS_NOT_DETECTED', None
        edits = dialog.filename_edits()
        if len(edits) != 1:
            return 'NATIVE_SAVE_AS_FILENAME_NOT_UNIQUE', None
        buttons = dialog.save_buttons()
        if len(buttons) != 1:
            return 'NATIVE_SAVE_AS_BUTTON_NOT_UNIQUE', None
        if not still_new() or not dialog.category_valid():
            return 'NATIVE_SAVE_AS_NOT_DETECTED', None
        edits[0].set_edit_text(str(target))
        if edits[0].get_value() != str(target):
            return 'NATIVE_SAVE_AS_PATH_MISMATCH', None
        print('SAVE_AS_PATH_CONFIRMED')
        if not still_new() or not dialog.category_valid():
            return 'NATIVE_SAVE_AS_NOT_DETECTED', None
        # UIA Invoke pattern: one action, no keyboard or coordinate input.
        buttons[0].invoke()
        print('NATIVE_SAVE_AS_SAVE_DISPATCHED')
        deadline = clock() + 10
        while clock() < deadline:
            if not still_new():
                return 'NATIVE_SAVE_AS_SAVE_DISPATCHED', target
            pump(500)
        return 'NATIVE_SAVE_AS_SAVE_UNCONFIRMED', None
    except Exception:
        # UIA exceptions can include arbitrary window contents. Never print them.
        return 'NATIVE_SAVE_AS_SAVE_UNCONFIRMED', None
