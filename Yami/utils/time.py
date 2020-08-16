import typing
from datetime import timedelta, datetime


def display_time(seconds: typing.Union[int, float], granularity=4):
    result = []
    if granularity > 7 or granularity < 1:
        raise ValueError("granularity must be between 7 and 1")
    intervals = (
        ("years", 0x1E14320),
        ("months", 0x2819A0),
        ("weeks", 0x93A80),
        ("days", 0x15180),
        ("hours", 0xE10),
        ("minutes", 0x3C),
        ("seconds", 0x1)
    )
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip("s")
            result.append(f"{int(value)} {name}")
    return ", ".join(result[:granularity])


def display_time_from_delta(delta: timedelta, *, granularity=4):
    return display_time(delta.total_seconds(), granularity)


def display_time_from_datetimes(first: datetime, second: datetime, *, granularity=4):
    return display_time((first - second).total_seconds(), granularity)
