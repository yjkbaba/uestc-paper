from uestc_paper.viewer_controls import select_candidate


def candidate(**overrides):
    return dict(dict(visible=True, enabled=True, main_toolbar=True, drive_controls=False,
                     menu=False, aria='Download', title='Download', download_controls=True,
                     download_icon=True), **overrides)


def test_drive_and_download_disambiguated_independent_of_order():
    drive = candidate(drive_controls=True, aria='Save to Google Drive', download_controls=False)
    download = candidate()
    assert select_candidate([drive, download]) == 1
    assert select_candidate([download, drive]) == 0


def test_two_equal_download_controls_remain_ambiguous():
    assert select_candidate([candidate(), candidate()]) is None


def test_hidden_disabled_menu_and_non_toolbar_are_excluded():
    records = [candidate(visible=False), candidate(enabled=False), candidate(menu=True),
               candidate(main_toolbar=False), candidate()]
    assert select_candidate(records) == 4
