"""Optimizer for weights of portfolio."""

from datetime import datetime

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from mypo.common import safe_cast
from mypo.market import Market
from mypo.optimizer import BaseOptimizer
from mypo.optimizer.objective import covariance


class MaximumDiversificationOptimizer(BaseOptimizer):
    """Minimum variance optimizer."""

    _span: int
    _risk_free_rate: float

    def __init__(
        self,
        span: int = 260,
    ):
        """Construct this object.

        Args:
            span: Span for evaluation.
        """
        self._span = span
        super().__init__([1])

    def optimize(self, market: Market, at: datetime) -> np.float64:
        """Optimize weights.

        Args:
            market: Past market stock prices.
            at: Current date.

        Returns:
            Optimized weights
        """
        historical_data = market.extract(market.get_index() <= pd.to_datetime(at)).get_rate_of_change()
        prices = historical_data.tail(n=self._span).to_numpy()
        Q = covariance(prices)
        Q_diag = np.diag(Q)
        n = Q.shape[0]
        x = np.ones(n) / n

        def fn(
            x: np.ndarray,
            Q: np.ndarray,
            Q_diag: np.ndarray,
        ) -> np.float64:
            ret: np.float64 = -np.dot(x, Q_diag) / np.dot(np.dot(x, Q), x.T)
            return ret

        cons = {"type": "eq", "fun": lambda x: np.sum(x) - 1}
        bounds = [[0.0, 1.0] for i in range(n)]
        minout = minimize(
            fn,
            x,
            args=(Q, Q_diag),
            method="SLSQP",
            bounds=bounds,
            constraints=cons,
        )
        self._weights = safe_cast(minout.x)
        return np.float64(minout.fun)
