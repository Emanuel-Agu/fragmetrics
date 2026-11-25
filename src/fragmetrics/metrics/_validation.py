"""Internal input validation helpers for fragmetrics."""

import geopandas as gpd


def check_projected_crs(gdf: gpd.GeoDataFrame, name: str = "GeoDataFrame") -> None:
    """Raise ValueError if *gdf* uses a geographic (angular) CRS.

    Metric formulas assume planar coordinates in metres. A missing CRS
    (``None``) is permitted so synthetic unit-test geometries work without
    assigning an EPSG code, while geographic CRSs (e.g. EPSG:4326) are
    rejected explicitly to prevent silent area/perimeter corruption.
    """
    if gdf.crs is not None and gdf.crs.is_geographic:
        raise ValueError(
            f"{name} has a geographic CRS ({gdf.crs}). "
            "Reproject to a projected CRS in metres (e.g. UTM or EPSG:3035) "
            "before computing fragmentation metrics."
        )
