"""Command-line entry point."""

import argparse

from .config import Config


def login(config: Config) -> int:
    from .browser import persistent_browser
    from .config import UESTC_ENTRY
    from .session import institution_session

    with persistent_browser(config) as context:
        page = context.new_page()
        page.goto(UESTC_ENTRY, wait_until="domcontentloaded", timeout=60000)
        print("MANUAL_AUTH_REQUIRED: complete authentication yourself in the visible browser.")
        print("USER_AUTH_REQUIRED")
        print("Do not enter passwords, OTPs or CAPTCHA answers in this terminal.")
        input("Press Enter after completing or cancelling browser authentication: ")
    print(f"Local session evidence: {institution_session(config)}")
    print("LOGIN_STATE_UNKNOWN: local browser state does not prove institutional access.")
    return 2


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="uestc-paper", description="Retrieve one authorized paper.")
    result.add_argument("--home", help="Local root (default: UESTC_PAPER_HOME or current directory)")
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("setup", help="Prepare local runtime and download directories")
    commands.add_parser("login", help="Open visible browser for manual UESTC authentication")
    commands.add_parser("status", help="Inspect local runtime and session state")
    get = commands.add_parser("get", help="Retrieve one DOI, open access first")
    get.add_argument("doi")
    get.add_argument("--no-browser", action="store_true", help="Stop before institutional browser")
    get.add_argument("--wait-seconds", type=int, default=300,
                     help="Time allowed for user authentication/resource entry (1–3600, default: 300)")
    return result


def _run(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    config = Config.load(args.home)
    if args.command == "setup":
        from .browser import runtime_status

        config.setup()
        print(f"SETUP_READY\nDownload directory: {config.downloads}")
        state = runtime_status()
        print(f"Browser runtime: {state}")
        if state != "READY":
            print("Install package dependencies and run: python -m playwright install chromium")
        return 0
    if args.command == "login":
        return login(config)
    if args.command == "status":
        from .browser import runtime_status
        from .session import institution_session, profile_present

        print(f"Browser runtime: {runtime_status()}")
        print(f"Browser profile: {'FOUND' if profile_present(config) else 'MISSING'}")
        print(f"Institution session: {institution_session(config)}")
        print(f"Download directory: {config.downloads}")
        print(f"Download directory exists: {config.downloads.is_dir()}")
        return 0
    from .workflow import get_paper

    if not 1 <= args.wait_seconds <= 3600:
        print("INVALID_TIMEOUT: --wait-seconds must be between 1 and 3600.")
        return 2
    return get_paper(args.doi, config, no_browser=args.no_browser, timeout=args.wait_seconds)


def main(argv: list[str] | None = None) -> int:
    from .browser import BrowserError

    try:
        return _run(argv)
    except (KeyboardInterrupt, EOFError):
        print("CANCELLED")
        return 130
    except BrowserError as exc:
        print(str(exc))
        return 2
    except (OSError, ImportError):
        print("LOCAL_RUNTIME_ERROR: check installation, file permissions and available disk space.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
