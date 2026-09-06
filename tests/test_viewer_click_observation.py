from types import SimpleNamespace

from playwright.sync_api import TimeoutError

from uestc_paper.viewer_click_observation import Files, click_and_observe


def test_timeout_then_file_evidence_without_second_click(tmp_path):
    files = Files([tmp_path])
    monitor = SimpleNamespace(files=files, evidence=False)
    clicks = []
    def click(**kwargs):
        clicks.append(kwargs)
        raise TimeoutError('redacted')
    ticks = iter(range(10))
    def pump():
        (tmp_path / 'one.crdownload').write_bytes(b'%PDF')
        monitor.evidence = True
    result = click_and_observe(SimpleNamespace(click=click), monitor, pump,
                               seconds=3, clock=lambda: next(ticks))
    assert result == 'VIEWER_DOWNLOAD_CLICK_DISPATCHED_AFTER_TIMEOUT'
    assert len(clicks) == 1 and files.changed


def test_old_file_is_not_new_evidence(tmp_path):
    (tmp_path / 'old.pdf').write_bytes(b'%PDF')
    files = Files([tmp_path])
    monitor = SimpleNamespace(files=files, evidence=False)
    def click(**kwargs):
        raise TimeoutError('redacted')
    ticks = iter(range(10))
    result = click_and_observe(SimpleNamespace(click=click), monitor, lambda: None,
                               seconds=3, clock=lambda: next(ticks))
    assert result == 'VIEWER_DOWNLOAD_CLICK_NOT_CONFIRMED'
    assert not files.changed
