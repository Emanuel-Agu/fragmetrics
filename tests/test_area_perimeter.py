"""Unit tests for fragmetrics.metrics.area_perimeter."""

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import LineString, Point, Polygon, box

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
            box(0, 0, 1000, 1000),      # touching class 1? no, diagonal corner -> intersects=True!
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


def test_geographic_crs_raises():
    gdf = gpd.GeoDataFrame(
        {"CLASS": [1], "CUDIS": ["D1"]},
        geometry=[box(0, 0, 1, 1)],
        crs="EPSG:4326",
    )
    with pytest.raises(ValueError, match="geographic CRS"):
        area_perimeter.object_metrics(gdf)


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
    assert np.isnan(c1["dimB"])  # identical perimeters -> degenerate regression

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
    # 4 internal edges of 1 km + 8 km outer boundary = 12 km unique edge length
    # Formula: (sum_obj_perims=16 + PerimSO=8) / 2 = 12 km
    assert row["PerimT"] == pytest.approx(12.0)
    assert row["NCl"] == 2
    assert row["NobSO"] == 4
    assert row["DU"] == pytest.approx(0.5)


def test_ifup_and_degenerate_geometries():
    objects, districts = _make_synthetic_scene()
    objects = area_perimeter.object_metrics(objects)
    res = area_perimeter.ifup(objects, districts, obstruction_map={1: 1.0, 2: 0.0})

    # Each class-1 square has L_max=1000 m, AreaCl=2.0 km², O_c=1.0 -> contrib=2000 each -> sum=4000
    # IFU = 4000 / AreaSO(4.0) = 1000.0; single district => IFUP == IFU
    assert res.iloc[0]["IFU"] == pytest.approx(1000.0)
    assert res.iloc[0]["IFUP"] == pytest.approx(1000.0)

    # Degenerate geometries must not crash _max_object_length
    assert area_perimeter._max_object_length(Point(0, 0)) == 0.0
    assert area_perimeter._max_object_length(Polygon()) == 0.0
    assert area_perimeter._max_object_length(LineString([(0, 0), (30, 40)])) == pytest.approx(50.0)
