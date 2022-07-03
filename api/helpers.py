import pytz
import datetime as dt


class Time:
    @property
    def time(self):
        """ return current EST time as a datetime object """
        tz_ny = pytz.timezone('US/Eastern')
        time1 = dt.datetime.now(tz=tz_ny).time()
        return time1

    def time_between(self, time1: tuple, time2: tuple):
        """
        return True if current time between: time1, and time2, else: return False

        :param time1: tuple, ex: (10, 30), or with sec and micro-sec: (10, 30, 0, 250000)
        :param time2: tuple, ex: (12, 45)
        :return: bool
        """
        if dt.time(*time1) < self.time < dt.time(*time2):
            return True
        return False


class Timer:
    def __init__(self):
        self.timer_start = time.perf_counter()

    @property
    def time_elapsed(self):
        return time.perf_counter() - self.timer_start
