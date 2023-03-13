from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .enums import PortfolioTab, OrderType

if TYPE_CHECKING:
    from tradezero import TradeZero  # for the example in the docs


class Portfolio:
    def __init__(self, driver: WebDriver):
        self.driver = driver

    def open_orders(self) -> pd.DataFrame:
        """
        return the Portfolio table as a pandas.DataFrame or nested dict, with the symbol column as index.
        the column names are the following: 'type', 'qty', 'p_close', 'entry',
        'price', 'change', '%change', 'day_pnl', 'pnl', 'overnight'
        note that if the portfolio is empty Pandas won't be able to locate the table,
        and therefore will return None

        :return: pandas.DataFrame or None if table empty
        """
        portfolio_symbols = self.driver.find_elements(By.XPATH, '//*[@id="opTable-1"]/tbody/tr/td[1]')
        if len(portfolio_symbols) == 0:
            return pd.DataFrame()

        df = pd.read_html(self.driver.page_source, attrs={'id': 'opTable-1'})[0]
        df.columns = [
            'symbol', 'type', 'qty', 'p_close', 'entry', 'price', 'change', '%change', 'day_pnl', 'pnl', 'overnight'
        ]
        # TODO clean the DF
        # df = df.set_index('symbol')
        return df

    def closed_orders(self) -> pd.DataFrame:
        raise NotImplementedError

    def active_orders(self) -> pd.DataFrame:
        """
        Get a dataframe with all the active orders and their info

        :return: dataframe or dictionary (based on the return_type parameter)
        """
        active_orders = self.driver.find_elements(By.XPATH, '//*[@id="aoTable-1"]/tbody/tr[@order-id]')
        if len(active_orders) == 0:
            return pd.DataFrame()

        df = pd.read_html(self.driver.page_source, attrs={'id': 'aoTable-1'})[0]
        df = df.drop(0, axis=1)  # remove the first column which contains the button "CANCEL"
        df.columns = ['ref_number', 'symbol', 'side', 'qty', 'type', 'status', 'tif', 'limit', 'stop', 'placed']
        # df = df.set_index('symbol')  # cant set it as a column since its not always unique
        return df

    def inactive_orders(self) -> pd.DataFrame:
        raise NotImplementedError

    def invested(self, symbol) -> bool:
        """
        returns True if the given symbol is in portfolio, else: false

        Examples:
        >>> tz = TradeZero(...)
        >>> tz.portfolio.invested('AAPL')
        True
        >>> tz.portfolio.invested('aapl')
        True
        >>> tz.portfolio.invested('NVDA')
        False

        :param symbol: str: e.g: 'aapl', 'amd', 'NVDA', 'GM'
        :return: bool
        """
        return symbol.upper() in self.open_orders()['symbol']

    def _switch_portfolio_tab(self, tab: PortfolioTab) -> None:
        """
        Switch the focus to a given tab

        Note that this is idem-potent, meaning you can switch twice consecutively in the same tab.

        :param tab: enum of PortfolioTab
        :return: None
        """
        portfolio_tab = self.driver.find_element(By.ID, tab)  # TODO: test if .value is needed
        portfolio_tab.click()

    def cancel_active_order(self, symbol: str, order_type: OrderType) -> None:
        """
        Cancel a pending order

        :param symbol:
        :param order_type: enum of OrderType
        :return: None
        """
        symbol = symbol.upper()
        self._switch_portfolio_tab(tab=PortfolioTab.active_orders)

        df = self.active_orders()
        assert symbol in df['symbol'].values, f'Given symbol {symbol} is not present in the active orders tab'

        # find the ref-id of all the orders we have to cancel:
        filt = (df['symbol'] == symbol) & (df['type'] == order_type)
        ids_to_cancel = df[filt]['ref_number'].values
        ids_to_cancel = [x.replace('S.', '') for x in ids_to_cancel]

        for order_id in ids_to_cancel:
            cancel_button = self.driver.find_element(
                By.XPATH, f'//div[@id="portfolio-content-tab-ao-1"]//*[@order-id="{order_id}"]/td[@class="red"]')
            cancel_button.click()
