"""Read-only current-desktop top-level Save As detection; no control inspection."""

import ctypes
import sys
import time
from ctypes import wintypes


def save_as_windows():
    if sys.platform != 'win32':
        raise OSError('WINDOW_ENUMERATION_UNAVAILABLE')
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    found = set()

    @callback_type
    def visit(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            title = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, title, len(title))
            if title.value.strip().casefold() in {'save as', '另存为'}:
                found.add(hwnd)
        return True

    if not user32.EnumWindows(visit, 0):
        raise OSError('WINDOW_ENUMERATION_FAILED')
    return found  # Handles remain local; no titles or handles are logged.


class SaveAsObservation:
    def __init__(self, snapshot=save_as_windows, clock=time.monotonic):
        self.snapshot = snapshot
        self.clock = clock
        self.before = snapshot()
        self.detected = None
        print('NATIVE_SAVE_AS_SNAPSHOT_READY')

    def observe(self, pump, files):
        deadline = self.clock() + 10
        while True:
            new = self.snapshot() - self.before
            if len(new) > 1:
                return 'NATIVE_SAVE_AS_AMBIGUOUS'
            if new:
                self.detected = next(iter(new))
                print('NATIVE_SAVE_AS_DETECTED: window_title_category=SAVE_AS; '
                      'appeared_after_click=true')
                return 'NATIVE_SAVE_AS_DETECTED'
            if self.clock() >= deadline:
                break
            files.poll()
            pump(500)
        print('NATIVE_SAVE_AS_NOT_DETECTED')
        # Passive browser-event/file observation only; no further UI action or save.
        deadline = self.clock() + 30
        while self.clock() < deadline:
            files.poll()
            pump(500)
        files.poll()
        return 'NATIVE_SAVE_AS_NOT_DETECTED'
