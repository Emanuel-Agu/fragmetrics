"""Unit tests for fragmetrics.metrics.area_perimeter."""

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import box

import fragmetrics
from fragmetrics.metrics import area_perimeter


def _make_synthetic_scene():
    """Return a 2 km x 2 km district partitioned into four 1 km x 1 km squares."""
    districts = gpd.GeoDataFrame(
        {"CUDIS": ["D1"]},
        geometry=[box(0, 0, 2000, 2000)],
        crs="EPSG:25830",
    )
    objects = gpd.GeoDataFrame(
        {
            "CLASS": [1, 1, 2, 2],
            "CUDIS": ["D1", "D1", "D1", "D1"],
        },
        geometry=[
            box(0, 0, 1000, 1000),
            box(1000, 1000, 2000, 2000),
            box(1000, 0, 2000, 1000),
            box(0, 1000, 1000, 2000),
        ],
        crs="EPSG:25830",
    )
    return objects, districts


def test_package_version_exposed():
    assert isinstance(fragmetrics.__version__, str)
    assert len(fragmetrics.__version__) > 0


def test_object_metrics_units():
    objects, _ = _make_synthetic_scene()
    res = area_perimeter.object_metrics(objects)
    assert np.allclose(res["AreaO"], 1.0)    # 1e6 m² = 1 km²
    assert np.allclose(res["PerimO"], 4.0)   # 4000 m = 4 km


def test_class_metrics_basic_and_leapfrog():
    # Two disjoint squares of class 1 (LPF = 1.0), two edge-touching squares of class 2 (LPF = 0.0)
    objects = gpd.GeoDataFrame(
        {
            "CLASS": [1, 1, 2, 2],
            "CUDIS": ["D1", "D1", "D1", "D1"],
        },
        geometry=[
            box(0, 0, 1000, 1000),
            box(2000, 0, 3000, 1000),
            box(0, 2000, 1000, 3000),
            box(1000, 2000, 2000, 3000),
        ],
        crs="EPSG:25830",
    )
    objects = area_perimeter.object_metrics(objects)
    cl = area_perimeter.class_metrics(objects)

    c1 = cl[cl["CLASS"] == 1].iloc[0]
    c2 = cl[cl["CLASS"] == 2].iloc[0]

    assert c1["AreaCl"] == pytest.approx(2.0)
    assert c1["PerimCl"] == pytest.approx(8.0)
    assert c1["NobCl"] == 2
    assert c1["DC"] == pytest.approx(0.5)
    assert c1["TM"] == pytest.approx(1e6)
    assert c1["DB"] == pytest.approx(2.0)
    assert c1["LPF"] == pytest.approx(1.0)

    assert c2["LPF"] == pytest.approx(0.0)


def test_boundary_dimension_scales_as_expected():
    # Squares of varying sizes have A = (P/4)^2 => ln(A) = 2 ln(P) + c => dimB = 2/2 = 1.0
    sides = np.array([100.0, 200.0, 500.0, 1000.0])
    dimb = area_perimeter._boundary_dimension(sides**2, 4 * sides)
    assert dimb == pytest.approx(1.0)


def test_super_object_metrics_and_urban_density():
    objects, districts = _make_synthetic_scene()
    objects = area_perimeter.object_metrics(objects)
    so = area_perimeter.super_object_metrics(
        objects, districts, urban_classes={1}
    )

    row = so.iloc[0]
    assert row["AreaSO"] == pytest.approx(4.0)
    assert row["PerimSO"] == pytest.approx(8.0)
    assert row["PerimT"] == pytest.approx(12.0)
    assert row["NCl"] == 2
    assert row["NobSO"] == 4
    assert row["DU"] == pytest.approx(0.5)


def test_ifup():
    objects, districts = _make_synthetic_scene()
    objects = area_perimeter.object_metrics(objects)
    res = area_perimeter.ifup(objects, districts, obstruction_map={1: 1.0, 2: 0.0})

    assert res.iloc[0]["IFU"] == pytest.approx(1000.0)
    assert res.iloc[0]["IFUP"] == pytest.approx(1000.0)
