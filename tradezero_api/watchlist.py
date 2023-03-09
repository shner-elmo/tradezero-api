from __future__ import annotations

import time
import warnings

import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class Watchlist:
    """
    this class is for managing the data withing the watchlist container
    note that if the container is placed on the left side of the UI it will show
    only about half of the properties (Last, Bid, Ask, %Chg, Chg, Vol) instead of all 12.
    """
    def __init__(self, driver):
        self.driver = driver
        self.symbols = set()

    def add(self, symbol: str):
        """
        add symbol to watchlist

        :param symbol:
        :raises Exception: if given symbol is not valid
        """
        symbol = symbol.upper()
        symbol_input = self.driver.find_element(By.ID, 'trading-l1-input-symbol')
        symbol_input.send_keys(symbol, Keys.RETURN)

        time.sleep(0.4)
        if self._symbol_valid(symbol):
            self.symbols.add(symbol)
        else:
            raise Exception(f'Error: Given symbol is not valid ({symbol})')

    def remove(self, symbol: str):
        """
        remove symbol from watchlist

        :param symbol:
        """
        symbol = symbol.upper()
        if symbol not in self._get_current_symbols():
            warnings.warn(f'Given Symbol is not present in watchlist ({symbol})')
            return

        delete_button = f'//*[@id="wl-{symbol}"]/td[1]'
        self.driver.find_element(By.XPATH, delete_button).click()
        self.symbols.remove(symbol)

    def reset(self):
        """
        remove all symbols from watchlist
        """
        rows = self.driver.find_elements(By.XPATH, '//*[@id="trading-l1-tbody"]/tr/td[1]')
        for delete_button in rows:
            delete_button.click()
        self.symbols = set()

    def restore(self):
        """
        make sure all symbols that have been added,
        are present in the watchlist (after refresh the watchlist resets)
        """
        current_list = set(self._get_current_symbols())  # set because the order might be different
        if self.symbols != current_list:
            for symbol in self.symbols:
                if symbol not in current_list:
                    self.add(symbol)

    def _get_current_symbols(self):
        """
        return list with current symbols on watchlist
        """
        rows = self.driver.find_elements(By.XPATH, '//*[@id="trading-l1-tbody"]/tr/td[2]')
        if len(rows) == 0:
            return []

        data = self.data('dict')
        return list(data.keys())

    def _symbol_valid(self, symbol: str):
        """
        check if a symbol is valid

        :param symbol:
        :return: bool
        """
        last_notif_message = self.driver.find_element(By.CSS_SELECTOR, 'span.message').text
        if last_notif_message == f'Symbol not found: {symbol.upper()}':
            return False
        return True

    def data(self, return_type: str = 'df'):
        """
        returns the watchlist table as either a DataFrame or Dict,
        if return_type is equal to: 'df' it will return a pandas.DataFrame
        or if return_type equal to: 'dict' it will return a Dictionary with the symbols as keys
        and the data as values.
        note that if there are no symbols in the watchlist, Pandas will not be able
        to locate the table and therefore will return False

        :param return_type: 'df' or 'dict'
        :return: None if empty, else: DF or dict
        """
        symbols_lst = self.driver.find_elements(By.XPATH, '//*[@id="trading-l1-tbody"]//td[2]')
        if len(symbols_lst) == 0:
            warnings.warn('There are no symbols present in your watchlist')
            return None

        # selenium can only read visible rows, while pandas can find also non-visible text
        # if there are no rows pandas will not be able to locate the table, and throw an error
        df = pd.read_html(self.driver.page_source, attrs={'id': 'trading-l1-table'})[0]

        if len(df.columns) == 8:
            df = df.drop(columns=[0])  # drop 'x'
            df.columns = ['symbol', 'last', 'bid', 'ask', '%chg', 'chg', 'vol']

        elif len(df.columns) == 14:
            df = df.drop(columns=[0, 2])  # drop 'x' and currency_get_current_symbols
            df.columns = ['symbol', 'open', 'close', 'last', 'bid', 'ask',
                          'high', 'low', '%chg', 'chg', 'vol', 'time']

        df = df.set_index('symbol')
        if return_type == 'dict':
            return df.to_dict('index')
        return df
