import os

import numpy.testing as npt
import pandas as pd

from mypo import Market, SamplingMethod

TEST_DATA = os.path.join(os.path.dirname(__file__), "data", "test.bin")


def test_save_load() -> None:
    market = Market.load(TEST_DATA)
    index = market.get_rate_of_change().index
    assert index[0] == pd.Timestamp("2010-09-10")


def test_get_first_date() -> None:
    market = Market.load(TEST_DATA)
    assert market.get_first_date() == pd.Timestamp("2010-09-09")


def test_get_last_date() -> None:
    market = Market.load(TEST_DATA)
    market = market.head(300)
    assert market.get_last_date() == pd.Timestamp("2011-11-14")


def test_rate_of_change() -> None:
    market = Market.load(TEST_DATA)
    df = market.get_rate_of_change()
    npt.assert_almost_equal(df["VOO"][0], 0.004540062)
    npt.assert_almost_equal(df["IEF"][0], -0.00288483)


def test_filter() -> None:
    market = Market.load(TEST_DATA)
    market = market.filter(["VOO"])
    df = market.get_rate_of_change()
    assert df.columns == ["VOO"]


def test_raw_price() -> None:
    market = Market.load(TEST_DATA)
    df = market.get_raw()
    npt.assert_almost_equal(df["VOO"][0], 101.3199996)
    npt.assert_almost_equal(df["IEF"][0], 97.05999755)


def test_normalized_price() -> None:
    market = Market.load(TEST_DATA)
    df = market.get_normalized_prices()
    npt.assert_almost_equal(df["VOO"][0], 1)
    npt.assert_almost_equal(df["IEF"][0], 1)


def test_dividends() -> None:
    market = Market.load(TEST_DATA)
    df = market.get_price_dividends_yield()
    npt.assert_almost_equal(df["VOO"][0], 0)
    npt.assert_almost_equal(df["IEF"][0], 0)


def test_make_market() -> None:
    market = Market.create(ticker="NONE", start_date="2021-01-01", end_date="2021-12-31", yearly_gain=0.01)
    df = market.get_raw()
    assert df.index[0] == pd.Timestamp("2021-01-01")
    assert df.index[-1] == pd.Timestamp("2021-12-31")
    npt.assert_almost_equal(df["NONE"][0], 1)
    npt.assert_almost_equal(df["NONE"][-1], 1.01, decimal=3)

    df = market.get_price_dividends_yield()
    npt.assert_almost_equal(df["NONE"].sum(), 0)


def test_resample_yearly() -> None:
    market = Market.load(TEST_DATA)
    market = market.resample(method=SamplingMethod.YEAR)
    df = market.get_raw()
    npt.assert_almost_equal(df["VOO"][0], 130.38000488, decimal=5)
    npt.assert_almost_equal(df["IEF"][0], 107.48999786, decimal=5)


def test_resample_monthly() -> None:
    market = Market.load(TEST_DATA)
    market = market.resample(method=SamplingMethod.MONTH)
    df = market.get_raw()
    npt.assert_almost_equal(df["VOO"][0], 108.1800003051, decimal=5)
    npt.assert_almost_equal(df["IEF"][0], 97.6500015258, decimal=5)


def test_summary() -> None:
    market = Market.load(TEST_DATA)
    summary = market.get_summary()
    npt.assert_almost_equal(summary.loc["VOO", "daily return"], 0.0005541, decimal=5)


def test_relative() -> None:
    market = Market.load(TEST_DATA)
    relative = market.get_relative(ticker="VOO")
    print(relative)
    assert relative.index[0] == "VOO"
