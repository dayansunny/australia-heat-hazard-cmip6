"""Land masking and area-weighted averaging on a regular lat-lon grid."""

import cartopy.io.shapereader as shpreader
import numpy as np
import shapely
import xarray as xr


def land_mask(lat, lon, resolution="50m"):
    """True where a grid-cell centre lies on land (Natural Earth coastline).

    A centre-point test is coarse at ~1° resolution: coastal cells that are
    partly land may be classed as ocean and vice versa.
    """
    lon2d, lat2d = np.meshgrid(np.asarray(lon), np.asarray(lat))
    lon_wrapped = (lon2d + 180) % 360 - 180

    path = shpreader.natural_earth(resolution=resolution, category="physical", name="land")
    bbox = shapely.box(lon_wrapped.min() - 1, lat2d.min() - 1, lon_wrapped.max() + 1, lat2d.max() + 1)
    land = shapely.union_all(
        [geom.intersection(bbox) for geom in shpreader.Reader(path).geometries() if geom.intersects(bbox)]
    )
    shapely.prepare(land)

    return xr.DataArray(
        shapely.contains_xy(land, lon_wrapped, lat2d),
        coords={"lat": lat, "lon": lon},
        dims=("lat", "lon"),
        name="land",
    )


def area_weights(lat):
    """Relative grid-cell area on a regular lat-lon grid (proportional to cos(lat))."""
    return np.cos(np.deg2rad(lat))


def regional_mean(da, mask):
    """Area-weighted mean over the cells where `mask` is True."""
    weights = (area_weights(da.lat) * mask).fillna(0)
    return da.weighted(weights).mean(("lat", "lon"))


def cell_edges(centres):
    """Edges of grid cells from their centres (midpoints, extrapolated at the ends)."""
    c = np.asarray(centres, dtype=float)
    mid = (c[:-1] + c[1:]) / 2
    return np.concatenate([[2 * c[0] - mid[0]], mid, [2 * c[-1] - mid[-1]]])


def block_mean(fine, lat, lon, min_coverage=0.5):
    """Average a finer grid onto coarser cells centred on `lat`, `lon`.

    Each fine cell is assigned to the coarse cell containing its centre. Coarse
    cells where less than `min_coverage` of the fine cells have data (e.g. along
    coasts for a land-only dataset) are set to NaN.
    """
    lat, lon = np.asarray(lat), np.asarray(lon)

    def to_coarse(da):
        da = da.groupby_bins("lat", cell_edges(lat), labels=lat).mean()
        da = da.groupby_bins("lon", cell_edges(lon), labels=lon).mean()
        return da.rename(lat_bins="lat", lon_bins="lon").transpose(..., "lat", "lon")

    coverage = to_coarse(fine.notnull().astype(float))
    return to_coarse(fine).where(coverage >= min_coverage)


def nearest_land_cell(mask, lat, lon):
    """Return the (lat, lon) of the land cell closest to a point."""
    lat2d, lon2d = xr.broadcast(mask.lat, mask.lon)
    # Equirectangular distance is accurate enough for picking the nearest cell.
    dx = (lon2d - lon) * np.cos(np.deg2rad(lat))
    dy = lat2d - lat
    distance = np.hypot(dx, dy).where(mask)
    i, j = np.unravel_index(np.nanargmin(distance.values), distance.shape)
    return float(mask.lat[i]), float(mask.lon[j])
