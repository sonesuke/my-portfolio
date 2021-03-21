"""Optimizer for weights of portfolio."""

from datetime import datetime

import numpy as np
from scipy.optimize import minimize

from mypo.common import safe_cast
from mypo.market import Market
from mypo.optimizer.base_optimizer import BaseOptimizer
from mypo.optimizer.objective import covariance, semi_covariance


class MinimumVarianceOptimizer(BaseOptimizer):
    """Minimum variance optimizer."""

    _with_semi_covariance: bool
    _span: int

    def __init__(
        self,
        span: int = 260,
        with_semi_covariance: bool = False,
        minimum_return: float = None,
    ):
        """Construct this object.

        Args:
            span: Span for evaluation.
            with_semi_covariance: whether use semi covariance mode if it's Ture.
            minimum_return: Minimum return.
        """
        self._span = span
        self._with_semi_covariance = with_semi_covariance
        self._minimum_return = minimum_return
        super().__init__()

    def optimize(self, market: Market, at: datetime) -> None:
        """Optimize weights.

        Args:
            market: Past market stock prices.
            at: Current date.

        Returns:
            Optimized weights
        """
        historical_data = market.extract(market.get_index() < at).get_rate_of_change()
        prices = historical_data.tail(n=self._span).to_numpy()
        Q = semi_covariance(prices) if self._with_semi_covariance else covariance(prices)
        n = len(historical_data.columns)
        x = np.ones(n) / n

        def fn(x: np.ndarray, Q: np.ndarray) -> np.float64:
            ret: np.float64 = np.dot(np.dot(x, Q), x.T) / np.max(np.abs(Q))
            return ret

        cons = [{"type": "eq", "fun": lambda x: np.sum(x) - 1}]
        if self._minimum_return is not None:
            ret = prices.mean(axis=0)
            daily_risk_free_rate = (1.0 + self._minimum_return) ** (1 / 252) - 1.0
            print(ret)
            print(daily_risk_free_rate)
            cons += [
                {
                    "type": "ineq",
                    "fun": lambda x: np.dot(ret, x) - daily_risk_free_rate,
                }
            ]

        bounds = [[0.0, 1.0] for i in range(n)]
        minout = minimize(fn, x, args=(Q), method="SLSQP", bounds=bounds, constraints=cons)
        self._weights = safe_cast(minout.x)
