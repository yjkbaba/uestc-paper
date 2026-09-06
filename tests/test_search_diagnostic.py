from uestc_paper.search_diagnostic import select_main


def record(**kw):
    return dict(dict(visible=True, enabled=True, search_type=True, in_form=True, within=False), **kw)


def test_main_search_selected_without_first_element_assumption():
    assert select_main([record(within=True), record(search_type=False), record()]) == 2


def test_multiple_main_candidates_stop():
    assert select_main([record(), record()]) is None


def test_only_within_result_search_is_not_main():
    assert select_main([record(within=True)]) is None
