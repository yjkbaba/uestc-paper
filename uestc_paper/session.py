"""Conservative non-secret session inspection."""

from .config import Config


def profile_present(config: Config) -> bool:
    return (config.profile / "Default").is_dir()


def institution_session(config: Config) -> str:
    """File presence cannot prove authentication or entitlement; never read cookie contents."""
    if not profile_present(config):
        return "MISSING"
    directory = config.profile / "Default"
    candidates = [directory / "Cookies", directory / "Network" / "Cookies"]
    if any(path.is_file() and path.stat().st_size > 0 for path in candidates):
        return "UNKNOWN"
    storage = directory / "Local Storage"
    if storage.is_dir() and any(path.is_file() for path in storage.rglob("*")):
        return "UNKNOWN"
    return "MISSING"
