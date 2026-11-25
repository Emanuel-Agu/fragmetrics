"""Integration validation tests against published IndiFrag Valencia reference outputs."""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest

from fragmetrics.metrics import aggregation, area_perimeter, shape

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "valencia"
REF_DIR = REPO_ROOT / "reference" / "expected_results"

pytestmark = pytest.mark.skipif(
    not (DATA_DIR / "VALENCIA_DISTR.shp").exists()
    or not (REF_DIR / "Results_FI_SO.txt").exists(),
    reason="Valencia reference data not available in this installation",
)


@pytest.fixture(scope="module")
def valencia_layers():
    """Load and intersect Valencia LULC objects with districts in EPSG:25830."""
    districts = gpd.read_file(DATA_DIR / "VALENCIA_DISTR.shp")
    objects = gpd.read_file(
        DATA_DIR / "ES003L2_VALENCIA_UA2006_Revised_Clipped_to_Core.shp"
    ).to_crs(districts.crs)

    intersected = gpd.overlay(
        objects[["CLASS", "geometry"]],
        districts[["CUDIS", "geometry"]],
        how="intersection",
        keep_geom_type=False,
    )
    # Keep polygon parts and explode MultiPolygons into single objects (IndiFrag convention)
    intersected = intersected[
        intersected.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
    ].explode(index_parts=False).reset_index(drop=True)

    intersected = area_perimeter.object_metrics(intersected)
    intersected = shape.object_metrics(intersected)
    return intersected, districts


def test_super_object_matches_indifrag_reference(valencia_layers):
    objects, districts = valencia_layers
    so = area_perimeter.super_object_metrics(objects, districts)

    exp = pd.read_csv(REF_DIR / "Results_FI_SO.txt", sep="\t", skiprows=4)
    exp.columns = exp.columns.str.strip()
    exp["CUDIS"] = exp["CUDIS"].astype(str)
    so["CUDIS"] = so["CUDIS"].astype(str)

    merged = so.merge(exp, on="CUDIS", suffixes=("_ours", "_exp"))
    assert len(merged) == len(exp)

    # AreaSO and PerimSO match IndiFrag reference closely (<0.5% CRS/projection diff)
    assert np.allclose(merged["AreaSO_ours"], merged["AreaSO_exp"], rtol=5e-3, atol=1e-3)
    assert np.allclose(merged["PerimSO_ours"], merged["PerimSO_exp"], rtol=5e-3, atol=1e-3)
    # PerimT agrees closely across all districts (minor sliver differences from clipping engines)
    assert np.allclose(merged["PerimT_ours"], merged["PerimT_exp"], rtol=0.02)


def test_class_metrics_match_indifrag_reference(valencia_layers):
    objects, districts = valencia_layers
    cl_ap = area_perimeter.class_metrics(objects)
    cl_ag = aggregation.class_metrics(objects, districts)

    exp = pd.read_csv(REF_DIR / "Results_FI_Cls.txt", sep="\t", skiprows=4)
    exp.columns = exp.columns.str.strip()
    exp["SO"] = exp["SO"].astype(str)
    exp = exp.rename(columns={"CLASE": "CLASS"})

    cl_ap["SO"] = cl_ap["SO"].astype(str)
    cl_ag["SO"] = cl_ag["SO"].astype(str)

    merged_ap = cl_ap.merge(exp, on=["CLASS", "SO"], suffixes=("_ours", "_exp"))
    assert len(merged_ap) == len(exp)
    assert np.allclose(merged_ap["AreaCl_ours"], merged_ap["AreaCl_exp"], rtol=1e-2, atol=1e-3)
    assert np.allclose(merged_ap["DC_ours"], merged_ap["DC_exp"], rtol=1e-2, atol=1e-3)

    # Compactness (C vs CCl); note class 8 in 4625010 has CCl=0.0000 in reference file
    merged_ag = cl_ag.merge(exp, on=["CLASS", "SO"])
    nonzero = merged_ag[merged_ag["CCl"] > 0]
    assert np.allclose(nonzero["C"], nonzero["CCl"], rtol=0.05, atol=0.01)


def test_shape_and_aggregation_run_cleanly_on_valencia(valencia_layers):
    objects, districts = valencia_layers
    cl_sh = shape.class_metrics(objects)
    so_sh = shape.super_object_metrics(objects, districts)
    so_ag = aggregation.super_object_metrics(objects, districts, urban_classes={3, 6, 7})

    assert len(cl_sh) > 0
    assert len(so_sh) == len(districts)
    assert len(so_ag) == len(districts)
    # Compact polygons (more circular than a square) can have DF slightly below 1.0
    assert so_sh["DF"].between(0.9, 2.0).all()
    assert (so_ag["CU"] > 0).all()
