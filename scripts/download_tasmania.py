"""Download daily maximum temperature for Tasmania from NCI's public THREDDS server.

Fetches, for a box around Tasmania only (cut on the server via OPeNDAP):

* BARPA-R driven by ERA5 (evaluation run), 1985-2014
* BARPA-R driven by CESM2 r11i1p1f1: historical 1970-2014, SSP1-2.6 and SSP3-7.0 2015-2100
* BARPA-R land fraction and surface height
* AGCD v1.0.3 gridded observations, 1985-2014

No NCI account is needed. Years are cached in data/raw/tasmania/_parts, so an
interrupted run resumes where it stopped. Takes roughly 15 minutes.

Usage:  python scripts/download_tasmania.py
"""

import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import xarray as xr

THREDDS = "https://thredds.nci.org.au/thredds/dodsC"
BOX = {"lat": slice(-44.0, -39.5), "lon": slice(143.5, 149.0)}
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "tasmania"
PART_DIR = OUT_DIR / "_parts"
WORKERS = 4  # be polite to a shared public server

BARPA_ROOT = f"{THREDDS}/py18/BARPA/output-CMIP6/DD/AUS-15/BOM"
BARPA_RUNS = {
    # name: (driving model, experiment, member, data version, first year, last year)
    "era5_evaluation": ("ERA5", "evaluation", "r1i1p1f1", "v20240801", 1985, 2014),
    "cesm2_historical": ("CESM2", "historical", "r11i1p1f1", "v20231001", 1970, 2014),
    "cesm2_ssp126": ("CESM2", "ssp126", "r11i1p1f1", "v20231001", 2015, 2100),
    "cesm2_ssp370": ("CESM2", "ssp370", "r11i1p1f1", "v20231001", 2015, 2100),
}
AGCD_URL = f"{THREDDS}/zv2/agcd/v1-0-3/tmax/mean/r005/01day/agcd_v1_tmax_mean_r005_daily_{{year}}.nc"
AGCD_YEARS = (1985, 2014)


def barpa_url(gcm, experiment, member, version, freq, variable, suffix):
    stem = f"{variable}_AUS-15_{gcm}_{experiment}_{member}_BOM_BARPA-R_v1-r1_{freq}{suffix}"
    return f"{BARPA_ROOT}/{gcm}/{experiment}/{member}/BARPA-R/v1-r1/{freq}/{variable}/{version}/{stem}.nc"


def fetch(url, variable, target, retries=3):
    """Download one subset to `target`, keeping only the variable and its grid."""
    if target.exists():
        return target
    for attempt in range(1, retries + 1):
        try:
            with xr.open_dataset(url) as ds:
                da = ds[variable].sel(**BOX)
                # Known BARPA issue: files differ in extra metadata variables
                # (e.g. crs, height), so keep only the core coordinates.
                da = da.drop_vars([c for c in da.coords if c not in da.dims])
                subset = da.to_dataset()
                subset.attrs = {"source_url": url, **{k: v for k, v in ds.attrs.items() if isinstance(v, str)}}
                tmp = target.with_suffix(".tmp")
                subset.load().to_netcdf(tmp, encoding={variable: {"zlib": True, "complevel": 4}})
                tmp.rename(target)
                return target
        except Exception as err:  # network hiccups are common on long runs
            if attempt == retries:
                raise RuntimeError(f"Failed after {retries} attempts: {url}") from err
            time.sleep(10 * attempt)


def merge(parts, variable, target):
    combined = xr.open_mfdataset(sorted(parts), combine="by_coords", data_vars="minimal", coords="minimal")
    combined.attrs.pop("source_url", None)
    combined.to_netcdf(target, encoding={variable: {"zlib": True, "complevel": 4}})
    combined.close()


def main():
    PART_DIR.mkdir(parents=True, exist_ok=True)
    jobs = {}  # output file -> (variable, [(url, part path)])

    for name, (gcm, experiment, member, version, first, last) in BARPA_RUNS.items():
        target = OUT_DIR / f"barpa_{name}_tasmax_{first}-{last}.nc"
        parts = [
            (barpa_url(gcm, experiment, member, version, "day", "tasmax", f"_{year}01-{year}12"),
             PART_DIR / f"barpa_{name}_tasmax_{year}.nc")
            for year in range(first, last + 1)
        ]
        jobs[target] = ("tasmax", parts)

    for variable in ("sftlf", "orog"):
        url = barpa_url("CESM2", "historical", "r11i1p1f1", "v20231001", "fx", variable, "")
        jobs[OUT_DIR / f"barpa_{variable}.nc"] = (variable, [(url, PART_DIR / f"barpa_{variable}.nc")])

    first, last = AGCD_YEARS
    jobs[OUT_DIR / f"agcd_tmax_{first}-{last}.nc"] = (
        "tmax",
        [(AGCD_URL.format(year=year), PART_DIR / f"agcd_tmax_{year}.nc") for year in range(first, last + 1)],
    )

    pending = [(url, variable, part) for target, (variable, parts) in jobs.items()
               if not target.exists() for url, part in parts]
    print(f"{len(pending)} subsets to fetch ({sum(p.exists() for _, _, p in pending)} already cached)")

    # Separate processes, not threads: the netCDF C library is not thread-safe.
    with ProcessPoolExecutor(WORKERS) as pool:
        futures = {pool.submit(fetch, url, variable, part): part for url, variable, part in pending}
        for done, future in enumerate(as_completed(futures), start=1):
            future.result()
            if done % 20 == 0 or done == len(futures):
                print(f"  {done}/{len(futures)} fetched", flush=True)

    for target, (variable, parts) in jobs.items():
        if not target.exists():
            merge([part for _, part in parts], variable, target)
            print(f"wrote {target.relative_to(OUT_DIR.parent.parent.parent)}")
    print("Done. Year files in data/raw/tasmania/_parts can be deleted.")


if __name__ == "__main__":
    main()
