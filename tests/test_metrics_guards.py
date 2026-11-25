"""Unit tests for CRS validation, degenerate geometry guards, and STRtree nearest-neighbor."""

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import LineString, Point, Polygon, box

from fragmetrics.metrics import aggregation, area_perimeter, shape


def test_geographic_crs_raises_across_metric_modules():
    gdf = gpd.GeoDataFrame(
        {"CLASS": [1], "CUDIS": ["D1"]},
        geometry=[box(0, 0, 1, 1)],
        crs="EPSG:4326",
    )
    with pytest.raises(ValueError, match="geographic CRS"):
        area_perimeter.object_metrics(gdf)
    with pytest.raises(ValueError, match="geographic CRS"):
        shape.object_metrics(gdf)
    with pytest.raises(ValueError, match="geographic CRS"):
        aggregation.class_metrics(gdf, gdf)


def test_degenerate_geometries_in_max_object_length():
    assert area_perimeter._max_object_length(Point(0, 0)) == 0.0
    assert area_perimeter._max_object_length(Polygon()) == 0.0
    assert area_perimeter._max_object_length(None) == 0.0
    assert area_perimeter._max_object_length(LineString([(0, 0), (30, 40)])) == pytest.approx(50.0)


def test_boundary_dimension_identical_perimeters_returns_nan():
    assert np.isnan(area_perimeter._boundary_dimension([100.0, 100.0], [40.0, 40.0]))


def test_strtree_nearest_neighbor_distances():
    gdf = gpd.GeoDataFrame(
        {"CLASS": [1, 1, 1], "CUDIS": ["D1", "D1", "D1"]},
        geometry=[
            box(0, 0, 100, 100),
            box(300, 0, 400, 100),   # 200 m from first
            box(1000, 0, 1100, 100), # 600 m from second
        ],
        crs="EPSG:25830",
    )
    dists = aggregation._nearest_neighbor_distances(gdf)
    assert np.allclose(dists, [200.0, 200.0, 600.0])
