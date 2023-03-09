from __future__ import annotations

from selenium.webdriver.common.by import By

from .time_helpers import Time


class Notification(Time):
    """A class for retrieving notifications from the web-app"""

    def __init__(self, driver):
        self.driver = driver

    def get_last_notification_message(self):
        """
        return last notification message

        :return: str
        """
        return self.driver.find_element(By.CSS_SELECTOR, 'span.message').text

    def get_notifications(self, notif_amount: int = 1):
        """
        return a nested list with each sublist containing [time, title, message],
        note that u can only view the amount of notifications that are visible in the box/widget
        without scrolling down (which usually is around 6-9 depending on each message length)
        example of nested list: (see the docs for a better look):
        [['11:34:49', 'Order canceled', 'Your Limit Buy order of 1 AMD was canceled.'],
        ['11:23:34', 'Level 2', 'You are not authorized for symbol: AMD'],
        ['11:23:34', 'Error', 'You are not authorized for symbol: AMD']].

        :param notif_amount: int amount of notifications to retrieve sorted by most recent
        :return: nested list
        """
        notif_lst = self.driver.find_elements(By.XPATH,
                                              '//*[@id="notifications-list-1"]/li')
        notif_lst_text = [x.text.split('\n') for x in notif_lst[0:notif_amount] if x.text != '']

        notifications = []
        for (notification, i) in zip(notif_lst_text, range(notif_amount)):
            if len(notification) == 2:
                notification.insert(0, str(self.time))

            elif notification[0] == '' or notification[0] == '-':
                notification[0] = str(self.time)

            notifications.append(notification)
        return notifications
    
    def notifications_generator(self):
        """
        A notification generator, similarly to get_notifications(), this yields one notification at a time,
        on each next() it will yield a list like so: 
        ['11:34:49', 'Order canceled', 'Your Limit Buy order of 1 AMD was canceled.']
        You can think of it as a more dynamic version of get_notifications(), on each next(); it gets 
        one notification message.

        :return: list
        """
        notif_lst = self.driver.find_elements(By.XPATH, '//*[@id="notifications-list-1"]/li')
        for item in notif_lst:
            if item.text == '':
                continue
                
            notification = item.text.split('\n')
            if len(notification) == 2:
                notification.insert(0, str(self.time))

            elif notification[0] == '' or notification[0] == '-':
                notification[0] = str(self.time)

            yield notification
