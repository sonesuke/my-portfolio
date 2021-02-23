import datetime

import numpy as np
import numpy.typing as npt
import pandas as pd

from .common import calc_capital_gain_tax, calc_fee, calc_income_gain_tax, safe_cast
from .market import Market
from .rebalancer import Rebalancer
from .reporter import Reporter


class Runner(object):
    assets: np.ndarray
    rebalancer: Rebalancer
    reporter: Reporter
    initial_assets: np.ndarray
    cash: np.float64
    tax_rate: np.float64
    spending: np.float64
    fee_rate: np.float64

    def __init__(
        self, assets: npt.ArrayLike, rebalancer: Rebalancer, cash: np.float64, spending: np.float64
    ):
        self.assets = safe_cast(assets)
        self.initial_assets = self.assets
        self.rebalancer = rebalancer
        self.reporter = Reporter()
        self.cash = cash
        self.spending = spending
        self.tax_rate = 0.2  # type: ignore
        self.fee_rate = 0.005  # type: ignore

    def total_assets(self) -> np.float64:
        return np.float64(np.sum(self.assets) + self.cash)

    def apply(
        self,
        index: datetime.datetime,
        market: npt.ArrayLike,
        price_dividends_yield: npt.ArrayLike,
        expense_ratio: npt.ArrayLike,
    ) -> None:
        market = safe_cast(market)
        price_dividends_yield = safe_cast(price_dividends_yield)
        expense_ratio = safe_cast(expense_ratio)

        # apply market prices
        self.assets = self.assets * market
        diff = self.rebalancer.apply(index, self.assets, self.cash)
        deal: np.float64 = np.abs(diff)

        # process of capital gain
        capital_gain_tax = calc_capital_gain_tax(self.initial_assets, self.assets, diff, self.tax_rate)
        self.cash -= capital_gain_tax
        fee = calc_fee(diff, self.fee_rate)
        self.cash -= fee
        self.cash -= np.float64(np.sum(diff))
        self.assets += diff

        # process of income gain
        income_gain = np.sum(self.assets * price_dividends_yield)
        income_gain_tax = calc_income_gain_tax(self.assets, price_dividends_yield, self.tax_rate)
        self.cash += income_gain
        self.cash -= income_gain_tax

        # process of others
        self.assets = (1.0 - expense_ratio) * self.assets

        # record to reporter
        capital_gain: np.float64 = np.float64(np.sum(self.assets))
        self.reporter.record(index, capital_gain, income_gain, self.cash, deal, fee, capital_gain_tax, income_gain_tax)

    def run(self, market: Market, expense_ratio: npt.ArrayLike) -> None:
        index = market.get_index()
        markets = market.get_prices().to_records(index=False)
        price_dividends_yield = market.get_price_dividends_yield().to_records(index=False)
        expense_ratio = safe_cast(expense_ratio)
        for i in range(len(markets)):
            self.apply(index[i], markets[i], price_dividends_yield[i], expense_ratio)

    def report(self) -> pd.DataFrame:
        return self.reporter.report()
