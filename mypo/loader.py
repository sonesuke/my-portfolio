"""
Loader class for downloading stock data.

Download stock data from yahoo finance.

"""


from collections import OrderedDict
from typing import Dict

import pandas as pd
import yfinance as yf

from .market import Market


def normalized_raw(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize stock price data.

    Parameters
    ----------
    df
        raw stock price data.

    Returns
    -------
    out: pandas.DataFrame

    """
    out: pd.DataFrame = df.copy()
    out["r"] = out["Close"].pct_change() + 1.0
    out.dropna(inplace=True)
    out["ir"] = out["Dividends"] / out["Close"]
    return out


class Loader(object):
    """Loader class for downloading stock."""

    _tickers: Dict[str, pd.DataFrame]

    def __init__(self) -> None:
        self._tickers = OrderedDict()

    def get(self, ticker: str) -> None:
        """
        Get stock data of specified ticker.

        Parameters
        ----------
        ticker
            Ticker that you want to download stock data.

        Returns
        -------
        Nothing

        """
        ticker = ticker.upper()
        df = yf.Ticker(ticker).history(period="max")
        df.index = pd.to_datetime(df.index)
        self._tickers[ticker] = normalized_raw(df)

    def get_market(self) -> Market:
        """
        Get Market data.

        Returns
        -------
        Market data
        """
        return Market(self._tickers)
