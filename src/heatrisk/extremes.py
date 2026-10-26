"""Generalised Extreme Value (GEV) fits for annual-maximum series.

scipy's `genextreme` uses a shape parameter c = -ξ, the opposite sign to the
usual climate-science convention: c > 0 means a bounded upper tail.
"""

import numpy as np
import xarray as xr
from scipy import stats


def fit_gev(sample):
    """Fit a stationary GEV by maximum likelihood. Returns (c, loc, scale)."""
    sample = np.asarray(sample, dtype=float)
    sample = sample[np.isfinite(sample)]
    if sample.size < 10:
        return np.nan, np.nan, np.nan
    return stats.genextreme.fit(sample)


def return_level(params, return_period_years):
    """Level exceeded with probability 1/T in any one year."""
    c, loc, scale = params
    return stats.genextreme.isf(1 / return_period_years, c, loc=loc, scale=scale)


def return_period(params, level):
    """Average years between exceedances of `level` (inf if beyond the upper bound)."""
    c, loc, scale = params
    with np.errstate(divide="ignore"):
        return 1 / stats.genextreme.sf(level, c, loc=loc, scale=scale)


def gev_parameters(annual_max):
    """Fit a GEV at every grid cell. Adds a `param` dimension (c, loc, scale)."""
    params = xr.apply_ufunc(
        lambda x: np.array(fit_gev(x)),
        annual_max,
        input_core_dims=[["time"]],
        output_core_dims=[["param"]],
        vectorize=True,
    )
    return params.assign_coords(param=["c", "loc", "scale"])


def _unpack(params):
    return [params.sel(param=name, drop=True) for name in ("c", "loc", "scale")]


def return_level_field(params, return_period_years):
    """`return_level` applied to the output of `gev_parameters`."""
    return xr.apply_ufunc(
        lambda c, loc, scale: return_level((c, loc, scale), return_period_years),
        *_unpack(params),
    )


def return_period_field(params, level):
    """`return_period` applied to the output of `gev_parameters`."""
    return xr.apply_ufunc(
        lambda c, loc, scale, lev: return_period((c, loc, scale), lev),
        *_unpack(params),
        level,
    )


def bootstrap_return_level(sample, return_period_years, n_boot=500, ci=0.90, seed=0):
    """Return level with a bootstrap confidence interval.

    Resamples years with replacement, so it captures sampling uncertainty
    only, not climate-model, scenario or structural uncertainty.
    Returns (best_estimate, lower, upper).
    """
    sample = np.asarray(sample, dtype=float)
    rng = np.random.default_rng(seed)
    best = return_level(fit_gev(sample), return_period_years)
    draws = np.array(
        [
            return_level(fit_gev(rng.choice(sample, sample.size, replace=True)), return_period_years)
            for _ in range(n_boot)
        ]
    )
    alpha = (1 - ci) / 2
    lower, upper = np.nanquantile(draws, [alpha, 1 - alpha])
    return float(best), float(lower), float(upper)
