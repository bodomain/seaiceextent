# Scientific methods and primary sources for sea-ice monitoring

Verified 11 November 2026. The sources below are first-party documentation, official service announcements, and original methodological work. PDF page numbers are printed page numbers, starting with the cover as page 1. The local text files are a dated snapshot; upstream historical and provisional values can change.

## Dataset identity and definitions

Use the complete EUMETSAT OSI SAF **Sea-Ice Index v3.0, OSI-420-a**, operational since 4 May 2026, produced by MET Norway, beginning 25 October 1978. Cite **EUMETSAT OSI SAF, Sea-Ice Index (2026), OSI-420-a, doi:10.15770/EUM_SAF_OSI_0026**; attribution is required under CC BY 4.0. [Official product page](https://osi-saf.eumetsat.int/products/osi-420-a), [DOI](https://doi.org/10.15770/EUM_SAF_OSI_0026).

The three current product documents linked by that product page are:

- [Product User Manual, document version 2.1, 9 April 2026](https://osisaf-hl.met.no/sites/osisaf-hl/files/user_manuals/osisaf_pum_sea-ice-index_2.1.pdf) (PUM).
- [Algorithm Theoretical Basis Document, document version 1.2, 8 April 2026](https://osisaf-hl.met.no/sites/osisaf-hl/files/baseline_document/osisaf_atbd_sea-ice-index_1.2.pdf) (ATBD).
- [Scientific Validation Report, document version 1.0, 30 April 2026](https://osisaf-hl.met.no/sites/osisaf-hl/files/validation_reports/osisaf_svr_sea-ice-index_1.0.pdf) (SVR).

PUM §6.2.2, p.26 defines extent as the summed area of ocean grid cells with **sea-ice concentration ≥15%**; sea-ice area instead weights grid-cell area by fractional concentration. Use the precise ≥ definition from the equations rather than the looser “exceeds 15%” wording in product overviews. PUM §8.3.1, p.41 specifies **km² in plain-text files**, six whitespace-separated columns, `#` metadata lines, and **−999 as missing**. NetCDF index values instead use million km² (§6.2.2); always inspect units when changing file formats. Decimal output precision is not physical measurement accuracy.

The current source files are [Northern Hemisphere daily extent](https://osisaf-hl.met.no/archive/osisaf/sea-ice-index/v3p0/timeseries/nh/ice_extent_nh_sii-v3p0_daily.txt) and [Southern Hemisphere daily extent](https://osisaf-hl.met.no/archive/osisaf/sea-ice-index/v3p0/timeseries/sh/ice_extent_sh_sii-v3p0_daily.txt). Their headers identify v3.0 and km², but still mention older document versions and the earlier product-page URL. Prefer the current official documents above for interpretation.

Extent quantifies surface coverage. It does not measure thickness, ice volume, or land-ice mass. Deriving volume requires thickness information absent from these files. NSIDC separately describes extent, concentration, area, and thickness measurement in its [Science of Sea Ice, “Data terminology” and “Satellite remote sensing” sections](https://nsidc.org/learn/parts-cryosphere/sea-ice/science-sea-ice). A rise in daily extent alone therefore does not establish a rise in volume.

## Provenance, interpolation, missingness, and recent revisions

PUM §6.2.2, pp.27–28, Table 5 documents source labels and interpolation/extrapolation suffixes. Preserve the original flag as a provenance field:

| Observed/documented label | Interpretation |
| --- | --- |
| `OSI450A1` | Historical concentration CDR OSI-450-a1; SMMR, SSM/I, SSMIS |
| `OSI430A` | SSMIS interim concentration CDR OSI-430-a |
| `OSI438` | Nominal AMSR2 interim concentration CDR OSI-438 |
| `OSI438FT` | AMSR2 fast-track label documented in the April 2026 PUM |
| `OSI438AFT` | Label present in the November 2026 snapshot; inferred to denote AMSR3 OSI-438-a fast-track from the September 2026 service change below |
| `_interp` / `_extrap` | Provider-interpolated / provider-extrapolated daily estimate |
| `MISSING` with `-999` | Missing extent; mask before any aggregation, rank, extrema, or regression |

Do not interpret every row as a direct, independent satellite observation. PUM §7.3, p.36 explains that SMMR observations were generally every second day and the provider filled short gaps, smoothing the series. Do not add unrestricted interpolation across the remaining long gaps.

The official missing daily intervals are **12–24 August 1984; 1 April–23 June 1986; 3–15 January 1987; and 3 December 1987–12 January 1988**, totaling 151 days. The missing monthly indices are April, May, June 1986 and December 1987. [PUM Appendix A, p.51](https://osisaf-hl.met.no/sites/osisaf-hl/files/user_manuals/osisaf_pum_sea-ice-index_2.1.pdf#page=51), [ATBD Appendix A, p.31](https://osisaf-hl.met.no/sites/osisaf-hl/files/baseline_document/osisaf_atbd_sea-ice-index_1.2.pdf#page=31). These dates agree with the 151 `MISSING` rows in each local snapshot. The 1987–1988 break is only one of the gaps.

ATBD §§4.1–4.3, pp.16–20: provider interpolation fills ≤7 consecutive missing days; latest fast-track days are not gap-filled. Monthly means average daily indices; provider yearly means average 12 monthly means and interpolate missing monthly values first. **Notebook policy:** disclose any departure. Requiring complete calendar months/years and omitting incomplete periods is a conservative alternative to the provider's yearly interpolation. Calendar-month means computed from these complete months agree in definition; an annual mean weighted equally by days differs from the provider's equal-month annual mean.

## Satellite transitions and comparability

The **v3.0 transition to calibrated AMSR2 begins 1 January 2025**. It also uses calibrated AMSR2 to fill a September 2024 SSMIS gap. ATBD §§2.4.1 and 4.1.2, pp.12,17–18 describes region/hemisphere-specific cubic-spline calibration over the January 2021–June 2025 overlap. Calibration addresses sensor-dependent offsets but does not make instrument differences vanish. PUM §§7.1 and 7.4, pp.36–37 warns of residual differences, especially coastal land spillover, when comparing pre-2025 and later values.

Do not confuse v3.0 with the earlier v2.3 transition on **1 August 2025**, described in the [official v2.3 release announcement, 2 September 2025](https://osi-saf.eumetsat.int/community/list-of-service-messages/release-sea-ice-index-product-version-v23). Download the whole v3.0 record; appending new v3.0 observations to old-version histories creates a mixed product.

A further operational change matters at this retrieval date. The [official AMSR3 service message #3571, 31 August 2026](https://osi-saf.eumetsat.int/community/list-of-service-messages/operational-release-amsr3-based-sea-ice-products-1st-september) states that from **1 September 2026**, the latest approximately 16 days of this index use **AMSR3 OSI-438-a fast-track**, while older nominal days continue using **AMSR2 OSI-438**. This supersedes the April PUM's description of fast-track input. Accept the actual `OSI438AFT` flag rather than a fixed list that recognizes only `OSI438FT`.

The index updates daily with about one-day latency. Recent fast-track estimates are **provisional** and replaced by nominal values after roughly 16 days; a completed month is first released on day 1 and finalized on day 16 of the next month. [ATBD executive summary, pp.10–11, and §4.2, p.20](https://osisaf-hl.met.no/sites/osisaf-hl/files/baseline_document/osisaf_atbd_sea-ice-index_1.2.pdf). Use flags to identify actual provisional records; documentary wording alternates between 15 and 16 days. As of 11 November, October 2026 is complete in calendar coverage but still contains provisional inputs. Flag it in monitoring summaries or exclude it from nominal-only trend fits. These are distinct decisions from excluding partial November.

SVR §5, pp.22–31 compares OSI SAF with NSIDC; §7, pp.36–48 assesses AMSR calibration impacts, including monthly anomalies, trends, and extrema. This supports treating the official record as a climate-monitoring product while retaining transition caveats. It does not justify merging index products. Different masks, algorithms, and pole-hole treatments create systematic differences; PUM §7.5, pp.37–38 explicitly cautions about external comparisons. Nor is this validation evidence of an exact uncertainty bound for an individual day.

## Climatology, seasonal comparisons, and records

Use and label a fixed **1991–2020 reference climatology**. WMO defines standard normals as overlapping 30-year periods updated every decade; 1991–2020 is appropriate to current monitoring. [WMO Climatological Normals](https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/climate-services/wmo-climatological-normals). The OSI SAF product also provides 1981–2010; changing baseline changes anomalies and percentage trends, so never compare unnamed baselines.

Align daily baselines by **month and day**, not unadjusted Gregorian day-of-year, which shifts March–December across leap years. The provider uses a 366-day all-leap calendar and interpolates 29 February in non-leap years. [PUM §6.2.2, p.26](https://osisaf-hl.met.no/sites/osisaf-hl/files/user_manuals/osisaf_pum_sea-ice-index_2.1.pdf#page=26). A notebook may instead omit 29 February from daily display or calculate it from the leap-year subset, provided it documents that difference. Display the number of baseline values, particularly for leap day.

**Notebook definitions:** absolute anomaly is observed extent minus the same-calendar-day or same-month baseline mean; relative anomaly is 100 times absolute anomaly divided by that mean. Empirical percentile bands describe historical variability, not a confidence interval on a mean or a probability of an event under a stationary climate. A fixed normal is descriptive; it does not assert stationarity.

PUM §6.2.2, pp.26–27 explicitly warns that daily ranks are ordinal: tiny extent differences produce different ranks, so distinct ranks do **not** imply statistically significant differences. Report the same-calendar-day rank, eligible-year count, tie rule, and provisional status. Restrict annual extrema to complete years, label the current year as year-to-date, and never compare its unfinished annual mean directly with full-year annual means. These completeness rules are notebook choices to prevent unequal time coverage from masquerading as a climate signal.

## Trends and uncertainty

Fit each calendar month's annual sequence separately, or use complete-year aggregates, to avoid fitting a raw daily seasonal cycle. OSI SAF uses ordinary least squares calendar-month trends (PUM §6.2.3, p.28). Report the fit period and sample size. With extent expressed in million km² and time in years, multiply slope and confidence limits by 10 for million km² per decade. Relative trend is 100 × decadal absolute slope / corresponding baseline mean.

Ordinary independent-error standard errors are unsuitable when regression residuals are serially correlated. Newey–West provides heteroskedasticity- and autocorrelation-consistent covariance under stated large-sample conditions: [Newey & West, original NBER technical paper, 1986, published in Econometrica 55 (1987), 703–708](https://www.nber.org/papers/t0055), [published-paper DOI](https://doi.org/10.2307/1913610). This is a covariance method, not a guarantee that a short climate series satisfies a linear stationary-error model.

[statsmodels OLS robust-covariance documentation](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html) documents `cov_type="HAC"`, required `maxlags`, Bartlett kernel, optional small-sample correction, and `use_t` (normal inference is the robust-covariance default). Specify all choices explicitly, including confidence level. A transparent annual-series choice is lags 3 with lags 0, 1, and 5 as sensitivity checks; that is a notebook convention, not an OSI SAF or Newey–West mandated bandwidth.

**Calendar gaps matter:** [statsmodels `cov_hac` v0.14.4 documentation](https://www.statsmodels.org/v0.14.4/generated/statsmodels.stats.sandwich_covariance.cov_hac.html) assumes consecutive equally spaced periods. Dropping a missing year compresses time for an ordinary lag-based HAC implementation even if the regression regressor retains actual year. Use a consecutive valid analysis window, a covariance implementation pairing residual score products by actual calendar lag, or explain the approximation. Do not invent values solely to satisfy a covariance API. Keep trend uncertainty and lag-sensitivity results interpretable when a historical missing month/annual exclusion produces a gap.

Finally, identify reported intervals as **regression sampling uncertainty conditional on the selected series/model**, not complete satellite measurement uncertainty. PUM §7 documents retrieval/sensor limitations; ATBD §4.6, pp.26–27 states that the product does not yet propagate full observation uncertainties into index/trend estimates. HAC intervals do not include structural sensor errors, mask uncertainty, baseline uncertainty, model misspecification, or calibration uncertainty. Trend fit sensitivity to start date and lag is useful; neither it nor daily ranks establishes attribution, a causal mechanism, a forecast, or independent daily significance. If presenting 12 monthly confidence intervals, label them pointwise rather than simultaneous and avoid selecting only apparently significant months.

## Additional checks implemented in the notebook

The notebook applies Holm adjustment to the 24 hemisphere-by-month trend p-values
as one declared family. This controls family-wise error under valid individual
tests without assuming their independence; the underlying small-sample HAC tests
remain approximate. All slopes and pointwise intervals are displayed regardless
of adjusted p-value. [statsmodels multiple-testing API](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html).

A circular residual-block bootstrap with fixed observation years provides an
uncertainty sensitivity check, with blocks of 3 and 5 years, 4,000 draws, and a
declared random seed. It requires contiguous annual observations and assumes a
linear mean plus approximately stationary dependent residuals. It cannot repair a
nonstationary residual process or propagate satellite retrieval uncertainties.
The general principle of resampling blocks for dependent stationary sequences is
established by Künsch (1989), [The Jackknife and the Bootstrap for General
Stationary Observations](https://doi.org/10.1214/aos/1176347265). The notebook's
precise circular residual algorithm and percentile interval are specified in its
code rather than claimed to reproduce every detail of that paper.

On 11 November 2026, recomputed complete-month means were checked against the
provider's separately published [Northern monthly extent](https://osisaf-hl.met.no/archive/osisaf/sea-ice-index/v3p0/timeseries/nh/ice_extent_nh_sii-v3p0_monthly.txt)
and [Southern monthly extent](https://osisaf-hl.met.no/archive/osisaf/sea-ice-index/v3p0/timeseries/sh/ice_extent_sh_sii-v3p0_monthly.txt).
All 569 eligible months per hemisphere agreed within 1 km² (maximum absolute
differences 0.5667 km² north and 0.6129 km² south). This is consistent with text
rounding, not evidence of sub-km² physical accuracy. Published monthly snapshots,
source URLs, timestamps, and hashes are retained in the export bundle; the
notebook verifies their checksums and skips this dated validation if daily input
hashes change. This checks aggregation arithmetic within the same provider's
product, not independent sensor accuracy or external product agreement.
