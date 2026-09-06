from types import SimpleNamespace

import pytest

from test_verify import make_pdf
from uestc_paper.publishers.ieee_viewer_download import download_viewer


@pytest.mark.parametrize('kind', ['valid', 'invalid', 'partial', 'no-event', 'event', 'bad-hit'])
def test_single_viewer_click_and_verification(tmp_path, monkeypatch, kind):
    monkeypatch.setattr('uestc_paper.publishers.ieee_viewer_download.sys.platform', 'linux')
    clock = [0.0]
    monkeypatch.setattr('uestc_paper.publishers.ieee_viewer_download.time.monotonic', lambda: clock[0])
    directory = tmp_path / 'download-capture'
    directory.mkdir()
    destination = tmp_path / 'paper-test' / 'article.part'
    destination.parent.mkdir()
    source = make_pdf(tmp_path / 'source.pdf', doi='10.1109/test')
    handlers, clicks = {}, []

    class Page:
        url = 'https://webvpn.uestc.edu.cn/'

        def is_closed(self):
            return False

        def on(self, event, callback):
            handlers[event] = callback

        def remove_listener(self, event, callback):
            handlers.pop(event)

        def wait_for_timeout(self, ms):
            clock[0] += ms / 1000

    page = Page()
    context = SimpleNamespace(pages=[page], on=lambda *a: None, remove_listener=lambda *a: None)

    class Control:
        def bounding_box(self):
            return dict(x=10, y=20, width=30, height=40)

        def is_visible(self):
            return True

        def is_enabled(self):
            return True

        def evaluate(self, expression):
            assert 'elementFromPoint' in expression
            return kind != 'bad-hit'

    class Mouse:
        def move(self, x, y):
            assert (x, y) == (25, 40)
            assert 'download' in handlers
            clicks.append('move')

        def down(self):
            clicks.append('down')

        def up(self):
            clicks.append('up')
            if kind == 'no-event':
                return
            if kind == 'event':
                handlers['download'](object())
            name = 'paper.crdownload' if kind == 'partial' else 'paper.pdf'
            (directory / name).write_bytes(
                b'<html>error</html>' if kind == 'invalid' else source.read_bytes())

    page.mouse = Mouse()

    monkeypatch.setattr('uestc_paper.viewer_download_diagnostic.viewer_control',
                        lambda ctx: (page, Control()))
    monkeypatch.setattr('uestc_paper.publishers.ieee_viewer_download.evidence',
                        lambda *a: dict(aria='Download', title='Download', visible=True,
                                        enabled=True, main_toolbar=True,
                                        drive_controls=False, menu=False))
    result = download_viewer(context, destination, SimpleNamespace(doi='10.1109/test'),
                             completion_seconds=3)
    assert clicks == ([] if kind == 'bad-hit' else ['move', 'down', 'up'])
    assert not handlers
    success = kind in {'valid', 'event'}
    assert (result.status == 'DOWNLOAD_RECEIVED') is success
    assert destination.exists() is success
    expected = {'invalid': 'PDF_VERIFICATION_FAILED', 'partial': 'DOWNLOAD_INCOMPLETE',
                'no-event': 'VIEWER_MOUSE_CLICK_NOT_CONFIRMED',
                'bad-hit': 'VIEWER_MOUSE_HITTEST_FAILED'}
    if not success:
        assert result.status == expected[kind]
    if success:
        assert clock[0] < 3  # no fixed full-window delay
