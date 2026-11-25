"""Unit tests for fragmetrics.metrics.shape."""

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import Point, box

from fragmetrics.metrics import shape


def test_object_metrics_square_and_circle():
    sq = box(0, 0, 100, 100)
    circ = Point(500, 500).buffer(100, quad_segs=256)

    gdf = gpd.GeoDataFrame(
        {"CLASS": [1, 2], "CUDIS": ["D1", "D1"]},
        geometry=[sq, circ],
        crs="EPSG:25830",
    )
    res = shape.object_metrics(gdf)

    assert res.loc[0, "DF"] == pytest.approx(1.0, rel=1e-9)
    assert res.loc[0, "IF"] == pytest.approx(1.0, rel=1e-9)
    assert res.loc[1, "IF"] == pytest.approx(np.sqrt(np.pi) / 2.0, rel=1e-3)


def test_class_and_super_object_shape_metrics():
    districts = gpd.GeoDataFrame(
        {"CUDIS": ["D1"]},
        geometry=[box(0, 0, 200, 200)],
        crs="EPSG:25830",
    )
    objects = gpd.GeoDataFrame(
        {"CLASS": [1, 1], "CUDIS": ["D1", "D1"]},
        geometry=[box(0, 0, 100, 100), box(100, 0, 200, 100)],
        crs="EPSG:25830",
    )
    objects = shape.object_metrics(objects)
    cl = shape.class_metrics(objects)
    so = shape.super_object_metrics(objects, districts)

    row_cl = cl.iloc[0]
    assert row_cl["DFP"] == pytest.approx(1.0)
    assert row_cl["RMPA"] == pytest.approx(0.04)
    assert row_cl["IF"] == pytest.approx(np.sqrt(2.0))

    row_so = so.iloc[0]
    assert row_so["DF"] == pytest.approx(1.0)
    assert row_so["IF"] == pytest.approx(1.0)
    assert row_so["RMPA"] == pytest.approx(0.04)
