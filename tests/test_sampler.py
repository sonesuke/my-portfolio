import os

import pytest
import numpy.testing as npt

from mypo import Market
from mypo.sampler import Sampler

skip_long_tests = pytest.mark.skipif(True, reason="This test takes long time.")
TEST_DATA = os.path.join(os.path.dirname(__file__), "data", "test.bin")

MODEL_DATA = os.path.join(os.path.dirname(__file__), "data", "sample.bin")


@skip_long_tests
def test_save_load() -> None:
    market = Market.load(TEST_DATA)
    market = market.extract(market.get_index()[:10])
    sampler = Sampler(market, scenarios=5)
    sampler.save(MODEL_DATA)


def test_sample() -> None:
    sampler = Sampler.load(MODEL_DATA)
    samples = sampler.sample(10, 100)
    npt.assert_almost_equal(samples[0].mean(), [-0.0114186,  0.0020582])
    npt.assert_almost_equal(samples[9].mean(), [0.0102163, 0.005347])