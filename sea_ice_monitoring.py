"""Auditable data preparation and trend estimators for sea_ice_monitoring.ipynb.

Raw files are never modified. Extent is represented in million km². Missing
values remain missing; provider interpolation flags remain available for audit.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


NAMES = {"nh": "Arctic", "sh": "Antarctic", "global": "Global sum"}
COLS = ["fractional_year", "year", "month", "day", "extent_km2", "source"]


def read_daily(path, hemisphere):
    """Read and validate one complete daily grid, without inventing observations."""
    raw = pd.read_csv(path, sep=r"\s+", comment="#", names=COLS)
    if raw.empty or raw["source"].isna().any():
        raise ValueError("Expected nonempty daily records with six columns including source flags")
    dates = pd.to_datetime(raw[["year", "month", "day"]], errors="raise")
    if dates.duplicated().any() or not dates.is_monotonic_increasing:
        raise ValueError("Dates must be unique and in increasing order")
    values = pd.to_numeric(raw["extent_km2"], errors="raise")
    if (~((values.between(0, 40_000_000)) | values.eq(-999))).any():
        raise ValueError("Unexpected sea-ice extent value")
    raw.index = pd.DatetimeIndex(dates, name="date")
    frame = raw[["extent_km2", "source"]].reindex(
        pd.date_range(dates.min(), dates.max(), freq="D", name="date")
    )
    frame["source"] = frame["source"].fillna("ABSENT")
    frame["extent"] = frame["extent_km2"].replace(-999, np.nan) / 1e6
    frame["provider_interpolated"] = frame["source"].str.contains("interp", regex=False)
    frame["provider_extrapolated"] = frame["source"].str.contains("extrap", regex=False)
    # Recognize both documented AMSR2 ...FT and observed AMSR3 ...AFT labels.
    frame["provisional"] = frame["source"].str.contains(r"FT(?:_|$)", regex=True)
    frame["hemisphere"] = hemisphere
    return frame


def load_series(directory):
    """Return aligned hemispheric records and a sum requiring both observations."""
    directory = Path(directory)
    frames = {
        h: read_daily(directory / f"osisaf_{h}_sie_daily.txt", h)
        for h in ("nh", "sh")
    }
    extents = pd.concat({h: f["extent"] for h, f in frames.items()}, axis=1)
    global_frame = pd.DataFrame(index=extents.index)
    global_frame["extent"] = extents.sum(axis=1, min_count=2)
    global_frame["extent_km2"] = global_frame["extent"] * 1e6
    global_frame["source"] = "SUM_OF_BOTH"
    for flag in ("provider_interpolated", "provider_extrapolated", "provisional"):
        global_frame[flag] = pd.concat([f[flag] for f in frames.values()], axis=1).astype("boolean").fillna(False).any(axis=1)
    global_frame["hemisphere"] = "global"
    frames["global"] = global_frame
    return frames


def calendar_climatology(frame, baseline=(1991, 2020)):
    """Group by MM-DD, including a separate February 29 sample (no day drift)."""
    ref = frame.loc[frame.index.year.to_series(index=frame.index).between(*baseline), "extent"]
    grouped = ref.groupby(ref.index.strftime("%m-%d"))
    result = grouped.agg(mean="mean", std="std", count="count", minimum="min", maximum="max")
    result["q10"] = grouped.quantile(0.10)
    result["q90"] = grouped.quantile(0.90)
    return result


def with_anomalies(frame, climatology):
    result = frame.copy()
    keys = pd.Series(result.index.strftime("%m-%d"), index=result.index)
    for col in ("mean", "std", "q10", "q90", "count"):
        result[f"reference_{col}"] = keys.map(climatology[col])
    result["anomaly"] = result["extent"] - result["reference_mean"]
    result["anomaly_percent"] = 100 * result["anomaly"] / result["reference_mean"]
    return result


def aggregate_periods(frame, frequency):
    """Strict period means: every calendar day must have a valid observation.

    Partial first/last periods and periods with a single missing day have NaN
    eligible means. A provisional measurement is valid but is flagged separately.
    """
    if frequency not in ("ME", "YE"):
        raise ValueError("Use calendar month-end ME or calendar year-end YE")
    groups = frame.resample(frequency)
    out = groups["extent"].agg(observed_mean="mean", valid_days="count", min="min", max="max")
    out["expected_days"] = (
        out.index.days_in_month if frequency == "ME"
        else np.where(out.index.is_leap_year, 366, 365)
    )
    out["coverage"] = out["valid_days"] / out["expected_days"]
    out["complete"] = out["valid_days"].eq(out["expected_days"])
    out["mean"] = out["observed_mean"].where(out["complete"])
    out["provisional_days"] = groups["provisional"].sum().astype(int)
    out["provider_interpolated_days"] = groups["provider_interpolated"].sum().astype(int)
    out["provider_extrapolated_days"] = groups["provider_extrapolated"].sum().astype(int)
    return out


def gap_runs(frame):
    missing = frame["extent"].isna()
    groups = missing.ne(missing.shift()).cumsum()
    return pd.DataFrame([
        {"start": g.index.min(), "end": g.index.max(), "days": len(g)}
        for _, g in frame[missing].groupby(groups[missing])
    ], columns=["start", "end", "days"])


def matched_ytd(frame, as_of, first_year=1979):
    """Same MM-DD window in each year; omit Feb 29 in every year for equality."""
    end = pd.Timestamp(as_of)
    keys = frame.index.strftime("%m-%d")
    mask = (keys <= end.strftime("%m-%d")) & (keys != "02-29")
    subset = frame.loc[mask & (frame.index.year >= first_year) & (frame.index.year <= end.year)]
    window = pd.date_range("2000-01-01", f"2000-{end:%m-%d}")
    required = int((window.strftime("%m-%d") != "02-29").sum())
    out = subset.groupby(subset.index.year)["extent"].agg(mean="mean", valid_days="count")
    out["mean"] = out["mean"].where(out["valid_days"].eq(required))
    out["expected_days"] = required
    return out


def seasonal_extrema(frame, hemisphere, last_year):
    """Window-limited daily extrema, requiring complete windows, ties use first date.

    These are intentionally called seasonal extrema: they need not equal extrema
    over a complete calendar year. Five-day smoothing is a sensitivity diagnostic.
    """
    windows = {
        "nh": {"minimum": (8, 10), "maximum": (2, 4)},
        "sh": {"minimum": (1, 3), "maximum": (8, 10)},
    }[hemisphere]
    smoothed = frame["extent"].rolling(5, center=True, min_periods=5).mean()
    rows = []
    for year in range(1979, last_year + 1):
        for event, (first, last) in windows.items():
            start = pd.Timestamp(year, first, 1)
            stop = pd.Timestamp(year, last, 1) + pd.offsets.MonthEnd(0)
            idx = pd.date_range(start, stop, freq="D")
            values = frame["extent"].reindex(idx)
            valid = values.notna().all()
            smooth = smoothed.reindex(idx)
            smooth_valid = valid and smooth.notna().all()
            chooser = "idxmin" if event == "minimum" else "idxmax"
            event_date = getattr(values, chooser)() if valid else pd.NaT
            smooth_date = getattr(smooth, chooser)() if smooth_valid else pd.NaT
            rows.append({
                "year": year, "event": event,
                "window": f"{start:%b}–{stop:%b}", "complete": valid,
                "date": event_date, "extent": values.loc[event_date] if valid else np.nan,
                "smooth_date": smooth_date,
                "smooth_extent": smooth.loc[smooth_date] if smooth_valid else np.nan,
                "provisional_days": int(frame["provisional"].reindex(idx).astype("boolean").fillna(False).sum()),
            })
    return pd.DataFrame(rows)


def linear_trend(series, maxlags=3, alpha=0.05):
    """OLS slope with calendar-year-aware Bartlett/Newey–West covariance.

    Input index is integer years. Missing years are zero-score calendar slots,
    so a 1985/1987 pair never becomes a lag-one pair. Small-sample covariance
    correction n/(n-2), approximate Student-t interval with n-2 df. As in ordinary
    HAC, this assumes sufficiently weak residual dependence; it does not repair
    a nonlinear trend, sensor bias, or missing-not-at-random sampling.
    """
    if maxlags < 0 or int(maxlags) != maxlags:
        raise ValueError("maxlags must be a non-negative integer")
    clean = series.dropna().sort_index()
    years = np.asarray(clean.index, dtype=float)
    y = clean.to_numpy(dtype=float)
    if len(y) < 8 or not np.isfinite(y).all():
        raise ValueError("At least eight finite annual observations are required")
    if len(np.unique(years)) != len(years) or not np.equal(years, years.astype(int)).all():
        raise ValueError("Trend index must contain unique integer calendar years")
    center = years.mean()
    X = np.column_stack([np.ones(len(y)), years - center])
    bread = np.linalg.inv(X.T @ X)
    beta = bread @ X.T @ y
    residuals = y - X @ beta
    grid = np.arange(int(years.min()), int(years.max()) + 1)
    scores = np.zeros((len(grid), 2))
    scores[(years - grid[0]).astype(int)] = X * residuals[:, None]
    meat = scores.T @ scores
    for lag in range(1, min(maxlags, len(grid) - 1) + 1):
        cross = scores[lag:].T @ scores[:-lag]
        meat += (1 - lag / (maxlags + 1)) * (cross + cross.T)
    covariance = bread @ meat @ bread * len(y) / (len(y) - 2)
    slope_se = np.sqrt(max(covariance[1, 1], 0))
    critical = stats.t.ppf(1 - alpha / 2, len(y) - 2)
    pvalue = 2 * stats.t.sf(abs(beta[1] / slope_se), len(y) - 2) if slope_se > 0 else np.nan
    ts_slope = stats.theilslopes(y, years).slope
    return {
        "n": len(y), "first_year": int(years.min()), "last_year": int(years.max()),
        "slope_decade": beta[1] * 10, "ci_low": (beta[1] - critical * slope_se) * 10,
        "ci_high": (beta[1] + critical * slope_se) * 10,
        "pvalue": pvalue, "hac_lags": maxlags, "theil_sen_decade": ts_slope * 10,
        "intercept_at_center": beta[0], "center_year": center,
        "residuals": pd.Series(residuals, index=clean.index), "covariance": covariance,
    }


def trend_record(result):
    return {k: v for k, v in result.items() if k not in ("residuals", "covariance")}


def circular_block_bootstrap(series, block_length=5, draws=4000, seed=20261111):
    """Conditional residual bootstrap for a contiguous annual series.

    Resample centered OLS residuals in circular blocks at fixed observation times.
    Percentile intervals are conditional on a linear trend and stationary residuals;
    they exclude observational/product uncertainty and are a sensitivity check.
    """
    clean = series.dropna().sort_index()
    years = np.asarray(clean.index, dtype=float)
    y = clean.to_numpy(dtype=float)
    if len(y) < 12 or not np.all(np.diff(years) == 1):
        raise ValueError("Bootstrap requires at least 12 contiguous annual observations")
    if not 1 <= block_length < len(y) or draws < 100:
        raise ValueError("Invalid bootstrap block length or number of draws")
    x = years - years.mean()
    slope = x @ y / (x @ x)
    residuals = y - (y.mean() + slope * x)
    residuals -= residuals.mean()
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(y), size=(draws, int(np.ceil(len(y) / block_length))))
    indices = (starts[..., None] + np.arange(block_length)) % len(y)
    sampled = residuals[indices.reshape(draws, -1)[:, :len(y)]]
    return (slope + sampled @ x / (x @ x)) * 10
