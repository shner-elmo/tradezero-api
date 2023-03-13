from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .exceptions import AccountAttributeHiddenError

if TYPE_CHECKING:
    AttributeValue: TypeAlias = str | float


class Account:
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    buying_power: float
    cash: float
    exposure: float
    equity: float
    equity_ratio: float
    used_lvg: float
    allowed_lvg: float
    account: str  # TODO: test these three IDs
    account_label: str
    login_id: str
    
    attribute_name_id_mapping = {
        'realized_pnl': 'h-realized-value',
        'unrealized_pnl': 'h-unrealizd-pl-value',
        'total_pnl': 'h-total-pl-value',
        'buying_power': 'p-bp',
        'cash': 'h-cash-value',
        'exposure': 'h-exposure-value',
        'equity': 'h-equity-value',
        'equity_ratio': 'h-equity-ratio-value',
        'used_lvg': 'h-used-lvg-value',
        'allowed_lvg': 'p-allowed-lev',
        'account': 'h-select-account',
        'account_label': 'trading-order-label-account',
        'login_id': 'h-loginId',
    }
    
    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver

    def hide_attributes(self) -> None:
        """
        Hides all account attributes i.e, account username, equity-value, cash-value, realized-value...
        """
        for attr_id in self.attribute_name_id_mapping.values():
            element = self.driver.find_element(By.ID, attr_id)
            self.driver.execute_script("arguments[0].setAttribute('style', 'display: none;')", element)
                    
    def get(self, attr: str) -> AttributeValue | None:
        try:
            return self[attr]
        except KeyError:
            return None
    
    def __getitem__(self, attr_id: str) -> AttributeValue:
        element = self.driver.find_element(By.ID, attr_id)
        if element.get_attribute('style') == 'display: none;':
            raise AccountAttributeHiddenError('cannot fetch attribute that has been hidden')
        return element.text.translate(str.maketrans('', '', '$%x,'))

    def __getattr__(self, item) -> AttributeValue:
        return self[item]
