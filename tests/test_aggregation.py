"""Unit tests for fragmetrics.metrics.aggregation."""

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import box

from fragmetrics.metrics import aggregation


def _make_aggregation_scene():
    districts = gpd.GeoDataFrame(
        {"CUDIS": ["D1"]},
        geometry=[box(0, 0, 2000, 2000)],  # 4 km²
        crs="EPSG:25830",
    )
    # Two class-1 squares separated by 500 m horizontally, plus one class-2 square
    objects = gpd.GeoDataFrame(
        {"CLASS": [1, 1, 2], "CUDIS": ["D1", "D1", "D1"]},
        geometry=[
            box(0, 0, 500, 500),       # 0.25 km²
            box(1000, 0, 1500, 500),   # 0.25 km², 500 m from first
            box(0, 1000, 1000, 2000),  # 1.00 km²
        ],
        crs="EPSG:25830",
    )
    return objects, districts


def test_nearest_neighbor_distances():
    objects, _ = _make_aggregation_scene()
    c1 = objects[objects["CLASS"] == 1]
    dists = aggregation._nearest_neighbor_distances(c1)
    assert np.allclose(dists, [500.0, 500.0])

    # Single object -> NaN
    c2 = objects[objects["CLASS"] == 2]
    dists_single = aggregation._nearest_neighbor_distances(c2)
    assert len(dists_single) == 1
    assert np.isnan(dists_single[0])


def test_class_aggregation_metrics():
    objects, districts = _make_aggregation_scene()
    cl = aggregation.class_metrics(objects, districts)

    c1 = cl[cl["CLASS"] == 1].iloc[0]
    c2 = cl[cl["CLASS"] == 2].iloc[0]

    assert c1["Nob"] == 2
    assert c1["DO"] == pytest.approx(2 / 4.0)
    assert c1["DEM"] == pytest.approx(0.5)  # 500 m = 0.5 km
    # TEM = (0.25^2 + 0.25^2) / 4 = 0.125 / 4 = 0.03125 km²
    assert c1["TEM"] == pytest.approx(0.03125)
    # IS = 4^2 / (0.25^2 + 0.25^2) = 16 / 0.125 = 128
    assert c1["IS"] == pytest.approx(128.0)
    # GC = (0.25/4)^2 + (0.25/4)^2 = 2 / 256 = 1/128
    assert c1["GC"] == pytest.approx(1.0 / 128.0)
    # C = 2*sqrt(pi * 500000) / 4000
    assert c1["C"] == pytest.approx(2.0 * np.sqrt(np.pi * 500_000.0) / 4000.0)

    # Single object class: DEM is NaN, DEP is 0.0
    assert c2["Nob"] == 1
    assert np.isnan(c2["DEM"])
    assert c2["DEP"] == pytest.approx(0.0)


def test_super_object_aggregation_metrics_with_urban_compactness():
    objects, districts = _make_aggregation_scene()
    so = aggregation.super_object_metrics(objects, districts, urban_classes={2})

    row = so.iloc[0]
    assert row["Nob"] == 3
    assert row["DO"] == pytest.approx(3 / 4.0)
    # Urban class 2 is a 1000x1000 square: C_u = 2*sqrt(pi*1e6)/4000 = sqrt(pi)/2
    assert row["CU"] == pytest.approx(np.sqrt(np.pi) / 2.0)


def test_aggregation_geographic_crs_raises():
    gdf = gpd.GeoDataFrame(
        {"CLASS": [1], "CUDIS": ["D1"]},
        geometry=[box(0, 0, 1, 1)],
        crs="EPSG:4326",
    )
    with pytest.raises(ValueError, match="geographic CRS"):
        aggregation.class_metrics(gdf, gdf)
