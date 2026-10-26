"""Load CMIP6 daily temperature files and join historical + scenario runs."""

import warnings

import xarray as xr

KELVIN_OFFSET = 273.15


def load_daily_tas(
    historical_path,
    scenario_path,
    historical_end="2014-12-31",
    scenario_start="2015-01-01",
    scenario_end="2100-12-31",
):
    """Return one continuous daily `tas` series in °C.

    Each run is trimmed to its own years before joining, because CMIP6 files
    often share a boundary day (e.g. both contain 2015-01-01) or run one day
    past the final year. A warning is raised if the scenario run does not
    branch from the historical member supplied, since the joined series then
    splices two different simulated climates together.
    """
    historical = xr.open_dataset(historical_path)
    scenario = xr.open_dataset(scenario_path)

    for ds in (historical, scenario):
        units = ds["tas"].attrs.get("units")
        if units != "K":
            raise ValueError(f"Expected tas in K, found {units!r}")

    hist_member = historical.attrs.get("variant_label")
    scen_member = scenario.attrs.get("variant_label")
    parent_member = scenario.attrs.get("parent_variant_label")
    if parent_member and parent_member != hist_member:
        warnings.warn(
            f"Scenario member {scen_member} branches from historical {parent_member}, "
            f"but the historical file is {hist_member}: the joined series splices two "
            f"different realisations at {scenario_start}.",
            stacklevel=2,
        )

    tas = xr.concat(
        [
            historical["tas"].sel(time=slice(None, historical_end)),
            scenario["tas"].sel(time=slice(scenario_start, scenario_end)),
        ],
        dim="time",
    )
    tas = tas - KELVIN_OFFSET
    tas.attrs = {
        "units": "°C",
        "long_name": "Daily mean near-surface air temperature",
        "source_id": historical.attrs.get("source_id"),
        "historical_member": hist_member,
        "scenario": scenario.attrs.get("experiment_id"),
        "scenario_member": scen_member,
    }
    return tas
