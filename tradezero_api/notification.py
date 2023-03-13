from __future__ import annotations

from typing import Iterator, TYPE_CHECKING, TypeAlias

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from more_itertools import take

from .utils import get_est_time_as_str

if TYPE_CHECKING:
    from tradezero import TradeZero  # for the example in the docs
    NotificationResult: TypeAlias = tuple[str, str, str]


class Notifications:
    """A class for retrieving notifications from the web-app"""
    def __init__(self, driver: WebDriver):
        self.driver = driver

    def last(self) -> NotificationResult:
        """
        return last notification message

        Examples:
        >>> tz = TradeZero(...)
        >>> tz.notifications.get_n_notifications(n=3)

        :return: str
        """
        return self.get_n(n=1)[0]
        # return self.driver.find_element(By.CSS_SELECTOR, 'span.message').text

    def get_n(self, n: int | None) -> list[NotificationResult]:
        """
        Get a list with N notifications

        The parameter `n` should be a positive integer or None, if its None it will return all the notifications
        in a list.
        The output is a list of tuples, with each tuple containing three fields: time, title, and message.
        Note that u can only view the amount of notifications that are visible in the box/widget
        without scrolling down (which usually is around 6-9 depending on each message length)

        >>> tz = TradeZero(...)
        >>> tz.notifications.get_n_notifications(n=3)
        [('11:34:49', 'Order canceled', 'Your Limit Buy order of 1 AMD was canceled.'),
        ('11:23:34', 'Level 2', 'You are not authorized for symbol: AMD'),
        ('11:23:34', 'Error', 'You are not authorized for symbol: AMD')].

        :param n: int or None, amount of notifications to retrieve sorted by most recent
        :return: nested list
        """
        return take(n=n, iterable=self.get_notifications_iter())

    def get_notifications_iter(self) -> Iterator[NotificationResult]:
        """
        A notification generator, similarly to get_notifications(), this yields one notification at a time,
        on each next() it will yield a list like so: 
        ['11:34:49', 'Order canceled', 'Your Limit Buy order of 1 AMD was canceled.']
        You can think of it as a more dynamic version of get_notifications(), on each next(); it gets 
        one notification message.

        :return: list
        """
        # TODO scroll down to load all the notifications if they're not all visible (and try pd.read_html())
        # or get the amount of nodes from find_elements(By.XPATH, '//*[@id="notifications-list-1"]/li/*')
        # and do self.driver.find_element(By.XPATH, f'//*[@id="notifications-list-1"]/li/[{i}]') for each item
        notif_lst = self.driver.find_elements(By.XPATH, '//*[@id="notifications-list-1"]/li')
        for item in notif_lst:
            if item.text == '':
                continue

            notification = item.text.split('\n')
            if len(notification) == 2:
                notification.insert(0, get_est_time_as_str())

            elif notification[0] == '' or notification[0] == '-':
                notification[0] = get_est_time_as_str()

            yield tuple(notification)

    def __iter__(self) -> Iterator[NotificationResult]:
        yield from self.get_notifications_iter()
