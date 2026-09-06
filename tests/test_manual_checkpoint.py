from test_ieee_download import Context
from uestc_paper.uestc import search_article


def test_result_checkpoint_prevents_automatic_article_click():
    context = Context()
    page = context.new_page()
    page.url = 'https://vpn.uestc.edu.cn/observed-resource/home'
    page.mode = 'proxy'
    page.searched = True
    visited = []
    sentinel = object()

    def checkpoint(scope, link):
        visited.append(scope)
        return sentinel

    result = search_article(page, '10.1109/test', '', '123', context=context,
                            on_result=checkpoint)
    assert result is sentinel and visited == [page]
    assert page.url.endswith('/home')
    assert not context.actions
