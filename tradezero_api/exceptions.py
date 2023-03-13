from __future__ import annotations


class TradeZeroAPIException(Exception):
    """
    Base TradeZero Exception
    """
    pass


class MarketCloseError(TradeZeroAPIException):
    """
    Raised when the time isn't between 9:30 and 16:00 EST
    """
    pass


class AccountAttributeHiddenError(TradeZeroAPIException):
    """
    Raised when trying to access an account-attribute that is hidden
    """
    pass


class SymbolNotFoundError(TradeZeroAPIException):
    """
    Raised when the given symbol doesn't exist (or isn't available on TradeZero)
    """
    pass
