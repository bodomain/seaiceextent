"""Download the complete OSI SAF v3.0 daily extent series for both hemispheres."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen


BASE_URL = "https://osisaf-hl.met.no/archive/osisaf/sea-ice-index/v3p0/timeseries"


def validate_data(data, hemisphere):
    """Reject error pages, unexpected formats, and incomplete or unordered series."""
    text = data.decode("utf-8")
    area = {"nh": "Northern Hemisphere", "sh": "Southern Hemisphere"}[hemisphere]
    if (
        f"# Area: {area}" not in text
        or "# Product: EUMETSAT OSI SAF Sea Ice Index v3.0" not in text
        or not text.startswith("# Format: FracYear YYYY MM DD SIE_mean[km^2] SIE_source")
    ):
        raise ValueError(f"Unexpected OSI SAF data header for {hemisphere}")

    dates = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) != 6:
            raise ValueError(f"Expected six columns for {hemisphere}: {line!r}")
        float(fields[0])
        day = date(*map(int, fields[1:4]))
        extent = float(fields[4])
        if not (0 <= extent <= 40_000_000 or extent == -999):
            raise ValueError(f"Invalid extent for {hemisphere} on {day}: {extent}")
        if dates and day <= dates[-1]:
            raise ValueError(f"Unordered or duplicate date for {hemisphere}: {day}")
        dates.append(day)

    if not dates or dates[0] != date(1978, 10, 25):
        raise ValueError(f"Expected the complete series from 1978-10-25 for {hemisphere}")
    return dates


def update_data(directory=None):
    directory = Path(directory) if directory is not None else Path(__file__).resolve().parent
    # Stage both downloads before replacing anything. Failed downloads or validation
    # leave the existing data intact; each replacement uses a same-filesystem rename.
    with TemporaryDirectory(prefix=".seaice-update-", dir=directory) as staging:
        downloads = []
        for hemisphere in ("nh", "sh"):
            url = f"{BASE_URL}/{hemisphere}/ice_extent_{hemisphere}_sii-v3p0_daily.txt"
            with urlopen(url, timeout=60) as response:
                data = response.read()
            dates = validate_data(data, hemisphere)
            destination = directory / f"osisaf_{hemisphere}_sie_daily.txt"
            if destination.exists():
                existing_dates = validate_existing_dates(destination)
                if existing_dates and dates[-1] < existing_dates[-1]:
                    raise ValueError(f"Download would shorten the existing series: {destination.name}")
            staged = Path(staging) / destination.name
            staged.write_bytes(data)
            downloads.append((staged, destination, dates))

        for staged, destination, dates in downloads:
            staged.replace(destination)
            print(f"Updated {destination.name}: {len(dates):,} rows, {dates[0]} through {dates[-1]}")


def validate_existing_dates(path):
    # Both the original v2.2 files and v3.0 files have these date columns.
    return [
        date(*map(int, line.split()[1:4]))
        for line in path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


if __name__ == "__main__":
    update_data()
