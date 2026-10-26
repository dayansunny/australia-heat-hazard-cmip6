"""Period means, threshold exceedances and annual maxima."""


def period_mean(da, period):
    """Time mean over an inclusive (start_year, end_year) window."""
    start, end = period
    return da.sel(time=slice(str(start), str(end))).mean("time")


def annual_exceedance_days(tas, threshold):
    """Days per calendar year on which `tas` is above `threshold`.

    `threshold` can be a scalar or a field (e.g. a per-cell percentile).
    Cells that are NaN in `tas` count as zero, so mask the result if needed.
    """
    return (tas > threshold).resample(time="YS").sum("time")


def annual_maximum(da):
    """Highest daily value in each calendar year."""
    return da.resample(time="YS").max("time")
