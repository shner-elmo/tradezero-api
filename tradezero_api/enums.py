from enum import Enum


class Order(Enum):
    """Order types"""
    BUY = 'buy'
    SELL = 'sell'
    SHORT = 'short'
    COVER = 'cover'


class TIF(Enum):
    """Time-in-force values"""
    DAY = 'DAY'
    GTC = 'GTC'
    GTX = 'GTX'
