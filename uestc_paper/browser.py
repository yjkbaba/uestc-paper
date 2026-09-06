"""Visible local persistent browser."""

import json
import importlib.util
import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

from .config import Config


class BrowserError(Exception):
    pass


def browser_choice(playwright) -> tuple[str | None, Path | None]:
    chromium = Path(playwright.chromium.executable_path)
    if chromium.is_file():
        return None, chromium
    for channel, relative, command in (
        ("chrome", "Google/Chrome/Application/chrome.exe", "google-chrome"),
        ("msedge", "Microsoft/Edge/Application/msedge.exe", "microsoft-edge"),
    ):
        candidates = [Path(os.environ[key]) / relative
                      for key in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")
                      if os.environ.get(key)]
        if shutil.which(command):
            candidates.append(Path(shutil.which(command)))
        if channel == "chrome":
            candidates.append(Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))
        for candidate in candidates:
            if candidate.is_file():
                return channel, candidate
    return None, None


def runtime_status() -> str:
    if importlib.util.find_spec("playwright") is None:
        return "PLAYWRIGHT_MISSING"
    cache = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or
                 (Path(os.environ.get("LOCALAPPDATA", Path.home() / ".cache")) / "ms-playwright"))
    patterns = ("chromium-*/chrome-win*/chrome.exe", "chromium-*/chrome-linux*/chrome",
                "chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium")
    if any(path.is_file() for pattern in patterns for path in cache.glob(pattern)):
        return "READY"
    fake = SimpleNamespace(chromium=SimpleNamespace(executable_path=str(cache / "missing")))
    return "READY" if browser_choice(fake)[1] else "BROWSER_MISSING"


def _disable_password_saving(config: Config) -> None:
    directory = config.profile / "Default"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "Preferences"
    preferences = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    preferences["credentials_enable_service"] = False
    preferences.setdefault("profile", {})["password_manager_enabled"] = False
    preferences.setdefault("autofill", {})["profile_enabled"] = False
    preferences.setdefault("plugins", {})["always_open_pdf_externally"] = False
    _download_preferences(preferences, config)
    path.write_text(json.dumps(preferences), encoding="utf-8")


def _download_preferences(preferences, config):
    directory = (config.runtime / "download-capture").resolve()
    directory.mkdir(parents=True, exist_ok=True)
    download = preferences.setdefault("download", {})
    download["prompt_for_download"] = False
    download["default_directory"] = str(directory)


def configure_download_preferences(config):
    """Call only with the dedicated browser closed; preserve other preferences."""
    path = config.profile / "Default" / "Preferences"
    preferences = json.loads(path.read_text(encoding="utf-8"))
    _download_preferences(preferences, config)
    preferences.setdefault("plugins", {})["always_open_pdf_externally"] = False
    path.write_text(json.dumps(preferences), encoding="utf-8")


@contextmanager
def persistent_browser(config: Config):
    if os.environ.get("DEBUG") or os.environ.get("PWDEBUG"):
        raise BrowserError("DEBUG_LOGGING_DISABLED: unset DEBUG and PWDEBUG before authentication.")
    from playwright.sync_api import Error, sync_playwright

    config.setup()
    # A local exclusive lock prevents this application from editing an in-use profile.
    lock = config.runtime / "browser.lock"
    try:
        handle = lock.open("x")
    except FileExistsError:
        raise BrowserError("PROFILE_IN_USE: close the other uestc-paper browser first.") from None
    try:
        with handle, sync_playwright() as playwright:
            channel, executable = browser_choice(playwright)
            if executable is None:
                raise BrowserError("BROWSER_MISSING: run python -m playwright install chromium")
            try:
                _disable_password_saving(config)
            except (ValueError, TypeError, AttributeError):
                raise BrowserError("PROFILE_INVALID: reset the local profile before retrying.") from None
            context = playwright.chromium.launch_persistent_context(
                str(config.profile), headless=False, channel=channel, accept_downloads=True,
                downloads_path=str(config.runtime),
            )
            try:
                yield context
            finally:
                context.close()
    except Error:
        # Playwright errors can include authentication URLs; do not print raw errors.
        raise BrowserError("BROWSER_ACTION_FAILED: browser closed, blocked, or unavailable.") from None
    finally:
        lock.unlink(missing_ok=True)
