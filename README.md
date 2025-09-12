# Sea Ice Extent Data Analysis

This project provides a Jupyter notebook for analyzing daily sea ice extent data for the Southern and Northern Hemispheres. It includes data download, cleaning (handling missing values and -999 codes), interpolation, and visualization of trends and key statistics.

## Features
- Download latest sea ice extent data from OSISAF FTP
- Clean and interpolate missing data
- Visualize July 1st values, annual minimums, and trends
- Compare Southern and Northern Hemisphere time series

## Usage
1. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```
2. Open `sea_ice_extent_analysis.ipynb` in Jupyter or VS Code.
3. Run the notebook cells to download, clean, and analyze the data.

## Data Sources
- [OSISAF FTP](ftp://osisaf.met.no/prod_test/ice/index/v2p2/)

## Requirements
- pandas
- matplotlib
- statsmodels
- numpy

## License
MIT
