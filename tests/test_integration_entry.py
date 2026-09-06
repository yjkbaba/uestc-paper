from contextlib import contextmanager

from test_ieee_download import Context
from uestc_paper.config import Config
from uestc_paper.integration import run
from uestc_paper.resolver import Metadata


def test_institutional_shortcut_waits_without_direct_or_oa(monkeypatch, tmp_path, capsys):
    context = Context()

    @contextmanager
    def browser(config):
        yield context

    monkeypatch.setattr('uestc_paper.integration.persistent_browser', browser)
    monkeypatch.setattr('uestc_paper.integration.resolve_metadata', lambda doi: Metadata(doi))
    seen = []

    def portal(ctx, timeout):
        seen.append(ctx)
        return None, 'UESTC_AUTH_OR_ENTRY_TIMEOUT'

    monkeypatch.setattr('uestc_paper.integration.enter_ieee', portal)
    assert run('10.1109/test', '123', Config(tmp_path), 1) == 2
    assert seen == [context] and not context.visits
    assert 'UESTC_AUTH_OR_ENTRY_TIMEOUT' in capsys.readouterr().out
