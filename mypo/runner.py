"""Simulation."""

from typing import Any, List, Optional

import numpy as np
from tqdm import tqdm

from mypo.common import calc_capital_gain_tax, calc_fee, calc_income_gain_tax, safe_cast
from mypo.market import Market
from mypo.model_selection import Fold
from mypo.rebalancer.base_rebalancer import BaseRebalancer
from mypo.rebalancer.no_rebalancer import NoRebalancer
from mypo.reporter import Reporter
from mypo.settings import DEFAULT_SETTINGS, Settings

WEEK_DAYS = int(365 * 5 / 7)


class Runner(object):
    """Runner of simulation."""

    _assets: np.ndarray
    _average_assets_prices: np.ndarray
    _rebalancer: BaseRebalancer
    _reporter: Reporter
    _cash: np.float64
    _withdraw: np.float64
    _settings: Settings
    _month: int

    def __init__(
        self,
        rebalancer: BaseRebalancer = NoRebalancer(),
        settings: Settings = DEFAULT_SETTINGS,
    ):
        """Construct this object.

        Args:
            rebalancer: Rebalance strategy.
            settings: Settings.
        """
        self._rebalancer = rebalancer
        self._reporter = Reporter()
        self._settings = settings
        self._month = 0

    def apply(self, market: Market, i: int) -> None:
        """Apply current market situation.

        Args:
            market: Market data.
            i: Index.
        """
        at = market.get_index()[i]
        prices = market.get_rate_of_change().to_records(index=False)[i]
        price_dividends_yield = market.get_price_dividends_yield().to_records(index=False)[i]
        expense_ratio = market.get_expense_ratio()

        prices = safe_cast(prices)
        price_dividends_yield = safe_cast(price_dividends_yield)
        expense_ratio = safe_cast(expense_ratio)

        # apply withdraw
        if self._month != at.month:
            self._cash -= self._withdraw / 12
        self._month = at.month

        # apply market prices
        previous_assets = self._assets
        self._assets = self._assets * (1.0 + prices)
        capital_gain = np.float64(self._assets.sum() - previous_assets.sum())

        diff = self._rebalancer.apply(at, market, self._assets, self._cash)
        self._assets += diff
        capital_gain_tax = calc_capital_gain_tax(self._average_assets_prices, prices, diff, self._settings)
        fee = calc_fee(diff, self._settings)

        # process of income gain
        income_gain = (self._assets * price_dividends_yield).sum()
        income_gain_tax = calc_income_gain_tax(self._assets, price_dividends_yield, self._settings)

        # process of others
        self._cash = self._cash + income_gain - income_gain_tax - diff.sum() - fee - capital_gain_tax
        self._assets = (1.0 - expense_ratio / WEEK_DAYS) * self._assets
        deal = np.max([diff.sum(where=diff > 0), -diff.sum(where=diff < 0)])
        trading_prices = np.where(diff > 0, 1.0 + prices, self._average_assets_prices)
        self._average_assets_prices = np.divide(
            self._average_assets_prices * previous_assets + diff * trading_prices,
            self._assets,
            out=np.zeros_like(self._assets),
            where=(self._assets != 0),
        )

        # record to reporter
        self._reporter.record(
            at=at,
            total_assets=np.float64(np.sum(self._assets) + self._cash),
            tickers=market.get_tickers(),
            weights=self._rebalancer.get_optimizer().get_weights(),
            capital_gain=capital_gain,
            income_gain=income_gain,
            cash=self._cash,
            deal=deal,
            fee=fee,
            capital_gain_tax=capital_gain_tax,
            income_gain_tax=income_gain_tax,
        )

    def run(
        self,
        assets: Optional[List[float]] = None,
        cash: float = 0.0,
        withdraw: float = 0.0,
        market: Optional[Market] = None,
        train_span: int = 0,
        fold: Optional[Fold] = None,
        verbose: bool = False,
    ) -> None:
        """Run simulation.

        Args:
            assets: Initial asset.
            cash: Initial cash.
            withdraw: Withdraw.
            market: Market data.
            train_span: Periods of training span.
            fold: Fold.
            verbose: Show progress.
        """
        self._cash = np.float64(cash)
        self._withdraw = np.float64(withdraw)

        if market is None and fold is not None:
            market = fold.get_valid()
            train_span = fold.get_train_span()

        if market is None:
            assert False  # pragma: no cover

        n = len(market.get_tickers())
        if assets is None:
            self._assets = safe_cast(np.ones(n) / n)
        else:
            self._assets = safe_cast(assets)

        self._average_assets_prices = np.ones(n)
        target = range(train_span, market.get_length())

        def wrap(x: Any) -> Any:
            """Wrapper for tqdm."""
            return tqdm(x) if verbose else x

        for i in wrap(target):
            self.apply(market, i)

    def report(self) -> Reporter:
        """Report simulation.

        Returns:
            result
        """
        return self._reporter
