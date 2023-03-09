from __future__ import annotations

import warnings
from collections import namedtuple

from selenium.webdriver.common.by import By


class Account:
    def __init__(self, driver):
        self.driver = driver
        self.attribute_ids = [
            "h-realized-value",
            "h-unrealizd-pl-value",
            "h-total-pl-value",
            "p-bp",
            "h-cash-value",
            "h-exposure-value",
            "h-equity-value",
            "h-equity-ratio-value",
            "h-used-lvg-value",
            "p-allowed-lev",
            "h-select-account",
            "h-loginId",
            "trading-order-label-account",
        ]

    def hide_attributes(self):
        """
        Hides all account attributes i.e, account username, equity-value, cash-value, realized-value...
        """
        for id_ in self.attribute_ids:
            element = self.driver.find_element(By.ID, id_)
            self.driver.execute_script("arguments[0].setAttribute('style', 'display: none;')", element)

    @property
    def attributes(self):
        """
        returns a namedtuple with the account following properties:
        realized_pnl, unrealized_pnl, total_pnl, buying_power, cash,
        exposure, equity, equity_ratio, used_lvg, allowed_lvg.
        note that if one or more of the attributes have been hidden; either by
        setting self.hide_attributes = True or by calling hide_attributes(),
        a namedtuple will be returned with None values.

        :return: namedtuple
        """
        Data = namedtuple('Data', ['realized_pnl', 'unrealized_pnl', 'total_pnl', 'buying_power', 'cash',
                                   'exposure', 'equity', 'equity_ratio', 'used_lvg', 'allowed_lvg'])

        attribute_ids = self.attribute_ids[:-3]
        values = []
        for id_ in attribute_ids:
            element = self.driver.find_element(By.ID, id_)

            if element.get_attribute('style') == 'display: none;':
                warnings.warn('cannot fetch attribute that has been hidden')

                empty_list = [None] * len(attribute_ids)
                return Data._make(empty_list)

            value = element.text.translate(str.maketrans('', '', '$%x,'))
            values.append(float(value))
        return Data._make(values)
