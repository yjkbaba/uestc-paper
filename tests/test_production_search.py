from contextlib import contextmanager

import pytest
from playwright.sync_api import TimeoutError

from test_ieee_download import Context, Download, Locator, Page, SearchInput
from test_verify import make_pdf
from uestc_paper.config import Config
from uestc_paper.oa import OAResult
from uestc_paper.resolver import Metadata
from uestc_paper.workflow import get_paper


def test_search_hit_test_failure_never_dispatches(monkeypatch):
    from test_ieee_target import TargetPage
    from uestc_paper.uestc import search_article
    context = Context()
    page = TargetPage(context, numbers=('123',))
    context.pages.append(page)
    monkeypatch.setattr(Locator, 'evaluate', lambda self, expression: False)
    result = search_article(page, '10.1109/test', '', '123', context=context)
    assert result.status == 'IEEE_SEARCH_MOUSE_HITTEST_FAILED'
    assert page.mouse_actions == []
    assert ('button', 'Search') not in context.actions


@pytest.mark.parametrize('scenario', ['target', 'submit-timeout-target', 'fill-cleared', 'explicit-zero'])
def test_get_production_main_search_readback_button_wait_and_result(
        tmp_path, monkeypatch, capsys, scenario):
    class Input(SearchInput):
        def __init__(self, page, within):
            super().__init__(page)
            self.within = within

        def evaluate(self, expression):
            return dict(search_type=True, in_form=True, within=self.within)

        def fill(self, value, **kwargs):
            assert not self.within, 'Never fill the first within-results input'
            super().fill(value, **kwargs)

        def input_value(self):
            value = super().input_value()
            return '' if scenario == 'fill-cleared' else value

    class SearchPage(Page):
        pending = 0
        finished = False

        def locator(self, selector):
            if selector == "input[type='search'], input[type='text'], input:not([type])":
                if self.mode != 'proxy':
                    return Locator()
                items = [Input(self, True), Input(self, False)]
                class Group:
                    def count(self):
                        return len(items)
                    def nth(self, i):
                        return items[i]
                return Group()
            if selector == '[role="progressbar"], [aria-busy="true"]':
                return Locator((lambda: None) if self.pending else None)
            if selector == 'xpl-results-item':
                return Locator((lambda: None) if self.searched else None)
            return super().locator(selector)

        def search(self, operation, value):
            if operation == 'button':
                self.context.actions.append((operation, value))
                self.pending = 4
                self.callbacks['framenavigated'](self)
                if scenario == 'submit-timeout-target':
                    raise TimeoutError('synthetic dispatched submit timeout')
            else:
                super().search(operation, value)

        def wait_for_timeout(self, milliseconds):
            for page in self.context.pages:
                if page.pending:
                    self.context.actions.append(('result-wait', page.pending))
                    page.pending -= 1
                    if not page.pending:
                        page.finished = True
                        page.searched = scenario in {'target', 'submit-timeout-target'}

        def get_by_text(self, name):
            if 'No ' in str(name) and self.finished:
                # Even a contradictory zero marker cannot override target evidence.
                return Locator(lambda: None)
            return super().get_by_text(name)

    source = make_pdf(tmp_path / 'fixture.pdf', doi='10.1109/test')
    context = Context(Download(source), direct_access=False)
    monkeypatch.setattr('test_ieee_download.Page', SearchPage)
    @contextmanager
    def browser(_config):
        yield context
    monkeypatch.setattr('uestc_paper.workflow.persistent_browser', browser)
    monkeypatch.setattr('uestc_paper.workflow.resolve_metadata', lambda doi, client: Metadata(doi))
    monkeypatch.setattr('uestc_paper.workflow.EuropePMCResolver.resolve',
                        lambda self, doi: OAResult('OA_NOT_FOUND'))
    monkeypatch.setattr('uestc_paper.publishers.ieee.IEEEAdapter.direct_seconds', .001)
    result = get_paper('10.1109/test', Config(tmp_path), timeout=1)
    output = capsys.readouterr().out
    assert result == (0 if scenario in {'target', 'submit-timeout-target'} else 2)
    assert ('fill', '10.1109/TEST') in context.actions
    assert ('read-back', '10.1109/TEST') in context.actions
    assert 'index=1' in output
    assert not any(a[0] == 'press' for a in context.actions if isinstance(a, tuple))
    if scenario == 'fill-cleared':
        assert 'IEEE_SEARCH_FILL_FAILED' in output
        assert ('button', 'Search') not in context.actions
    else:
        assert context.actions.count(('button', 'Search')) == 1
        actions = [a for p in context.pages for a in p.mouse_actions]
        assert actions == [('move', 10, 10), ('down',), ('up',)]
        assert len([a for a in context.actions if isinstance(a, tuple) and a[0] == 'result-wait']) == 4
        assert 'SEARCH_VALUE_CONFIRMED' in output
        assert 'IEEE_SEARCH_PRE_SUBMIT: matching_target_links=0' in output
        if scenario in {'target', 'submit-timeout-target'}:
            assert 'IEEE_TARGET_RESULT_FOUND' in output
            assert 'IEEE_SEARCH_NO_RESULT' not in output
            assert ('IEEE_SEARCH_SUBMIT_UNCONFIRMED' if scenario == 'submit-timeout-target'
                    else 'IEEE_SEARCH_MOUSE_DISPATCHED') in output
        else:
            assert 'IEEE_SEARCH_NO_RESULT' in output
