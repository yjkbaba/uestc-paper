from types import SimpleNamespace

from test_verify import make_pdf

from uestc_paper.viewer_download_diagnostic import save_completed, viewer_control


def test_completed_download_passes_existing_verifier(tmp_path):
    path = make_pdf(tmp_path / 'temporary')
    metadata = SimpleNamespace(doi='10.1234/abc', title='An example research article')
    output = tmp_path / 'final'
    assert save_completed(path, metadata, output)
    assert len(list(output.glob('*.pdf'))) == 1
    assert not path.exists()


def test_invalid_download_is_not_saved(tmp_path):
    path = tmp_path / 'temporary'
    path.write_bytes(b'<html>not a PDF</html>')
    metadata = SimpleNamespace(doi='10.1234/abc', title='Example')
    output = tmp_path / 'final'
    assert not save_completed(path, metadata, output)
    assert not list(output.iterdir())
    assert path.exists()


def test_stamp_alone_never_exposes_download_control():
    class Frame:
        def locator(self, selector):
            assert selector == 'pdf-viewer'
            return SimpleNamespace(count=lambda: 0)

    page = SimpleNamespace(is_closed=lambda: False, frames=[Frame()])
    assert viewer_control(SimpleNamespace(pages=[page])) is None


def test_viewer_toolbar_control_can_be_in_child_frame():
    control = SimpleNamespace(is_visible=lambda: True, is_enabled=lambda: True,
                              bounding_box=lambda: dict(x=0, y=0, width=32, height=32),
                              evaluate=lambda _: dict(main_toolbar=True, drive_controls=False,
                                                      menu=False, aria='Download', title='Download',
                                                      download_controls=True, download_icon=True))
    controls = SimpleNamespace(count=lambda: 1, nth=lambda i: control)
    viewer = SimpleNamespace(count=lambda: 1, get_by_role=lambda *a, **kw: controls)
    frame = SimpleNamespace(locator=lambda selector: viewer)
    page = SimpleNamespace(is_closed=lambda: False, frames=[frame])
    assert viewer_control(SimpleNamespace(pages=[page])) == (page, control)
