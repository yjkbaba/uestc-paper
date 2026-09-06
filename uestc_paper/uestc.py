"""UESTC resource-list navigation; no credential access or proxy URL synthesis."""

import re
import time
from urllib.parse import urlsplit

from playwright.sync_api import Error, TimeoutError as PlaywrightTimeout

from .config import UESTC_ENTRY

LIBRARY = re.compile(r"图书馆.*(?:外文|外国).*数据库|Library.*(?:database|foreign)", re.I)
LIBRARY_SHORT = re.compile(r"^(?:图书馆(?:\s*\(?Library\)?)?|Library)$", re.I)
RESOURCE = re.compile(r"(?:\bIEEE\b|\bIEL\b)", re.I)
DOMAIN = re.compile(r"输入域名.*(?:访问|资源)|domain.*(?:access|resource)", re.I)
PORTAL_MARKERS = ("校内常用资源", "图书馆常用中文数据库", "图书馆常用外文数据库")


def is_webvpn_url(url):
    host = urlsplit(url).hostname or ""
    return any(host == official or host.endswith("." + official)
               for official in ("webvpn.uestc.edu.cn", "vpn.uestc.edu.cn"))


def unique_visible(groups):
    for group in groups:
        visible = [group.nth(i) for i in range(min(group.count(), 20))
                   if group.nth(i).is_visible()]
        if len(visible) == 1:
            return visible[0]
    return None


def named_action(page, name):
    return unique_visible([page.get_by_role(role, name=name) for role in
                           ("link", "button", "menuitem", "tab")] + [page.get_by_text(name)])


def detached_transient(exc):
    if 'detached' in str(exc).lower():
        print('FRAME_DETACHED_TRANSIENT')
        return True
    return False


def portal_marker(page):
    try:
        if not is_webvpn_url(page.url):
            return None
        for marker in PORTAL_MARKERS:
            group = page.get_by_text(re.compile(re.escape(marker)))
            if any(group.nth(i).is_visible() for i in range(min(group.count(), 10))):
                return marker
        return None
    except Error as exc:
        if not detached_transient(exc):
            raise
        return None


def portal_ready(page):
    return portal_marker(page) is not None


def domain_field(page):
    return unique_visible([page.get_by_placeholder(DOMAIN), page.get_by_label(DOMAIN)])


def domain_entry(page):
    """Use only the portal's domain widget and its HTTPS protocol selector."""
    field = domain_field(page)
    if field is None:
        return False
    group = field.locator("xpath=ancestor::*[.//button or .//*[@role='button']][1]")
    if group.count() != 1:
        return False
    selects = group.locator("select")
    if selects.count() == 1:
        selects.select_option(label="https")
    elif unique_visible([group.get_by_text(re.compile(r"^https:?[/]*$", re.I))]) is None:
        return False  # Do not guess the widget's selected protocol.
    button = unique_visible([
        group.get_by_role("button", name=re.compile(r"进入|访问|前往|打开|go|access", re.I)),
        group.get_by_role("button")])
    if button is None:
        return False
    field.fill("ieeexplore.ieee.org", timeout=3000)
    print("UESTC_DOMAIN_FALLBACK")
    button.click(timeout=3000)
    return True


def is_ieee(page, *, proxied=False) -> bool:
    host = urlsplit(page.url).hostname or ""
    if not proxied:
        return host == "ieeexplore.ieee.org"
    if not is_webvpn_url(page.url):
        return False
    return page.locator("xpl-root").count() > 0 or (
        page.get_by_role("img", name=re.compile("IEEE Xplore", re.I)).count() > 0)


def portal_ieee(scope):
    try:
        return is_ieee(scope, proxied=True)
    except Error as exc:
        if not detached_transient(exc):
            raise
        return False


def wait_for_ieee_resource(context, timeout=25):
    """Observe one official resource click through redirects/bootstrap; never click again."""
    deadline = time.monotonic() + timeout
    previous = None
    while time.monotonic() < deadline:
        pages = list(context.pages)
        diagnostics = []
        found = None
        live = []
        for index, owner in enumerate(pages):
            if owner.is_closed():
                continue
            live.append(owner)
            scopes = [owner] + [f for f in owner.frames if f != owner.main_frame]
            marker = False
            search = False
            links = 0
            for scope in scopes:
                try:
                    if not is_webvpn_url(scope.url):
                        continue
                    matched = is_ieee(scope, proxied=True)
                    marker |= matched
                    if matched and found is None:
                        found = scope
                    search |= (scope.get_by_role('searchbox').count() > 0 or
                               scope.locator("input[type='search']").count() > 0)
                    links += scope.locator("a[href*='/document/'], a[href*='arnumber=']").count()
                except Error as exc:
                    detached_transient(exc)
                    if found is scope:
                        found = None
                    # A redirect/detached frame is transitional, not a failed resource entry.
                    continue
            diagnostics.append((index, urlsplit(owner.url).hostname or 'NONE',
                                'IEEE' if marker else 'UNCONFIRMED', len(owner.frames),
                                marker, search, links))
        signature = (len(pages), tuple(diagnostics))
        if signature != previous:
            print(f'IEEE_RESOURCE_PAGES: count={len(pages)}')
            for index, host, title, frames, marker, search, links in diagnostics:
                print(f'IEEE_RESOURCE_PAGE: index={index}; host={host}; title_category={title}; '
                      f'frame_count={frames}; ieee_marker={marker}; search_control={search}; '
                      f'article_links={links}')
            previous = signature
        if found is not None:
            print('IEEE_VIA_UESTC_OPENED: host=' + (urlsplit(found.url).hostname or 'NONE'))
            return found, 'IEEE_VIA_WEBVPN'
        if not live:
            return None, 'CANCELLED'
        try:
            live[-1].wait_for_timeout(250)
        except Error:
            continue
    print('UESTC_ENTRY_UNRECOGNIZED')
    return None, 'UESTC_ENTRY_UNRECOGNIZED'


def enter_ieee(context, timeout, download_ready=lambda: False, on_portal_ready=None):
    print("OPENING_UESTC_WEBVPN")
    candidates = [p for p in context.pages if not p.is_closed() and is_webvpn_url(p.url)]
    candidates.sort(key=lambda p: urlsplit(p.url).hostname != 'webvpn.uestc.edu.cn')
    authenticated = [p for p in candidates if any(portal_ready(scope) for scope in
                     [p] + [f for f in p.frames if f != p.main_frame])]
    portal = (authenticated or candidates)[0] if candidates else context.new_page()
    if not candidates:
        portal.goto(UESTC_ENTRY + "/", wait_until="domcontentloaded", timeout=30000)
    portal.bring_to_front()
    if not authenticated:
        print("WAITING_FOR_USER_AUTH")
        print("UESTC institutional access is required.")
        print("Complete authentication in the visible browser.")
        print("The program will continue after authentication.")
    deadline = time.monotonic() + timeout
    library_at = None
    resource_at = None
    domain_at = None
    ready_reported = False
    last_pages = None
    while time.monotonic() < deadline:
        if download_ready():
            return None, "DOWNLOAD_RECEIVED"
        pages = [p for p in context.pages if not p.is_closed()]
        if not pages:
            return None, "CANCELLED"
        scopes = []
        signature = tuple((p.url == "about:blank", urlsplit(p.url).hostname) for p in pages)
        changed = signature != last_pages
        if changed:
            for index, (blank, host) in enumerate(signature):
                print(f"PAGE[{index}]: {'about:blank' if blank else (host or 'unknown') + '/...'}")
            last_pages = signature
        ordered = sorted(enumerate(pages), key=lambda item:
                         urlsplit(item[1].url).hostname != 'webvpn.uestc.edu.cn')
        for index, owner in ordered:
            if not is_webvpn_url(owner.url):
                continue
            if changed:
                print(f"WebVPN candidate: PAGE[{index}]")
            if portal_ready(owner) or portal_ieee(owner):
                scopes.append(owner)
            else:
                scopes.extend(frame for frame in owner.frames if frame != owner.main_frame)
        preferred_portal = next((scope for scope in scopes if portal_ready(scope)), None)
        for page in scopes:
            try:
                if portal_ieee(page):
                    print("IEEE_VIA_UESTC_OPENED: host=" + (urlsplit(page.url).hostname or "unknown"))
                    return page, "IEEE_VIA_WEBVPN"
                marker = portal_marker(page)
                if marker is None:
                    continue
                if page is not preferred_portal:
                    continue
                if not ready_reported:
                    print("Portal marker: " + marker)
                    print("UESTC_WEBVPN_PORTAL_READY")
                    ready_reported = True
                    if on_portal_ready is not None and on_portal_ready():
                        return None, "IEEE_POST_AUTH_DIRECT_SUCCESS"
                    if on_portal_ready is not None:
                        break  # Refresh scopes after the potentially long callback.
                now = time.monotonic()
                if library_at is None:
                    category = named_action(page, LIBRARY)
                    if category is None:
                        category = named_action(page, LIBRARY_SHORT)
                    if category is not None:
                        category.click(timeout=3000)
                        print("UESTC_LIBRARY_DATABASES_OPENED")
                    library_at = now
                    continue
                if resource_at is None and domain_at is None:
                    resource = named_action(page, RESOURCE)
                    if resource is None:
                        resource = unique_visible([page.locator("a[href*='ieeexplore.ieee.org']")])
                    if resource is not None:
                        print("UESTC_IEEE_RESOURCE_FOUND")
                        try:
                            resource.click(timeout=3000)
                            print("UESTC_IEEE_RESOURCE_OPENED")
                        except PlaywrightTimeout:
                            # A click can dispatch and then time out waiting for navigation.
                            # Observe its outcome without assuming dispatch or clicking again.
                            print('UESTC_RESOURCE_CLICK_UNCONFIRMED')
                        except Error as exc:
                            if not detached_transient(exc):
                                raise
                        return wait_for_ieee_resource(context)
                # Allow the official list and resource navigation to finish before the second route.
                if domain_at is None and now - (resource_at or library_at) >= 8:
                    if domain_entry(page):
                        domain_at = now
                    else:
                        print("USER_ACTION_REQUIRED: portal resource/domain controls are not recognized.")
                        return None, "UESTC_ENTRY_UNRECOGNIZED"
                elif domain_at is not None and now - domain_at >= 15:
                    print("USER_ACTION_REQUIRED: check the portal's domain-access result or SSO confirmation.")
                    return None, "UESTC_PROXY_NOT_CONFIRMED"
            except Error as exc:
                if not detached_transient(exc):
                    raise
                break  # Drop this snapshot and enumerate current frames on the next poll.
        pages[-1].wait_for_timeout(250)
    print("USER_ACTION_REQUIRED: complete institutional authentication or required SSO confirmation.")
    return None, "UESTC_AUTH_OR_ENTRY_TIMEOUT"


def search_article(page, doi, title, article_id, timeout=60, context=None, on_result=None):
    """Use the verified production main-form search; preserve caller continuation."""
    from .publishers.ieee_search import search_article as verified_search
    return verified_search(page, doi, title, article_id, timeout, context, on_result)
