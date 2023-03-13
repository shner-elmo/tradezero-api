from __future__ import annotations

import datetime as dt
from time import perf_counter

import pytz

__all__ = [
    'get_est_time',
    'get_est_time_as_str',
    'time_between',
    'is_market_open',
    'Timer',
    'time_it',
]


def get_est_time() -> dt.time:
    """
    Get the current EST time as a datetime.time object

    Examples:

    >>> get_est_time()
    datetime.time(16, 45, 40, 72406)

    :return: datetime.time object
    """
    tz_ny = pytz.timezone('US/Eastern')
    return dt.datetime.now(tz=tz_ny).time()


def get_est_time_as_str() -> str:
    """
    Get the current EST time as a string

    Examples:

    >>> get_est_time_as_str()
    '16:27:49'

    :return: string (HH:MM:SS)
    """
    return get_est_time().isoformat(timespec='seconds')


def time_between(time1: tuple[int, ...], time2: tuple[int, ...]) -> bool:
    """
    Check that the current time is between two given tuples

    Examples:

    >>> time_between((8,), (20,))  # time between 8AM and 8PM
    True
    >>> time_between((8, 30), (8, 45))  # time between 8:30 and 8:45
    False
    >>> time_between((15, 27, 40), (15, 27, 59))  # time between 15:27:40 and 15:27:59
    True

    :param time1: tuple, ex: (10, 30), or with sec and micro-sec: (10, 30, 0, 250000)
    :param time2: tuple, ex: (12, 45)
    :return: bool
    """
    return dt.time(*time1) < get_est_time() < dt.time(*time2)


def is_market_open() -> bool:
    """
    Check if the US stock market is currently open

    :return: bool
    """
    return time_between((9, 30), (16, 0))


class Timer:
    """
    A class that behaves like a stopwatch, when initialized the counter starts,
    and at any given moment you can check the total time elapsed with the time_elapsed property.
    """
    def __init__(self):
        self.timer_start = perf_counter()

    @property
    def time_elapsed(self) -> float:
        """
        Get the total time elapsed (since the class was instantiated)
        """
        return perf_counter() - self.timer_start


def time_it(func):
    """Decorator for debugging the time taken to run a function"""
    def wrapper(*args, **kwargs):
        timer = Timer()
        rv = func(*args, **kwargs)

        if kwargs.get('log_time_elapsed') or kwargs.get('log_info'):
            print(f'Time elapsed: {timer.time_elapsed:.2f} seconds')

        return rv
    return wrapper
