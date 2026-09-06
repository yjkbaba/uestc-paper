from types import SimpleNamespace

import pytest

from uestc_paper.native_save_as import SaveAsObservation


@pytest.mark.parametrize('new_dialog', [True, False])
def test_readonly_save_as_snapshot_then_bounded_observation(new_dialog, capsys):
    clock = [0]
    polls = []

    def snapshot():
        # Pre-existing Save As must not be attributed to this click.
        return {1, 2} if new_dialog and clock[0] >= 1 else {1}

    observer = SaveAsObservation(snapshot, lambda: clock[0])

    def pump(ms):
        assert ms == 500
        clock[0] += ms / 1000

    result = observer.observe(pump, SimpleNamespace(poll=lambda: polls.append(True)))
    assert result == ('NATIVE_SAVE_AS_DETECTED' if new_dialog else 'NATIVE_SAVE_AS_NOT_DETECTED')
    assert clock[0] == (1 if new_dialog else 40)
    assert polls
    output = capsys.readouterr().out
    assert ('appeared_after_click=true' in output) is new_dialog
