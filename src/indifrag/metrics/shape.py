"""
Shape metrics from IndiFrag: DF, DFP, IF, RMPA.

All functions expect geometries in a projected CRS (metres).

Levels:
  O  = Object    (individual polygon)
  Cl = Class     (group of objects with same land-use class within a super-object)
  SO = Super-Object (district / administrative unit)
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Object level (O)
# ---------------------------------------------------------------------------

def object_metrics(objects_gdf):
    """Add shape metrics DF and IF to the objects GeoDataFrame.

    Parameters
    ----------
    objects_gdf : GeoDataFrame
        Must have a projected CRS in metres. Each row is one LULC object.

    Returns
    -------
    GeoDataFrame with added columns: DF, IF
        DF = fractal dimension = 2 · ln(0.25 · P) / ln(A)
        IF = shape index = 0.25 · P / √A
        (P in metres, A in m²)
    """
    gdf = objects_gdf.copy()
    area_m2 = gdf.geometry.area
    perim_m = gdf.geometry.length

    # DF — fractal dimension
    # Guard: A ≤ 0, P ≤ 0, or ln(A) = 0 → NaN
    with np.errstate(divide="ignore", invalid="ignore"):
        ln_a = np.log(area_m2)
        ln_qp = np.log(0.25 * perim_m)
        df = 2.0 * ln_qp / ln_a
    valid = (area_m2 > 0) & (perim_m > 0) & (ln_a != 0)
    gdf["DF"] = np.where(valid, df, np.nan)

    # IF — shape index
    with np.errstate(divide="ignore", invalid="ignore"):
        shape_idx = 0.25 * perim_m / np.sqrt(area_m2)
    gdf["IF"] = np.where(area_m2 > 0, shape_idx, np.nan)

    return gdf


# ---------------------------------------------------------------------------
# Class level (Cl)  —  one row per (class, super-object) combination
# ---------------------------------------------------------------------------

def class_metrics(objects_gdf, class_col="CLASS", so_col="CUDIS"):
    """Compute class-level shape metrics within each super-object.

    Parameters
    ----------
    objects_gdf : GeoDataFrame
        Objects with DF column already computed (call object_metrics first).
        Must contain columns for the LULC class and the super-object ID.
    class_col : str
        Column with the LULC class identifier.
    so_col : str
        Column with the super-object identifier.

    Returns
    -------
    DataFrame with columns: CLASS, SO, DF, DFP, IF, RMPA
    """
    # Pre-compute per-object values in metres for aggregation
    area_m2 = objects_gdf.geometry.area
    perim_m = objects_gdf.geometry.length

    temp = objects_gdf[[class_col, so_col]].copy()
    temp["_area_m2"] = area_m2
    temp["_perim_m"] = perim_m
    temp["_pa_ratio"] = perim_m / area_m2  # for RMPA
    temp["_DF_obj"] = objects_gdf["DF"]    # object-level DF for DFP

    grouped = temp.groupby([so_col, class_col])

    # Aggregate area and perimeter in metres
    agg = grouped.agg(
        AreaCl_m2=("_area_m2", "sum"),
        PerimCl_m=("_perim_m", "sum"),
    ).reset_index()
    agg.rename(columns={so_col: "SO", class_col: "CLASS"}, inplace=True)

    # DF at class level — from aggregate area/perimeter
    with np.errstate(divide="ignore", invalid="ignore"):
        ln_a = np.log(agg["AreaCl_m2"])
        ln_qp = np.log(0.25 * agg["PerimCl_m"])
        agg["DF"] = np.where(
            (agg["AreaCl_m2"] > 0) & (agg["PerimCl_m"] > 0) & (ln_a != 0),
            2.0 * ln_qp / ln_a,
            np.nan,
        )

    # DFP — area-weighted mean of object-level DF
    def _dfp(grp):
        valid = grp["_DF_obj"].notna() & (grp["_area_m2"] > 0)
        if not valid.any():
            return np.nan
        g = grp.loc[valid]
        return (g["_DF_obj"] * g["_area_m2"]).sum() / g["_area_m2"].sum()

    dfp = grouped.apply(_dfp, include_groups=False).rename("DFP").reset_index()
    dfp.rename(columns={so_col: "SO", class_col: "CLASS"}, inplace=True)
    agg = agg.merge(dfp, on=["SO", "CLASS"], how="left")

    # IF at class level — from aggregate area/perimeter
    with np.errstate(divide="ignore", invalid="ignore"):
        agg["IF"] = np.where(
            agg["AreaCl_m2"] > 0,
            0.25 * agg["PerimCl_m"] / np.sqrt(agg["AreaCl_m2"]),
            np.nan,
        )

    # RMPA — mean of object-level P/A ratios
    rmpa = grouped["_pa_ratio"].mean().reset_index(name="RMPA")
    rmpa.rename(columns={so_col: "SO", class_col: "CLASS"}, inplace=True)
    agg = agg.merge(rmpa, on=["SO", "CLASS"], how="left")

    return agg[["CLASS", "SO", "DF", "DFP", "IF", "RMPA"]]


# ---------------------------------------------------------------------------
# Super-object level (SO)
# ---------------------------------------------------------------------------

def super_object_metrics(objects_gdf, districts_gdf,
                         class_col="CLASS", so_col="CUDIS"):
    """Compute super-object level shape metrics.

    Parameters
    ----------
    objects_gdf : GeoDataFrame
        Objects with geometry in projected CRS (metres).
    districts_gdf : GeoDataFrame
        District polygons with a name/ID column matching so_col.
    class_col : str
        Column with the LULC class identifier (unused here, kept for API
        consistency).
    so_col : str
        Column with the super-object identifier.

    Returns
    -------
    DataFrame with columns: CUDIS, DF, IF, RMPA
    """
    # DF and IF from district polygon geometry
    area_m2 = districts_gdf.geometry.area
    perim_m = districts_gdf.geometry.length

    so = pd.DataFrame({"CUDIS": districts_gdf[so_col]})

    with np.errstate(divide="ignore", invalid="ignore"):
        ln_a = np.log(area_m2.values)
        ln_qp = np.log(0.25 * perim_m.values)
        so["DF"] = np.where(
            (area_m2.values > 0) & (perim_m.values > 0) & (ln_a != 0),
            2.0 * ln_qp / ln_a,
            np.nan,
        )

    with np.errstate(divide="ignore", invalid="ignore"):
        so["IF"] = np.where(
            area_m2.values > 0,
            0.25 * perim_m.values / np.sqrt(area_m2.values),
            np.nan,
        )

    # RMPA — mean of object-level P/A ratios within each SO
    temp = pd.DataFrame({
        "SO": objects_gdf[so_col],
        "_pa_ratio": objects_gdf.geometry.length / objects_gdf.geometry.area,
    })
    rmpa = temp.groupby("SO")["_pa_ratio"].mean().reset_index()
    rmpa.rename(columns={"SO": "CUDIS", "_pa_ratio": "RMPA"}, inplace=True)
    so = so.merge(rmpa, on="CUDIS", how="left")

    return so
