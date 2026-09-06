from playwright.sync_api import TimeoutError

from uestc_paper.auto_click_diagnostic import pointer_click


class Action:
    def __init__(self, hit=True, timeout=False):
        self.hit = hit
        self.timeout = timeout
        self.clicks = []

    def scroll_into_view_if_needed(self, **kwargs):
        pass

    def hover(self, **kwargs):
        pass

    def click(self, **kwargs):
        self.clicks.append(kwargs)
        if self.timeout:
            raise TimeoutError('redacted')

    def bounding_box(self):
        return dict(x=1, y=2, width=30, height=30)

    def is_visible(self):
        return True

    def is_enabled(self):
        return True

    def evaluate(self, expression):
        assert 'elementFromPoint' in expression
        assert '.click(' not in expression
        return self.hit


def test_pointer_click_has_one_trial_and_one_real_click():
    action = Action()
    assert pointer_click(action) == 'AUTO_LOCATOR_CLICK_DISPATCHED'
    assert action.clicks == [dict(trial=True, timeout=5000), dict(timeout=5000)]


def test_overlay_prevents_real_click():
    action = Action(hit=False)
    assert pointer_click(action) == 'AUTO_CLICK_TARGET_MISMATCH'
    assert action.clicks == [dict(trial=True, timeout=5000)]


def test_actionability_timeout_never_retries():
    action = Action(timeout=True)
    assert pointer_click(action) == 'AUTO_CLICK_TIMING_FAILURE'
    assert len(action.clicks) == 1
