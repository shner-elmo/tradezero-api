import os
import math
import time
import pytz
from datetime import datetime
import pandas as pd
from collections import namedtuple
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from termcolor import colored
os.system('color')


class TradeZero:
    def __init__(self, chrome_driver_path: str, user_name: str, password: str,
                 headless: bool = True, debug: bool = False, buying_power: int = 100000):
        """
        :param chrome_driver_path: path to chromedriver.exe
        :param user_name: TradeZero user_name
        :param password: TradeZero password
        :param headless: True will run the browser in headless mode, which means it won't be visible
        # :param debug: if True: print useful information e.g., Time elapsed for login, weather a stock is HTB or ETB...
        :param buying_power: must provide a value which will be the default equity amount for buying and selling
        """
        self.user_name = user_name
        self.password = password
        self.headless = headless
        # self.debug = debug
        self.buying_power = buying_power

        s = Service(chrome_driver_path)
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        if headless is True:
            options.headless = self.headless

        self.driver = webdriver.Chrome(service=s, options=options)
        self.driver.get("https://standard.tradezeroweb.us/")

    def _dom_fully_loaded(self, iter_amount: int = 1):
        """
        check that webpage elements are fully loaded/visible.
        there is no need to call this method, but instead call tz_conn() and that will take care of all the rest.

        :param iter_amount: int, default: 1, number of times it will iterate.
        :return: if the elements are fully loaded: return True, else: return False.
        """
        container_xpath = "//*[contains(@id,'portfolio-container')]//div//div//h2"
        for i in range(iter_amount):
            elements = self.driver.find_elements(By.XPATH, container_xpath)
            x = [i.text for i in elements]
            if 'Portfolio' in x:
                return True
            time.sleep(0.5)
        return False

    def login(self, log_time_elapsed: bool = False):
        """
        login to TZ website (must call in order to place orders).
        :param log_time_elapsed: bool, if True it will print time elapsed for login
        :return: None
        """
        timer_start1 = time.time()
        element = self.driver.find_element(By.ID, "login")
        element.send_keys(self.user_name)

        element = self.driver.find_element(By.ID, "password")
        element.send_keys(self.password, Keys.RETURN)

        self._dom_fully_loaded(150)
        Select(self.driver.find_element(By.ID, "trading-order-select-type")).select_by_index(1)
        if log_time_elapsed is True:
            print(f'Time elapsed (log in): {time.time() - timer_start1 :.2f}')
        return True

    def conn(self, log_tz_conn: bool = False):
        """
        make sure that the website stays connected and is fully loaded.

        TradeZero will ask for a Login twice a day, and sometimes it will require the page to be reloaded,
        so this will make sure that its fully loaded, by reloading or doing the login.
        :param log_tz_conn: bool, default: False. if True it will print if it reconnects through the login or refresh.
        :return: if connected: True, else: False.
        """
        if self._dom_fully_loaded(1):
            return True

        try:
            self.driver.find_element(By.ID, "login")
            self.login()
            if log_tz_conn is True:
                print(colored('tz_conn(): Login worked', 'cyan'))
            return True

        except:

            self.driver.get("https://standard.tradezeroweb.us/")
            if self._dom_fully_loaded(150):
                if log_tz_conn is True:
                    print(colored('tz_conn(): Refresh worked', 'cyan'))
                return True

        print(colored('tz_conn(): Error! none of the methods worked', 'magenta'))
        return False

    def exit(self):
        self.driver.quit()
        return True

    def _load_symbol(self, symbol: str):
        """
        validate symbol is correct

        make sure data for the symbol is fully loaded and that the symbol itself is valid
        :param symbol: str
        :return: bool
        """
        element = self.driver.find_element(By.ID, "trading-order-input-symbol")
        element.send_keys(symbol, Keys.RETURN)
        time.sleep(0.04)

        for i in range(300):
            price = self.driver.find_element(By.ID, "trading-order-ask").text
            if price == '':
                time.sleep(0.01)

            elif price.isdigit() and float(price) == 0:
                print(f"Waring: Market Closed, ask/bid = {price}")
                return False

            elif price.isdigit():
                return True
        else:
            last_notif = self.fetch_notif(1)[-1][2]
            message = f'Symbol not found: {symbol.upper()}'
            if message in last_notif:
                raise Exception(f"ERROR: {symbol=} Not found")

    def fetch_spread(self, symbol: str):
        """
        return a namedtuple with: ask_price, bid_price, pct_spread (spread in %)

        :param symbol: str: ex: 'aapl', 'amd', 'NVDA', 'GM'
        :return: namedtuple = (ask_price, bid_price, pct_spread) (spread in %)
        """
        Data = namedtuple('Data', ['ask_price', 'bid_price', 'pct_spread'])

        if self._load_symbol(symbol):
            ask_price = float(self.driver.find_element(By.ID, "trading-order-ask").text)
            bid_price = float(self.driver.find_element(By.ID, "trading-order-bid").text)
            pct_spread = ((ask_price - bid_price) / ask_price) * 100
            return Data(ask_price, bid_price, pct_spread)
        else:
            return Data(0.0, 0.0, 0.0)

    def locate_stock(self, symbol: str, total_price: float = 0, buying_power: float = None,
                     shares_amount: int = None, debug_info: bool = False):
        """
        Locate shares for a given stock.

        Locate a stock, requires: stock symbol, and one of the following: buying_power or share_amount, do not provide
        both. optional: total_price.
        if locate_price < total_price: accept, else: decline.

        :param symbol: str, symbol to locate.
        :param total_price: float, default: 0, total price you are willing to pay for locates
        (if locate_price less than total_price: accept, else: decline.
        :param buying_power: float, default: 100000, locate (buying_power / share price) and round to the next
         ceiling of 100 multiple.
        :param shares_amount: int, default: 0, must be a multiple of 100 (100, 200, 300...)
        :return: dictionary = {'locate_pps': locate_pps, 'locate_total': locate_total} (pps = price per share)
        :param debug_info: bool, if True it will print info about the locates in the console
        """
        Data = namedtuple('Data', ['locate_pps', 'locate_total'])

        if buying_power is not None and shares_amount is not None:
            raise Exception('ERROR: Cannot Provide both buying_power and shares_amount parameters, only one')

        if shares_amount is not None and shares_amount % 100 != 0:
            raise Exception(f'ERROR: shares_amount is not divisible by 100 ({shares_amount=})')

        if self._load_symbol(symbol):
            ask_price = float(self.driver.find_element(By.ID, "trading-order-ask").text)
        else:  # program supposed to crash, right ?
            return False

        if ask_price <= 1.00:
            print(f'Error: Cannot locate stocks priced under $1.00 ({symbol=}, price={ask_price})')

        self.driver.find_element(By.ID, "locate-tab-1").click()
        element = self.driver.find_element(By.ID, "short-list-input-symbol")
        element.clear()
        element.send_keys(symbol, Keys.RETURN)

        element = self.driver.find_element(By.ID, "short-list-input-shares")
        element.clear()
        quantity = shares_amount or math.ceil(int(buying_power / ask_price) / 100) * 100
        element.send_keys(quantity)

        while self.driver.find_element(By.ID, "short-list-locate-status").text == '':
            time.sleep(0.1)

        if self.driver.find_element(By.ID, "short-list-locate-status").text == 'Easy to borrow':
            locate_pps = 0.00
            locate_total = 0.00
            if debug_info:
                print(colored(f'Stock ({symbol}) is "Easy to borrow"', 'green'))
            return Data(locate_pps, locate_total)

        self.driver.find_element(By.ID, "short-list-button-locate").click()

        for i in range(300):
            try:
                locate_pps = float(self.driver.find_element(By.ID, f"oitem-l-{symbol.upper()}-cell-2").text)
                locate_total = float(self.driver.find_element(By.ID, f"oitem-l-{symbol.upper()}-cell-6").text)
                break
            except:
                if i == 15 or i == 299:
                    insufficient_bp = 'Insufficient BP to short a position with requested quantity.'
                    last_notif = self.fetch_notif(1)[-1][2]
                    if insufficient_bp in last_notif:
                        print(f"ERROR! {insufficient_bp}")
                        return False
                time.sleep(0.15)
        else:
            raise Exception(f'Error: not able to locate symbol element ({symbol=})')

        if locate_total < total_price:
            self.driver.find_element(By.XPATH,
                                     "/html/body/div[3]/section[1]/div[3]/div[1]/div[2]/div[2]/div[1]/div[2]/div[3]/div[1]/div/table/tbody/tr/td[9]/span[1]").click()
            if debug_info:
                print(colored(f'HTB Locate accepted ({symbol}, $ {locate_total})', 'cyan'))
        return Data(locate_pps, locate_total)

    def credit_locates(self, symbol: str, quantity=None):
        """
        sell stock locates

        if no value is given in 'quantity', it will credit all the shares available of the given symbol.
        :param symbol: str
        :param quantity: amount of shares to sell, must be a multiple of 100, ie: 100, 200, 300
        :return: True if operation succeeded, else: False.
        """
        located_symbols = self.driver.find_elements(By.XPATH,
                                                    '/html/body/div[3]/section[1]/div[3]/div[1]/div[2]/div[2]/div[1]/div[2]/div[5]/div[1]/div/table/tbody/tr/td[1]')
        located_symbols = [x.text for x in located_symbols]
        if symbol.upper() not in located_symbols:
            raise Exception(f"ERROR! cannot find {symbol} in located symbols")

        if quantity is not None:
            if quantity % 100 != 0:
                raise ValueError(f"ERROR! quantity needs to be divisible by 100 ({quantity=})")

            element = float(self.driver.find_element(By.ID, f"inv-{symbol.upper()}-cell-1").text)
            if quantity > element:
                raise ValueError(f"ERROR! you cannot credit more shares than u already have ({quantity} vs {element}")

            element = self.driver.find_element(By.ID, f"inv-{symbol.upper()}-sell-qty")
            element.clear()
            element.send_keys(quantity)

        self.driver.find_element(By.XPATH, f'//*[@id="inv-{symbol.upper()}-sell"]/button').click()
        return True

    def limit_order(self, order_direction: str, symbol: str, limit_price: float = None, shares_amount: int = None,
                    buying_power: float = None, log_info: bool = False):
        """
        Place a Limit Order

        Places a Limit Order, the following params are required: order_direction, symbol, limit_price, and you must
        provide one of these two: shares_amount or buying_power, not both.
        if buying_power param provided it will send an order with int(buying_power / share_price)
        :param order_direction: str: 'buy', 'sell', 'short', 'cover'
        :param symbol: str: e.g: 'aapl', 'amd', 'NVDA', 'GM'
        :param limit_price: float
        :param shares_amount: int
        :param buying_power: float
        :param log_info: bool, if True it will print information about the order
        :return: True if operation succeeded
        """
        timer_start = time.time()
        symbol = symbol.lower()
        order_direction = order_direction.lower()

        self._load_symbol(symbol)

        order_menu = Select(self.driver.find_element(By.ID, "trading-order-select-type"))
        order_menu.select_by_index(1)

        if limit_price is None:
            if order_direction.lower() == 'buy' or order_direction.lower() == 'cover':
                ask_price = float(self.driver.find_element(By.ID, "trading-order-ask").text)
                limit_price = ask_price + ask_bid_diff(ask_price)

            elif order_direction.lower() == 'sell' or order_direction.lower() == 'short':
                bid_price = float(self.driver.find_element(By.ID, "trading-order-bid").text)
                limit_price = bid_price - ask_bid_diff(bid_price)
        else:
            limit_price = limit_price

        price_input = self.driver.find_element(By.ID, "trading-order-input-price")
        price_input.clear()
        price_input.send_keys(limit_price)

        price = float(self.driver.find_element(By.ID, "trading-order-bid").text)
        share_quantity = shares_amount or int(buying_power / price)
        input_quantity = self.driver.find_element(By.ID, "trading-order-input-quantity")
        input_quantity.clear()
        input_quantity.send_keys(share_quantity)

        self.driver.find_element(By.ID, f"trading-order-button-{order_direction}").click()
        if log_info is True:
            print(f"Time: {return_time()}, Time elapsed: {time.time() - timer_start :.2f}, Order direction:",
                  f"{order_direction}, Symbol: {symbol}, Price: {price}, Shares amount: {share_quantity}")

        Data = namedtuple('Data', ['share_quantity'])
        return True, Data(share_quantity)

    def market_order(self):
        pass

    def stop_market_order(self):
        pass

    def fetch_notif(self, notif_amount: int = 1):
        """
        return a nested list with each sublist containing [time, title, message]

        important: note that u can only request the amount of notifications that are visible in the box
        without scrolling down (which usually is around 6-9 depending on each message length)
        example of nested list: (see the docs for a better look)
        [['11:34:49', 'Order canceled', 'Your Limit Buy order of 1 AMD was canceled.'],
         ['11:23:34', 'Level 2', 'You are not authorized for symbol: AMD'],
         ['11:23:34', 'Error', 'You are not authorized for symbol: AMD']]
        :param notif_amount: int amount of notifications to retrieve sorted by most recent
        :return: a nested list, with each sublist containing [time, title, message]
        """
        time.sleep(2)
        notif_lst = self.driver.find_elements(By.XPATH,
                                              "/html/body/div[3]/section[1]/div[3]/div[1]/div[3]/div[2]/div/div[1]/div/ul/li")
        notif_lst2 = [x.text.split('\n') for x in notif_lst if x.text != '']
        notifications = []
        for (notification, i) in zip(notif_lst2, range(notif_amount)):
            if len(notification) == 2:
                notification.insert(0, return_time())
            elif notification[0] == '' or notification[0] == '-':
                notification[0] = return_time()

            notifications.append(notification)
        return notifications

    def portfolio(self):
        """
        return a pandas dataframe with all open positions. (column names are the same as in the website)
        :return: pandas.DataFrame
        """
        df = pd.read_html(self.driver.page_source, attrs={'id': 'opTable-1'})[0]
        df_cols = self.driver.find_elements(By.XPATH,
                                            '/html/body/div[3]/section[1]/div[3]/div[2]/div[3]/div[2]/div[2]/div[1]/table/thead/tr/th')
        df.columns = [x.text for x in df_cols]
        return df

    def open_orders(self):
        """
        returns only rows from open positions that were opened today (intraday positions)
        :return: pandas.DataFrame
        """
        df = self.portfolio()
        filt = df['O/N'] == 'Yes'
        return df.loc[~filt]

    def invested(self, symbol):
        """
        returns True if the given symbol is in portfolio, else: false
        :param symbol: str: e.g: 'aapl', 'amd', 'NVDA', 'GM'
        :return: bool
        """
        elements = self.driver.find_elements(By.XPATH,
                                             '/html/body/div[3]/section[1]/div[3]/div[2]/div[3]/div[2]/div[2]/div[1]/div/div[1]/div/table/tbody/tr/td[1]')
        elements1 = [x.text for x in elements]
        if symbol.upper() in elements1:
            return True
        return False

    def incognito_mode(self):
        elements = [
         self.driver.find_element(By.ID, "h-realized-value"),
         self.driver.find_element(By.ID, "h-unrealizd-pl-value"),
         self.driver.find_element(By.ID, "h-total-pl-value"),
         self.driver.find_element(By.ID, "p-bp"),
         self.driver.find_element(By.ID, "h-cash-value"),
         self.driver.find_element(By.ID, "h-exposure-value"),
         self.driver.find_element(By.ID, "h-equity-value"),
         self.driver.find_element(By.ID, "h-equity-ratio-value"),
         self.driver.find_element(By.ID, "h-used-lvg-value"),
         self.driver.find_element(By.ID, "p-allowed-lev"),
         self.driver.find_element(By.ID, "h-select-account")
        ]
        for element in elements:
            self.driver.execute_script("arguments[0].setAttribute('style', 'display: none;')", element)
        return True

    def fetch_val(self, attribute: str):
        """
        fetch_val allows you to fetch a certain attribute from you're account, attribute must be one of the following
        elements: 'Day Realized', 'Day Unrealized', 'Day Total', 'Buying Power', 'Cash BP', 'Total Exposure', 'Equity',
        'Equity ratio', 'Used LVG', 'Allowed LVG'

        :param attribute:
        :return:
        """

        realize_value = self.driver.find_element(By.ID, "h-realized-value").text
        unrealizd_pl_value = self.driver.find_element(By.ID, "h-unrealizd-pl-value").text
        total_pl_value = self.driver.find_element(By.ID, "h-total-pl-value").text
        bp = self.driver.find_element(By.ID, "p-bp").text
        cash_value = self.driver.find_element(By.ID, "h-cash-value").text
        exposure_value = self.driver.find_element(By.ID, "h-exposure-value").text
        equity_value = self.driver.find_element(By.ID, "h-equity-value").text
        equity_ratio_value = self.driver.find_element(By.ID, "h-equity-ratio-value").text
        used_lvg_value = self.driver.find_element(By.ID, "h-used-lvg-value").text
        allowed_lev = self.driver.find_element(By.ID, "p-allowed-lev").text

        elements = {
            'Day Realized': realize_value, 'Day Unrealized': unrealizd_pl_value,
            'Day Total': total_pl_value, 'Buying Power': bp, 'Cash BP': cash_value,
            'Total Exposure': exposure_value, 'Equity': equity_value,
            'Equity ratio': equity_ratio_value, 'Used LVG': used_lvg_value,
            'Allowed LVG': allowed_lev
        }

        if attribute not in elements.keys():
            print(colored('ERROR! given attribute is wrong'), 'magenta')
        x = elements.get(attribute)
        return x


def ask_bid_diff(price):
    if price < 6:
        return 0.02
    elif 6 < price < 10:
        return 0.03
    elif price > 10:
        return 0.04
    else:
        return 0.02


def return_time():
    tz_ny = pytz.timezone('US/Eastern')
    datetime_ny = datetime.now(tz_ny)
    time1 = datetime_ny.strftime("%H:%M:%S.%f")[:-3]
    return time1

# clean values fetch_val before returning them..

