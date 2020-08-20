from Yami.utils.time import display_time


def test_display_time_from_seconds():
    assert display_time(2000) == "33 minutes, 20 seconds"
    assert display_time(1) == "1 second"
    assert display_time(60) == "1 minute"
    assert display_time(3600) == "1 hour"
    assert display_time(86400) == "1 day"
    assert display_time(604800) == "1 week"
    assert display_time(604800 * 2) == "2 weeks"
