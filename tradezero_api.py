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
    def __init__(self, chrome_driver_path: str, user_name: str, password: str, headless: bool = True,
                 incognito_mode: bool = False, buying_power: int = 100000):
        """
        :param chrome_driver_path: path to chromedriver.exe
        :param user_name: TradeZero user_name
        :param password: TradeZero password
        :param headless: True will run the browser in headless mode, which means it won't be visible
        :param incognito_mode: bool, if True: Hide account attributes (acc username, equity, total exposure...)
        :param buying_power: must provide a value which will be the default equity amount for buying and selling
        """
        self.user_name = user_name
        self.password = password
        self.incognito_mode = incognito_mode
        self.buying_power = buying_power

        s = Service(chrome_driver_path)
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        if headless is True:
            options.headless = headless

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
            text_elements = [i.text for i in elements]
            if 'Portfolio' in text_elements:
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
        if self.driver.current_url == 'https://standard.tradezeroweb.us/':
            raise Exception('Already logged in')

        login_form = self.driver.find_element(By.ID, "login")
        login_form.send_keys(self.user_name)

        password_form = self.driver.find_element(By.ID, "password")
        password_form.send_keys(self.password, Keys.RETURN)

        self._dom_fully_loaded(150)
        if self.incognito_mode:
            self._incognito_mode()

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
        :return: True if symbol data loaded, False if prices == 0.00 (mkt closed), Error if symbol not found
        """
        current_symbol = self.driver.find_element(By.ID, 'trading-order-symbol').text.replace('(USD)', '')
        if symbol.upper() == current_symbol:
            price = self.driver.find_element(By.ID, "trading-order-ask").text.replace('.', '')
            if price.isdigit() and float(price) > 0:
                return True

        input_symbol = self.driver.find_element(By.ID, "trading-order-input-symbol")
        input_symbol.send_keys(symbol, Keys.RETURN)
        time.sleep(0.04)

        for i in range(300):
            price = self.driver.find_element(By.ID, "trading-order-ask").text.replace('.', '')
            if price == '':
                time.sleep(0.01)

            elif price.isdigit() and float(price) == 0:
                print(f"Warning: Market Closed, ask/bid = {price}")
                return False

            elif price.isdigit():
                return True
        else:
            last_notif = self.fetch_notif(1)[-1][2]
            message = f'Symbol not found: {symbol.upper()}'
            if message in last_notif:
                raise Exception(f"ERROR: {symbol=} Not found")

    def data(self, symbol: str):
        """
        return a namedtuple with data for the given symbol

        returns a namedtuple with data for the given symbol, the properties are:
        'open', 'high', 'low', 'close', 'volume', 'last', 'ask', 'bid'
        :param symbol: str: ex: 'aapl', 'amd', 'NVDA', 'GM'
        :return: namedtuple = (open, high, low, close, volume, last, ask, bid)
        """
        Data = namedtuple('Data', ['open', 'high', 'low', 'close', 'volume', 'last', 'ask', 'bid'])

        if self._load_symbol(symbol) is False:
            return Data(0.0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0)

        element_ids = [
            'trading-order-open',
            'trading-order-high',
            'trading-order-low',
            'trading-order-close',
            'trading-order-vol',
            'trading-order-p',
            'trading-order-ask',
            'trading-order-bid',
        ]
        lst = []
        for id_ in element_ids:
            val = self.driver.find_element(By.ID, id_).text

            if id_ == 'trading-order-vol':
                val = (val.replace(',', ''))
            lst.append(float(val))

        return Data._make(lst)

    def locate_stock(self, symbol: str, total_price: float = 0, buying_power: float = None,
                     share_amount: int = None, debug_info: bool = False):
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
        :param share_amount: int, default: 0, must be a multiple of 100 (100, 200, 300...)
        :return: dictionary = {'locate_pps': locate_pps, 'locate_total': locate_total} (pps = price per share)
        :param debug_info: bool, if True it will print info about the locates in the console
        """
        Data = namedtuple('Data', ['locate_pps', 'locate_total'])

        if buying_power is not None and share_amount is not None:
            raise Exception('ERROR: Cannot Provide both buying_power and share_amount parameters, only one')

        if share_amount is not None and share_amount % 100 != 0:
            raise Exception(f'ERROR: share_amount is not divisible by 100 ({share_amount=})')

        if self._load_symbol(symbol):
            ask_price = float(self.driver.find_element(By.ID, "trading-order-ask").text)
        else:  # program supposed to crash, right ?
            return False

        if ask_price <= 1.00:
            print(f'Error: Cannot locate stocks priced under $1.00 ({symbol=}, price={ask_price})')

        self.driver.find_element(By.ID, "locate-tab-1").click()
        input_symbol = self.driver.find_element(By.ID, "short-list-input-symbol")
        input_symbol.clear()
        input_symbol.send_keys(symbol, Keys.RETURN)

        input_shares = self.driver.find_element(By.ID, "short-list-input-shares")
        input_shares.clear()
        quantity = share_amount or math.ceil(int(buying_power / ask_price) / 100) * 100
        input_shares.send_keys(quantity)

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
                time.sleep(0.15)
                if i == 15 or i == 299:
                    insufficient_bp = 'Insufficient BP to short a position with requested quantity.'
                    last_notif = self.fetch_notif(1)[-1][2]
                    if insufficient_bp in last_notif:
                        print(f"ERROR! {insufficient_bp}")
                        return False
        else:
            raise Exception(f'Error: not able to locate symbol element ({symbol=})')

        if locate_total <= total_price:
            self.driver.find_element(By.XPATH, f'//*[@id="oitem-l-{symbol.upper()}-cell-8"]/span[1]').click()
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
        located_symbols = self.driver.find_elements(By.XPATH, '//*[@id="locate-inventory-table"]/tbody/tr/td[1]')
        located_symbols = [x.text for x in located_symbols]

        if symbol.upper() not in located_symbols:
            raise Exception(f"ERROR! cannot find {symbol} in located symbols")

        if quantity is not None:
            if quantity % 100 != 0:
                raise ValueError(f"ERROR! quantity needs to be divisible by 100 ({quantity=})")

            located_shares = float(self.driver.find_element(By.ID, f"inv-{symbol.upper()}-cell-1").text)
            if quantity > located_shares:
                raise ValueError(f"ERROR! you cannot credit more shares than u already have "
                                 f"({quantity} vs {located_shares}")

            input_quantity = self.driver.find_element(By.ID, f"inv-{symbol.upper()}-sell-qty")
            input_quantity.clear()
            input_quantity.send_keys(quantity)

        self.driver.find_element(By.XPATH, f'//*[@id="inv-{symbol.upper()}-sell"]/button').click()
        return True

    def limit_order(self, order_direction: str, symbol: str, limit_price: float, share_amount: int = None,
                    buying_power: float = None, log_info: bool = False):
        """
        Place a Limit Order

        Places a Limit Order, the following params are required: order_direction, symbol, limit_price, and you must
        provide one of these two: share_amount or buying_power, not both.
        if buying_power param provided it will send an order with int(buying_power / share_price)
        :param order_direction: str: 'buy', 'sell', 'short', 'cover'
        :param symbol: str: e.g: 'aapl', 'amd', 'NVDA', 'GM'
        :param limit_price: float
        :param share_amount: int
        :param buying_power: float
        :param log_info: bool, if True it will print information about the order
        :return: True if operation succeeded
        """
        timer_start = time.time()
        symbol = symbol.lower()
        order_direction = order_direction.lower()

        if buying_power is not None and share_amount is not None:
            raise Exception('ERROR: Cannot Provide both buying_power and share_amount parameters, only one')

        self._load_symbol(symbol)

        order_menu = Select(self.driver.find_element(By.ID, "trading-order-select-type"))
        order_menu.select_by_index(1)

        price = float(self.driver.find_element(By.ID, "trading-order-bid").text)
        share_quantity = share_amount or int(buying_power / price)
        input_quantity = self.driver.find_element(By.ID, "trading-order-input-quantity")
        input_quantity.clear()
        input_quantity.send_keys(share_quantity)

        price_input = self.driver.find_element(By.ID, "trading-order-input-price")
        price_input.clear()
        price_input.send_keys(limit_price)

        self.driver.find_element(By.ID, f"trading-order-button-{order_direction}").click()
        if log_info is True:
            print(f"Time: {return_time()}, Time elapsed: {time.time() - timer_start :.2f}, Order direction:",
                  f"{order_direction}, Symbol: {symbol}, Price: {price}, Shares amount: {share_quantity}")
        return True

    def market_order(self):
        pass

    def stop_market_order(self):
        pass

    def fetch_notif(self, notif_amount: int = 1):
        """
        return a nested list with each sublist containing [time, title, message]

        note that u can only request the amount of notifications that are visible in the box/widget
        without scrolling down (which usually is around 6-9 depending on each message length)
        example of nested list: (see the docs for a better look):
        [['11:34:49', 'Order canceled', 'Your Limit Buy order of 1 AMD was canceled.'],
         ['11:23:34', 'Level 2', 'You are not authorized for symbol: AMD'],
         ['11:23:34', 'Error', 'You are not authorized for symbol: AMD']]
        :param notif_amount: int amount of notifications to retrieve sorted by most recent
        :return: a nested list, with each sublist containing [time, title, message]
        """
        time.sleep(2)
        notif_lst = self.driver.find_elements(By.XPATH,
                                              '//*[@id="notifications-list-1"]/li')
        notif_lst_text = [x.text.split('\n') for x in notif_lst if x.text != '']
        notifications = []
        for (notification, i) in zip(notif_lst_text, range(notif_amount)):
            if len(notification) == 2:
                notification.insert(0, return_time())
            elif notification[0] == '' or notification[0] == '-':
                notification[0] = return_time()

            notifications.append(notification)
        return notifications

    def portfolio(self, return_type: str = 'df'):
        """
        return Portfolio as a pandas.DataFrame or nested dict,
        the column names are the following: 'symbol', 'type', 'qty', 'p_close', 'entry',
        'price', 'change', '%change', 'day_pnl', 'pnl', 'overnight'
        :param return_type: 'df' or 'dict'
        :return: pandas.DataFrame
        """
        df = pd.read_html(self.driver.page_source, attrs={'id': 'opTable-1'})[0]
        df.columns = [
            'symbol', 'type', 'qty', 'p_close', 'entry', 'price', 'change', '%change', 'day_pnl', 'pnl', 'overnight'
        ]
        if return_type == 'dict':
            return df.to_dict('records')
        return df

    def open_orders(self):
        """
        returns DF with only positions that were opened today (intraday positions)
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
        symbol_list = self.driver.find_elements(By.XPATH, '//*[@id="opTable-1"]/tbody/tr/td[1]')
        symbol_list_text = [x.text for x in symbol_list]
        if symbol.upper() in symbol_list_text:
            return True
        return False

    def _incognito_mode(self):
        """
        Hides all account attributes i.e, account username, equity-value, cash-value, realized-value...
        :return: bool
        """
        element_ids = [
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
            "h-loginId"
        ]
        for id_ in element_ids:
            element = self.driver.find_element(By.ID, id_)
            self.driver.execute_script("arguments[0].setAttribute('style', 'display: none;')", element)
        return True

    def fetch_val(self, attribute: str):
        """
        fetch account value (ex: 'Day Realized', 'Day Unrealized', 'Buying Power')

        fetch_val allows you to fetch a certain attribute from you're account, the attribute must be one of the
        following elements: 'Day Realized', 'Day Unrealized', 'Day Total', 'Buying Power', 'Cash BP', 'Total Exposure',
        'Equity', 'Equity ratio', 'Used LVG', 'Allowed LVG'.
        :param attribute: str
        :return: attribute value
        """
        attributes = {
            'Day Realized': 'h-realized-value',
            'Day Unrealized': 'h-unrealizd-pl-value',
            'Day Total': 'h-total-pl-value',
            'Buying Power': 'p-bp',
            'Cash BP': 'h-cash-value',
            'Total Exposure': 'h-exposure-value',
            'Equity': 'h-equity-value',
            'Equity ratio': 'h-equity-ratio-value',
            'Used LVG': 'h-used-lvg-value',
            'Allowed LVG': 'p-allowed-lev'
        }

        if attribute not in attributes.keys():
            raise KeyError('ERROR! given attribute is not valid')

        x = self.driver.find_element(By.ID, attributes[attribute]).text

        chars = ['$', '%', 'x', ',']
        for char in chars:
            x = x.replace(char, '')

        return float(x)


def return_time():
    tz_ny = pytz.timezone('US/Eastern')
    datetime_ny = datetime.now(tz_ny)
    time1 = datetime_ny.strftime("%H:%M:%S.%f")[:-3]
    return time1
