"""Helpers for screening heat hazard in CMIP6 daily temperature data."""

from .data import load_daily_tas
from .extremes import (
    bootstrap_return_level,
    fit_gev,
    gev_parameters,
    return_level,
    return_level_field,
    return_period,
    return_period_field,
)
from .metrics import annual_exceedance_days, annual_maximum, period_mean
from .spatial import area_weights, block_mean, cell_edges, land_mask, nearest_land_cell, regional_mean

__all__ = [
    "load_daily_tas",
    "fit_gev",
    "gev_parameters",
    "return_level",
    "return_period",
    "return_level_field",
    "return_period_field",
    "bootstrap_return_level",
    "annual_exceedance_days",
    "annual_maximum",
    "period_mean",
    "area_weights",
    "block_mean",
    "cell_edges",
    "land_mask",
    "nearest_land_cell",
    "regional_mean",
]
