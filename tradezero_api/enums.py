from __future__ import annotations

from enum import Enum


class OrderType(str, Enum):
    """All the order-types available in the drop-down menu"""
    market = 'MKT'
    limit = 'LMT'
    stop = 'Stop-MKT'
    stop_limit = 'Stop-LMT'
    market_on_close = 'MKT-Close'
    limit_on_close = 'LMT-Close'
    range = 'RANGE'


class TIF(str, Enum):
    """Time-in-force values"""
    DAY = 'DAY'
    GTC = 'GTC'
    GTX = 'GTX'


class Order(str, Enum):
    """Order types"""
    BUY = 'buy'
    SELL = 'sell'
    SHORT = 'short'
    COVER = 'cover'


class PortfolioTab(str, Enum):
    """The ID for each """
    open_positions = 'portfolio-tab-op-1'
    closed_positions = 'portfolio-tab-cp-1'
    active_orders = 'portfolio-tab-ao-1'
    inactive_orders = 'portfolio-tab-io-1'
