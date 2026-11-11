# Sea Ice Extent Data Analysis

This project provides a Jupyter notebook for analyzing daily sea ice extent data for the Southern and Northern Hemispheres. It includes data download, cleaning (handling missing values and -999 codes), interpolation, and visualization of trends and key statistics.

## Last twenty years

The additional **[sea_ice_last_20_years.ipynb](sea_ice_last_20_years.ipynb)**
focuses on **2007–2026**, including available 2026 observations through
**10 November 2026**. A [saved HTML report](sea_ice_last_20_years.html) is also
available. The primary yearly comparison uses **January 1–November 10 in every
year**, omitting February 29, so the partial current year participates with equal
seasonal coverage. The fixed 1991–2020 reference remains unchanged.

Completed 2026 months and seasonal windows enter their corresponding fits;
unfinished months stay missing. Monthly fits report their actual sample size
(currently 20 for January–October, 19 for November–December). Recent provisional
values are included and flagged, with a nominal-only sensitivity check. Full-year
means remain a separate supporting statistic: unfinished 2026 has no full-year
mean. The window advances with the latest observed year, dropping its oldest year.

The supplement includes matched-year-to-date and monthly trends, fixed-decade comparisons,
anomaly histories, seasonal extrema, global contributions, residual diagnostics,
block-bootstrap uncertainty, and leave-one-year-out and sensor-transition checks.
Figures, tables, and provenance are exported separately to
`artifacts/sea_ice_last_20_years/`. Conditional statistical intervals exclude the
full measurement/calibration uncertainty budget; twenty-year rates are sensitive
to the selected interval and are not forecasts.

```bash
python -m nbconvert --to notebook --execute --inplace sea_ice_last_20_years.ipynb --ExecutePreprocessor.timeout=240
python -m nbconvert --to html sea_ice_last_20_years.ipynb
```

## Scientific monitoring notebook

Open **[sea_ice_monitoring.ipynb](sea_ice_monitoring.ipynb)** for the new, thorough
monitoring analysis. Its saved outputs include:

- Data-quality and source-flag audits, missing intervals, and provisional status.
- Same-calendar-day and matched-year-to-date comparisons against 1991–2020.
- Seasonal curves, monthly anomaly histories and heatmaps, and a global sum.
- Complete-year and monthly trends with serial-correlation-aware uncertainty.
- Seasonal extrema and dates, estimator/start-date/bandwidth sensitivity, and
  reproducible block-bootstrap checks.
- Generated findings, CSV tables, PNG/PDF figures, and an input-hash manifest in
  `artifacts/sea_ice_monitoring/`.

The notebook reads the local data without downloading or modifying it. Missing
values stay missing; complete-month/year rules exclude unequal observation
windows. Its annual means weight days equally, which differs from the provider's
equal-month annual convention. Statistical intervals describe conditional
regression uncertainty, not a complete observational error budget.

To refresh and execute it from the project directory:

```bash
python update_data.py
python -m nbconvert --to notebook --execute --inplace sea_ice_monitoring.ipynb --ExecutePreprocessor.timeout=240
```

This overwrites the notebook's outputs and its export bundle. Preserve a copy if
you need a permanent historical release. For an HTML report, run:

```bash
python -m nbconvert --to html sea_ice_monitoring.ipynb
```

The numerical methods are in [sea_ice_monitoring.py](sea_ice_monitoring.py).
Run their tests with `python -m unittest discover -s tests -v`. Primary-source
documentation and methodological caveats are collected in
[docs/sea_ice_methods_sources.md](docs/sea_ice_methods_sources.md).
An independent check against OSI SAF's published monthly files validated 569
complete months per hemisphere (maximum difference below 1 km² from text
rounding). Its cached audit is bound to the exact daily input hashes and is
not reused for changed data.

## Features
- Download latest sea ice extent data from OSI SAF over HTTPS
- Clean and interpolate missing data
- Visualize July 1st values, annual minimums, and trends
- Compare Southern and Northern Hemisphere time series

## Usage
1. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```
2. Update both local data files from the project directory:
   ```bash
   python update_data.py
   ```
   The updater uses only the Python standard library. It downloads and validates
   both complete series before replacing the existing files, retains the filenames
   expected by the notebook, and reports the available date range. Download or
   validation failures leave the existing files intact.
3. Open `sea_ice_extent_analysis.ipynb` in Jupyter or VS Code and run all cells.
   Its download cell runs the same updater. Skip that cell for offline analysis.
   Saved chart outputs describe the previous run until you rerun the analysis.

## Updating the data

The original `ftp://osisaf.met.no/prod_test/ice/index/v2p2/` links are obsolete.
OSI SAF v3.0 (OSI-420-a) became operational on 4 May 2026. The current daily
**extent** files are:

- [Northern Hemisphere](https://osisaf-hl.met.no/archive/osisaf/sea-ice-index/v3p0/timeseries/nh/ice_extent_nh_sii-v3p0_daily.txt)
- [Southern Hemisphere](https://osisaf-hl.met.no/archive/osisaf/sea-ice-index/v3p0/timeseries/sh/ice_extent_sh_sii-v3p0_daily.txt)

Both retain the six whitespace-separated columns used here: fractional year,
year, month, day, extent in **km²**, and source. `-999` denotes missing data and
is handled by the notebook. Fetch the entire series each time; do not append new
rows to the old v2.2 data, because product revisions can change historical values.
Source identifiers also differ between versions.

Verified on 11 November 2026: both files contain 17,549 daily rows, from
25 October 1978 through 10 November 2026. The local data files were refreshed
with this release. The dated `sea_ice_extent_analysis-25-09.ipynb` snapshot has
been preserved; rerun the main notebook to refresh its chart outputs.

## Data Sources
- [OSI SAF v3.0 product details and documentation](https://osi-saf.eumetsat.int/products/osi-420-a)
- [HTTPS data archive](https://osisaf-hl.met.no/archive/osisaf/sea-ice-index/v3p0/)
- Data attribution: EUMETSAT OSI SAF, Sea-Ice Index (2026), OSI-420-a,
  [doi:10.15770/EUM_SAF_OSI_0026](https://doi.org/10.15770/EUM_SAF_OSI_0026), CC BY 4.0.

## Requirements
- pandas
- matplotlib
- statsmodels
- numpy

## License
MIT
