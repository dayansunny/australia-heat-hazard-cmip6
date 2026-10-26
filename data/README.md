# Data

The climate data are **not stored in this repository** because they are too large for git. Put the two files below in `data/raw/` before running the notebooks.

## Files used by notebook 01

| File | Model | Experiment | Member | Period |
|---|---|---|---|---|
| `tas_day_CESM2_historical_r1i1p1f1_gn_19700101-20141231_subset.nc` | NCAR CESM2 | historical | r1i1p1f1 | 1970-01-01 to 2015-01-01 |
| `tas_day_CESM2_ssp370_r11i1p1f1_gn_20150101-21001231_subset.nc` | NCAR CESM2 | ssp370 | r11i1p1f1 | 2015-01-01 to 2101-01-01 |

Variable `tas` (daily mean near-surface air temperature, K) on the native 0.9° × 1.25° grid.

## How the subsets were made

The original CMIP6 decadal files were joined and clipped with [CDO](https://code.mpimet.mpg.de/projects/cdo), as recorded in each file's `history` attribute:

```bash
cdo mergetime tas_day_CESM2_historical_r1i1p1f1_gn_*.nc tas_day_CESM2_historical_r1i1p1f1_gn_19700101-20141231.nc
cdo sellonlatbox,100,160,-40,-10 tas_day_CESM2_historical_r1i1p1f1_gn_19700101-20141231.nc tas_day_CESM2_historical_r1i1p1f1_gn_19700101-20141231_subset.nc
```

and likewise for the `ssp370` files. The decadal source files are available from any [ESGF](https://esgf.llnl.gov/) data node. Search for `source_id=CESM2`, `experiment_id=historical` or `ssp370`, `table_id=day`, `variable_id=tas`, and the member listed above.

Original file handles (`tracking_id`):

* historical r1i1p1f1: `hdl:21.14100/ee4dcacc-1783-41de-96d0-88dcba6bd1e2`
* ssp370 r11i1p1f1: `hdl:21.14100/32a166f9-7b51-441a-8bc6-191c46afd3b2`

## Licence and citation

CESM2 CMIP6 output is published by NCAR under the [Creative Commons Attribution-ShareAlike 4.0 International licence](https://creativecommons.org/licenses/by-sa/4.0/). See the [CMIP6 terms of use](https://pcmdi.llnl.gov/CMIP6/TermsOfUse) for citation requirements.

* Danabasoglu, G. (2019). *NCAR CESM2 model output prepared for CMIP6 CMIP historical.* Earth System Grid Federation. https://doi.org/10.22033/ESGF/CMIP6.7627
* Danabasoglu, G. (2019). *NCAR CESM2 model output prepared for CMIP6 ScenarioMIP ssp370.* Earth System Grid Federation. https://doi.org/10.22033/ESGF/CMIP6.7753

The land mask uses [Natural Earth](https://www.naturalearthdata.com/) coastlines (public domain), which cartopy downloads automatically.

## Files used by notebook 02 (Tasmania)

Run the download script from the repository root. It cuts a box around Tasmania (39.5–44°S, 143.5–149°E) on the server, so only about 1 GB is transferred, and no account is needed:

```bash
python scripts/download_tasmania.py
```

It writes these files to `data/raw/tasmania/`:

| File | Dataset | Version | Years |
|---|---|---|---|
| `barpa_era5_evaluation_tasmax_1985-2014.nc` | BARPA-R driven by ERA5 (evaluation run) | v20240801 | 1985–2014 |
| `barpa_cesm2_historical_tasmax_1970-2014.nc` | BARPA-R driven by CESM2 r11i1p1f1, historical | v20231001 | 1970–2014 |
| `barpa_cesm2_ssp126_tasmax_2015-2100.nc` | BARPA-R driven by CESM2 r11i1p1f1, SSP1-2.6 | v20231001 | 2015–2100 |
| `barpa_cesm2_ssp370_tasmax_2015-2100.nc` | BARPA-R driven by CESM2 r11i1p1f1, SSP3-7.0 | v20231001 | 2015–2100 |
| `barpa_sftlf.nc`, `barpa_orog.nc` | BARPA-R land fraction and terrain height | v20231001 | – |
| `agcd_tmax_1985-2014.nc` | AGCD daily maximum temperature, 0.05° grid | v1.0.3 | 1985–2014 |

**Sources.** BARPA comes from NCI project `py18` (`/thredds/dodsC/py18/BARPA/output-CMIP6/DD/AUS-15/BOM/...`). AGCD comes from NCI project `zv2` (`/thredds/dodsC/zv2/agcd/v1-0-3/tmax/mean/r005/01day/`). BARPA is also mirrored in the Bureau's public AWS bucket, `s3://bom-opendata-climate/BARPA/output-CMIP6/...`, but that serves whole-of-domain files (~190 MB per year), so the script uses NCI's server-side subsetting instead.

**Known BARPA data quirks handled by the script.** Yearly files differ in extra metadata variables (e.g. `crs`, `height`), which breaks `xarray.open_mfdataset`. The script keeps only the temperature variable and its grid. See the [BARPA known issues](https://opus.nci.org.au/x/kwDADw) page.

**Time conventions.** AGCD records each day's maximum against the date on which the 24-hour period (to 9 am) began. CESM2-driven BARPA runs use a 365-day calendar; the ERA5-driven run and AGCD use the standard calendar. Neither matters for 30-year statistics.

### Licences and citations

* **BARPA**, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The data are a research product that has not been fully evaluated (the evaluation in notebook 02 is part of using them responsibly).
  * Bureau of Meteorology (2023). *Bureau of Meteorology Atmospheric Regional Projections for Australia (BARPA)*. NCI Australia. https://doi.org/10.25914/z1x6-dq28
  * Su, C.-H., Stassen, C., Howard, E., Ye, H., Bell, S. S., Pepler, A., Dowdy, A. J., Tucker, S. O., Franklin, C. (2022). *BARPA: New development of ACCESS-based regional climate modelling for Australian Climate Service.* Bureau Research Report 069.
  * Howard, E., Su, C.-H., Stassen, C., et al. (2024). Performance and process-based evaluation of the BARPA-R Australasian regional climate model version 1. *Geoscientific Model Development* 17, 731–757. https://doi.org/10.5194/gmd-17-731-2024
* **AGCD**, [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) (**non-commercial use only**).
  * Australian Bureau of Meteorology (2025). *Australian Gridded Climate Data (AGCD) / AWAP; v1.0.3 Snapshot (1900-01-01 to 2024-12-31).* Downloaded from NCI in October 2026. https://doi.org/10.25914/mc6x-mt32
