import pytest

from test_ieee_download import Context, Download
from test_verify import make_pdf
from uestc_paper.publishers.ieee import IEEEAdapter
from uestc_paper.resolver import Metadata


def test_failed_direct_enters_library_without_post_auth_retry(tmp_path, monkeypatch, capsys):
    source = make_pdf(tmp_path / 'source.part', doi='10.1109/test')
    def no_terminal_confirmation(*args):
        pytest.fail('Portal auto-detection must not request terminal confirmation')
    monkeypatch.setattr('builtins.input', no_terminal_confirmation)
    context = Context(Download(source), direct_access=False)
    adapter = IEEEAdapter()
    adapter.direct_seconds = .01
    result = adapter.download(context, adapter.resolve(Metadata('10.1109/test')),
                              tmp_path / 'target.part', timeout=1)
    assert len(context.pages) == 2
    assert all(page.context is context for page in context.pages)
    assert context.visits == ['https://doi.org/10.1109/test', 'https://vpn.uestc.edu.cn/']
    output = capsys.readouterr().out
    assert 'IEEE_POST_AUTH_DIRECT_RETRY' not in output
    assert output.index('IEEE_DIRECT_RETRIEVAL_FAILED') < output.index('UESTC_WEBVPN_PORTAL_READY')
    assert result.status == 'DOWNLOAD_RECEIVED'
    assert result.route == 'UESTC WebVPN / IEEE'
    assert context.actions[0] == 'library'
