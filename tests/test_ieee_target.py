import itertools

import pytest

from test_ieee_download import Context, Locator, Page, SearchInput
from uestc_paper.publishers.ieee import canonical_article_id
from uestc_paper.uestc import search_article


class Links(Locator):
    def __init__(self, page, number):
        super().__init__(lambda: self.open())
        self.page = page
        self.number = number

    def get_attribute(self, name, **kwargs):
        assert name == 'href'
        return '/observed-proxy/document/' + self.number

    def open(self):
        self.page.url = 'https://webvpn.uestc.edu.cn/observed-proxy/document/' + self.number


class TargetPage(Page):
    def __init__(self, context, numbers=(), has_search=True, after_search=True):
        super().__init__(context)
        self.mode = 'proxy'
        self.url = 'https://webvpn.uestc.edu.cn/observed-proxy/home'
        self.numbers = numbers
        self.has_search = has_search
        self.after_search = after_search

    def title(self):
        return 'IEEE Xplore'

    def get_by_role(self, role, name=None, **kwargs):
        if role == 'searchbox':
            return Locator(self.search) if self.has_search else Locator()
        return super().get_by_role(role, name, **kwargs)

    def locator(self, selector):
        if selector == "input[type='search'], input[type='text'], input:not([type])":
            return SearchInput(self) if self.has_search else Locator()
        if selector == 'xpl-root':
            return Locator(lambda: None)
        if selector.startswith('a['):
            numbers = self.numbers if not self.after_search or self.searched else ()

            class Group:
                def count(inner):
                    return len(numbers)

                def nth(inner, i):
                    return Links(self, numbers[i])
            return Group()
        return Locator()


@pytest.mark.parametrize('url,expected', [
    ('https://ieeexplore.ieee.org/document/10752539/', '10752539'),
    ('https://ieeexplore.ieee.org/stamp/stamp.jsp?token=SECRET&arnumber=10752539', '10752539'),
    ('/stamp/stamp.jsp?arnumber=bad', ''),
])
def test_canonical_arnumber(url, expected):
    assert canonical_article_id(url) == expected


@pytest.mark.parametrize('immediate', [True, False])
def test_observed_article_link_or_doi_search(monkeypatch, capsys, immediate):
    ticks = itertools.count(0, .1)
    monkeypatch.setattr('uestc_paper.uestc.time.monotonic', lambda: next(ticks))
    context = Context()
    page = TargetPage(context, ('107525390', '10752539'), after_search=not immediate)
    context.pages.append(page)
    result = search_article(page, '10.1109/led.2024.3497584', '', '10752539', timeout=5)
    assert result
    assert page.url.endswith('/10752539')  # exact identifier, not prefix matching
    if immediate:
        assert context.actions == []
    else:
        assert context.actions[0] == ('fill', '10.1109/LED.2024.3497584')
    assert 'IEEE_TARGET_ARTICLE_OPENED' in capsys.readouterr().out


@pytest.mark.parametrize('has_search,status', [(False, 'IEEE_SEARCH_CONTROL_NOT_FOUND'),
                                            (True, 'IEEE_SEARCH_OBSERVATION_INCONCLUSIVE')])
def test_explicit_search_failures(monkeypatch, has_search, status):
    ticks = itertools.count(0, .1)
    monkeypatch.setattr('uestc_paper.uestc.time.monotonic', lambda: next(ticks))
    context = Context()
    page = TargetPage(context, has_search=has_search)
    context.pages.append(page)
    result = search_article(page,
                            '10.1109/test', '', '10752539', timeout=5)
    assert not result and result.status == status
    if has_search:
        assert [value for operation, value in context.actions if operation == 'fill'] == [
            '10.1109/TEST']


def test_target_link_in_frame(monkeypatch):
    ticks = itertools.count(0, .1)
    monkeypatch.setattr('uestc_paper.uestc.time.monotonic', lambda: next(ticks))
    context = Context()
    owner = TargetPage(context, has_search=False)
    frame = TargetPage(context, ('10752539',), after_search=False)
    owner.frames = [frame]
    context.pages.append(owner)
    result = search_article(owner, '10.1109/test', '', '10752539', timeout=5)
    assert result and result.page is frame
