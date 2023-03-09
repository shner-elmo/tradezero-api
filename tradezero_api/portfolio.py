from __future__ import annotations

import warnings

import pandas as pd
from selenium.webdriver.common.by import By


class Portfolio:
    def __init__(self, driver):
        self.driver = driver

    def portfolio(self, return_type: str = 'df'):
        """
        return the Portfolio table as a pandas.DataFrame or nested dict, with the symbol column as index.
        the column names are the following: 'type', 'qty', 'p_close', 'entry',
        'price', 'change', '%change', 'day_pnl', 'pnl', 'overnight'
        note that if the portfolio is empty Pandas won't be able to locate the table,
        and therefore will return None

        :param return_type: 'df' or 'dict'
        :return: pandas.DataFrame or None if table empty
        """
        portfolio_symbols = self.driver.find_elements(By.XPATH, '//*[@id="opTable-1"]/tbody/tr/td[1]')
        if len(portfolio_symbols) == 0:
            warnings.warn('Portfolio is empty')
            return None

        df = pd.read_html(self.driver.page_source, attrs={'id': 'opTable-1'})[0]
        df.columns = [
            'symbol', 'type', 'qty', 'p_close', 'entry', 'price', 'change', '%change', 'day_pnl', 'pnl', 'overnight'
        ]
        df = df.set_index('symbol')
        if return_type == 'dict':
            return df.to_dict('index')
        return df

    def open_orders(self):
        """
        return DF with only positions that were opened today (intraday positions)

        :return: pandas.DataFrame
        """
        df = self.portfolio()
        filt = df['overnight'] == 'Yes'
        return df.loc[~filt]

    def invested(self, symbol):
        """
        returns True if the given symbol is in portfolio, else: false

        :param symbol: str: e.g: 'aapl', 'amd', 'NVDA', 'GM'
        :return: bool
        """
        data = self.portfolio('dict')
        symbols_list = list(data.keys())

        if symbol.upper() in symbols_list:
            return True
        return False
