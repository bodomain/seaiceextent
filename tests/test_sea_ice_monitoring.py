"""Checks of scientific edge cases and covariance implementation.

Run: python -m unittest discover -s tests -v
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from sea_ice_monitoring import (
    aggregate_periods, calendar_climatology, circular_block_bootstrap,
    linear_trend, load_series, matched_ytd, read_daily, seasonal_extrema,
)


def frame(index, values=None):
    return pd.DataFrame({
        "extent": np.ones(len(index)) if values is None else values,
        "provisional": False, "provider_interpolated": False,
        "provider_extrapolated": False,
    }, index=index)


class DataTests(unittest.TestCase):
    def test_missing_is_not_zero_or_interpolated(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.txt"
            path.write_text("2000 2000 01 01 1000000 OSI450A1_interp\n"
                            "2000 2000 01 02 -999 MISSING\n"
                            "2000 2000 01 04 2000000 OSI438AFT\n")
            result = read_daily(path, "nh")
            self.assertEqual(len(result), 4)
            self.assertTrue(np.isnan(result.extent.iloc[1]))
            self.assertTrue(np.isnan(result.extent.iloc[2]))
            self.assertEqual(result.source.iloc[2], "ABSENT")
            self.assertTrue(result.provider_interpolated.iloc[0])
            self.assertTrue(result.provisional.iloc[-1])
            self.assertEqual(result.extent.iloc[-1], 2.0)

    def test_duplicate_dates_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.txt"
            path.write_text("2000 2000 01 01 1000000 X\n" * 2)
            with self.assertRaisesRegex(ValueError, "unique"):
                read_daily(path, "nh")

    def test_both_fast_track_source_labels_are_provisional(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.txt"
            path.write_text("2000 2000 01 01 1000000 OSI438FT\n"
                            "2000 2000 01 02 1000000 OSI438AFT\n"
                            "2000 2000 01 03 1000000 OSI438\n")
            result = read_daily(path, "nh")
            self.assertEqual(result.provisional.tolist(), [True, True, False])

    def test_missing_hemisphere_does_not_become_global_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            for h, value in [("nh", -999), ("sh", 2000000)]:
                Path(tmp, f"osisaf_{h}_sie_daily.txt").write_text(f"2000 2000 01 01 {value} X\n")
            result = load_series(tmp)
            self.assertTrue(np.isnan(result["global"].extent.iloc[0]))

    def test_partial_leap_month_and_year_are_excluded(self):
        data = frame(pd.date_range("2000-01-01", "2000-02-28"))
        monthly = aggregate_periods(data, "ME")
        self.assertTrue(monthly.complete.iloc[0])
        self.assertFalse(monthly.complete.iloc[1])
        self.assertEqual(monthly.expected_days.iloc[1], 29)
        self.assertTrue(np.isnan(monthly["mean"].iloc[1]))
        self.assertTrue(np.isnan(aggregate_periods(data, "YE")["mean"].iloc[0]))

    def test_one_missing_day_excludes_full_month(self):
        data = frame(pd.date_range("2001-01-01", "2001-01-31"))
        data.iloc[10, data.columns.get_loc("extent")] = np.nan
        self.assertFalse(aggregate_periods(data, "ME").complete.iloc[0])

    def test_calendar_climatology_does_not_shift_after_leap_day(self):
        idx = pd.to_datetime(["1999-03-01", "2000-02-29", "2000-03-01"])
        result = calendar_climatology(frame(idx, [2, 99, 4]), (1999, 2000))
        self.assertEqual(result.loc["03-01", "mean"], 3)
        self.assertEqual(result.loc["02-29", "count"], 1)

    def test_ytd_compares_equal_windows_and_handles_leap_asof(self):
        data = frame(pd.date_range("1999-01-01", "2000-12-31"))
        result = matched_ytd(data, "2000-02-29", first_year=1999)
        self.assertTrue((result.valid_days == 59).all())
        self.assertTrue((result.expected_days == 59).all())

    def test_twenty_year_ytd_includes_partial_2026_and_excludes_2006(self):
        index = pd.date_range("2006-01-01", "2026-11-10")
        # A fixed seasonal cycle makes unequal full/partial-year means misleading.
        data = frame(index, np.where(index.month <= 6, 1.0, 9.0))
        data.loc["2026-10-27":, "provisional"] = True
        result = matched_ytd(data, "2026-11-10", first_year=2007)
        self.assertEqual(result.index.tolist(), list(range(2007, 2027)))
        self.assertTrue(result.valid_days.eq(314).all())
        self.assertTrue(result["mean"].notna().all())
        np.testing.assert_allclose(result["mean"], result["mean"].iloc[0])
        full_years = aggregate_periods(data, "YE")
        self.assertTrue(np.isnan(full_years.loc["2026-12-31", "mean"]))
        self.assertNotAlmostEqual(result.loc[2026, "mean"], full_years.loc["2025-12-31", "mean"])

    def test_current_month_fits_use_only_available_complete_months(self):
        data = frame(pd.date_range("2007-01-01", "2026-11-10"))
        data.loc["2026-10-27":, "provisional"] = True
        monthly = aggregate_periods(data, "ME")
        for month in range(1, 13):
            selected = monthly.loc[monthly.index.month == month]
            series = pd.Series(selected["mean"].to_numpy(), index=selected.index.year).reindex(range(2007, 2027))
            self.assertEqual(series.notna().sum(), 20 if month <= 10 else 19)
            self.assertEqual(pd.notna(series.loc[2026]), month <= 10)
        self.assertTrue(monthly.loc["2026-10-31", "complete"])
        self.assertEqual(monthly.loc["2026-10-31", "provisional_days"], 5)
        self.assertFalse(monthly.loc["2026-11-30", "complete"])

    def test_incomplete_extrema_window_is_excluded(self):
        data = frame(pd.date_range("1979-01-01", "1979-10-10"))
        result = seasonal_extrema(data, "nh", 1979).set_index("event")
        self.assertTrue(result.loc["maximum", "complete"])
        self.assertFalse(result.loc["minimum", "complete"])
        self.assertTrue(np.isnan(result.loc["minimum", "extent"]))


class TrendTests(unittest.TestCase):
    def test_hac_matches_statsmodels_for_contiguous_years(self):
        rng = np.random.default_rng(12)
        years = np.arange(1979, 2026)
        y = 5 - .025 * (years - 1979) + rng.normal(0, .3, len(years))
        for lag in [0, 1, 3, 5, 8]:
            result = linear_trend(pd.Series(y, index=years), maxlags=lag)
            X = np.column_stack([np.ones(len(years)), years - years.mean()])
            expected = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": lag, "use_correction": True}, use_t=True)
            np.testing.assert_allclose(result["covariance"], expected.cov_params(), rtol=1e-11, atol=1e-14)
            np.testing.assert_allclose(result["slope_decade"], expected.params[1] * 10)
            np.testing.assert_allclose([result["ci_low"], result["ci_high"]], expected.conf_int()[1] * 10)

    def test_hac_gaps_use_calendar_lags_not_adjacent_rows(self):
        years = np.array([1979, 1980, 1982, 1983, 1986, 1987, 1989, 1990, 1992, 1993])
        y = np.array([5, 5.1, 4.8, 5.2, 4.9, 4.6, 4.7, 4.5, 4.4, 4.8])
        result = linear_trend(pd.Series(y, index=years), maxlags=1)
        X = np.column_stack([np.ones(len(y)), years - years.mean()])
        fit = sm.OLS(y, X).fit()
        score = X * fit.resid[:, None]
        meat = score.T @ score
        for i in range(len(years)):
            for j in range(i):
                if years[i] - years[j] == 1:
                    meat += .5 * (np.outer(score[i], score[j]) + np.outer(score[j], score[i]))
        bread = np.linalg.inv(X.T @ X)
        expected = bread @ meat @ bread * len(y) / (len(y) - 2)
        np.testing.assert_allclose(result["covariance"], expected, rtol=1e-10)
        naive = fit.get_robustcov_results(cov_type="HAC", maxlags=1, use_correction=True)
        self.assertFalse(np.allclose(result["covariance"], naive.cov_params()))

    def test_bootstrap_is_seeded_and_preserves_exact_linear_trend(self):
        series = pd.Series(10 - .1 * np.arange(30), index=np.arange(1990, 2020))
        np.testing.assert_allclose(circular_block_bootstrap(series, draws=200), -1, atol=1e-12)
        noisy = series + np.random.default_rng(5).normal(0, .2, len(series))
        a = circular_block_bootstrap(noisy, draws=200, seed=2)
        b = circular_block_bootstrap(noisy, draws=200, seed=2)
        np.testing.assert_array_equal(a, b)

    def test_bootstrap_rejects_missing_years(self):
        series = pd.Series(np.arange(20), index=np.r_[np.arange(1990, 2000), np.arange(2001, 2011)])
        with self.assertRaisesRegex(ValueError, "contiguous"):
            circular_block_bootstrap(series)


if __name__ == "__main__":
    unittest.main()
