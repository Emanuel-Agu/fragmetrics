"""
Aggregation metrics from IndiFrag: Nob, DO, DEP, DEM, TEM, COHE, IS, GC, CU, C.

All functions expect geometries in a projected CRS (metres).
A_T always refers to super-object area.

Levels:
  Cl = Class     (group of objects with same land-use class within a super-object)
  SO = Super-Object (district / administrative unit)
"""

import numpy as np
import pandas as pd
import geopandas as gpd


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _nearest_neighbor_distances(group_gdf):
    """Min boundary-to-boundary distance from each object to its nearest neighbour.

    Parameters
    ----------
    group_gdf : GeoDataFrame
        Objects belonging to one group (e.g. one class within one SO).

    Returns
    -------
    np.ndarray
        Array of minimum distances in CRS units (metres). NaN if n <= 1.
    """
    n = len(group_gdf)
    if n <= 1:
        return np.full(n, np.nan)

    geoms = group_gdf.geometry.values
    min_dists = np.empty(n)
    for i in range(n):
        dists = np.array([geoms[i].distance(geoms[j])
                          for j in range(n) if j != i])
        min_dists[i] = dists.min()
    return min_dists


# ---------------------------------------------------------------------------
# Class level (Cl)  —  one row per (class, super-object) combination
# ---------------------------------------------------------------------------

def class_metrics(objects_gdf, districts_gdf,
                  class_col="CLASS", so_col="CUDIS"):
    """Compute class-level aggregation metrics within each super-object.

    Parameters
    ----------
    objects_gdf : GeoDataFrame
        Objects with AreaO, PerimO already computed (call
        area_perimeter.object_metrics first). Must contain columns for
        the LULC class and the super-object ID.
    districts_gdf : GeoDataFrame
        District polygons with a name/ID column matching so_col.
    class_col : str
        Column with the LULC class identifier.
    so_col : str
        Column with the super-object identifier.

    Returns
    -------
    DataFrame with columns: CLASS, SO, Nob, DO, DEP, DEM, TEM, COHE, IS, GC, C
    """
    # SO areas from district polygons (m²)
    so_area_m2 = districts_gdf.set_index(so_col).geometry.area.rename("AreaSO_m2")

    # Pre-compute per-object values in metres
    temp = objects_gdf[[class_col, so_col, "geometry"]].copy()
    temp["_area_m2"] = objects_gdf.geometry.area
    temp["_perim_m"] = objects_gdf.geometry.length
    temp["_cx"] = objects_gdf.geometry.centroid.x
    temp["_cy"] = objects_gdf.geometry.centroid.y

    rows = []
    for (so, cls), grp in temp.groupby([so_col, class_col]):
        n = len(grp)
        a_i = grp["_area_m2"].values   # m²
        p_i = grp["_perim_m"].values   # m
        cx = grp["_cx"].values
        cy = grp["_cy"].values
        A_T = so_area_m2.get(so, np.nan)  # m²

        # Nob
        nob = n

        # DO — object density (n/km²)
        do = n / (A_T / 1e6) if A_T > 0 else np.nan

        # DEP — area-weighted standard distance (m → km)
        sum_a = a_i.sum()
        if sum_a > 0 and A_T > 0:
            x_bar = (a_i * cx).sum() / sum_a
            y_bar = (a_i * cy).sum() / sum_a
            dep_m = np.sqrt(
                (a_i * (cx - x_bar) ** 2).sum() / A_T
                + (a_i * (cy - y_bar) ** 2).sum() / A_T
            )
            dep = dep_m / 1e3
        else:
            dep = np.nan

        # DEM — mean nearest-neighbour distance (m → km)
        if n > 1:
            nn_dists = _nearest_neighbor_distances(grp)
            dem = np.nanmean(nn_dists) / 1e3
        else:
            dem = np.nan

        # TEM — effective mesh size (m² → km²)
        # Σ(A_i²) / A_T, all in m², result in m² → convert to km²
        tem = (a_i ** 2).sum() / A_T / 1e6 if A_T > 0 else np.nan

        # COHE — patch cohesion
        sum_p = p_i.sum()
        if sum_p > 0 and A_T > 0:
            sum_p_sqrtA = (p_i * np.sqrt(a_i)).sum()
            denom = 1.0 - 1.0 / np.sqrt(A_T)
            if denom != 0:
                cohe = (1.0 - sum_p / sum_p_sqrtA) / denom
            else:
                cohe = np.nan
        else:
            cohe = np.nan

        # IS — splitting index
        sum_a2 = (a_i ** 2).sum()
        A_T_km2 = A_T / 1e6
        a_i_km2 = a_i / 1e6
        if sum_a2 > 0:
            is_val = (A_T_km2 ** 2) / (a_i_km2 ** 2).sum()
        else:
            is_val = np.nan

        # GC — Gini coefficient of concentration
        if A_T > 0:
            gc = ((a_i / A_T) ** 2).sum()
        else:
            gc = np.nan

        # C — class compactness: 2·√(π·ΣA) / ΣP  (all in metres)
        if sum_p > 0 and sum_a > 0:
            c_val = 2.0 * np.sqrt(np.pi * sum_a) / sum_p
        else:
            c_val = np.nan

        rows.append({
            "CLASS": cls, "SO": so,
            "Nob": nob, "DO": do, "DEP": dep, "DEM": dem,
            "TEM": tem, "COHE": cohe, "IS": is_val, "GC": gc, "C": c_val,
        })

    result = pd.DataFrame(rows)
    # Ensure consistent types
    result["Nob"] = result["Nob"].astype(int)
    return result


# ---------------------------------------------------------------------------
# Super-object level (SO)
# ---------------------------------------------------------------------------

def super_object_metrics(objects_gdf, districts_gdf,
                         class_col="CLASS", so_col="CUDIS",
                         urban_classes=None):
    """Compute super-object level aggregation metrics.

    Parameters
    ----------
    objects_gdf : GeoDataFrame
        Objects with AreaO, PerimO already computed.
    districts_gdf : GeoDataFrame
        District polygons with a name/ID column matching so_col.
    class_col : str
        Column with the LULC class identifier (used for CU if urban_classes
        is provided).
    so_col : str
        Column with the super-object identifier.
    urban_classes : list or set, optional
        Class identifiers considered "urban". When provided, a CU (urban
        compactness) column is added.

    Returns
    -------
    DataFrame with columns: CUDIS, Nob, DO, DEP, TEM, COHE, IS, GC[, CU]
    """
    # SO areas from district polygons (m²)
    so_area_m2 = districts_gdf.set_index(so_col).geometry.area.rename("AreaSO_m2")

    # Pre-compute per-object values
    temp = objects_gdf[[class_col, so_col, "geometry"]].copy()
    temp["_area_m2"] = objects_gdf.geometry.area
    temp["_perim_m"] = objects_gdf.geometry.length
    temp["_cx"] = objects_gdf.geometry.centroid.x
    temp["_cy"] = objects_gdf.geometry.centroid.y

    rows = []
    for so, grp in temp.groupby(so_col):
        n = len(grp)
        a_i = grp["_area_m2"].values
        p_i = grp["_perim_m"].values
        cx = grp["_cx"].values
        cy = grp["_cy"].values
        A_T = so_area_m2.get(so, np.nan)

        # Nob
        nob = n

        # DO
        do = n / (A_T / 1e6) if A_T > 0 else np.nan

        # DEP
        sum_a = a_i.sum()
        if sum_a > 0 and A_T > 0:
            x_bar = (a_i * cx).sum() / sum_a
            y_bar = (a_i * cy).sum() / sum_a
            dep_m = np.sqrt(
                (a_i * (cx - x_bar) ** 2).sum() / A_T
                + (a_i * (cy - y_bar) ** 2).sum() / A_T
            )
            dep = dep_m / 1e3
        else:
            dep = np.nan

        # TEM
        tem = (a_i ** 2).sum() / A_T / 1e6 if A_T > 0 else np.nan

        # COHE
        sum_p = p_i.sum()
        if sum_p > 0 and A_T > 0:
            sum_p_sqrtA = (p_i * np.sqrt(a_i)).sum()
            denom = 1.0 - 1.0 / np.sqrt(A_T)
            if denom != 0:
                cohe = (1.0 - sum_p / sum_p_sqrtA) / denom
            else:
                cohe = np.nan
        else:
            cohe = np.nan

        # IS
        A_T_km2 = A_T / 1e6
        a_i_km2 = a_i / 1e6
        sum_a2_km2 = (a_i_km2 ** 2).sum()
        is_val = (A_T_km2 ** 2) / sum_a2_km2 if sum_a2_km2 > 0 else np.nan

        # GC
        gc = ((a_i / A_T) ** 2).sum() if A_T > 0 else np.nan

        row = {
            "CUDIS": so,
            "Nob": nob, "DO": do, "DEP": dep,
            "TEM": tem, "COHE": cohe, "IS": is_val, "GC": gc,
        }

        # CU — urban compactness
        if urban_classes is not None:
            urban_mask = grp[class_col].isin(urban_classes)
            a_u = grp.loc[urban_mask, "_area_m2"].sum()
            p_u = grp.loc[urban_mask, "_perim_m"].sum()
            if p_u > 0 and a_u > 0:
                row["CU"] = 2.0 * np.sqrt(np.pi * a_u) / p_u
            else:
                row["CU"] = np.nan

        rows.append(row)

    result = pd.DataFrame(rows)
    result["Nob"] = result["Nob"].astype(int)
    return result
