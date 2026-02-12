"""
Area and perimeter metrics from IndiFrag.

All functions expect geometries in a projected CRS (metres).
Output areas are in km², perimeters in km, to match IndiFrag conventions.

Levels:
  O  = Object    (individual polygon)
  Cl = Class     (group of objects with same land-use class within a super-object)
  SO = Super-Object (district / administrative unit)
"""

import numpy as np
import pandas as pd
import geopandas as gpd


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _boundary_dimension(areas_m2, perims_m):
    """Fractal boundary dimension from ln(A) vs ln(P) regression.

    Parameters
    ----------
    areas_m2 : array-like
        Object areas in m².
    perims_m : array-like
        Object perimeters in m.

    Returns
    -------
    float
        dimB value (typically 1.0–2.0), or NaN if undetermined.
    """
    a = np.asarray(areas_m2, dtype=float)
    p = np.asarray(perims_m, dtype=float)
    mask = (a > 0) & (p > 0)
    if mask.sum() < 2:
        return np.nan
    ln_a = np.log(a[mask])
    ln_p = np.log(p[mask])
    slope, _ = np.polyfit(ln_p, ln_a, 1)  # ln(A) = slope·ln(P) + intercept
    if slope <= 0:
        return np.nan
    return 2.0 / slope


def _leapfrog(group_gdf):
    """Fraction of total class area in isolated (non-touching) objects.

    Parameters
    ----------
    group_gdf : GeoDataFrame
        Objects belonging to one class within one super-object.

    Returns
    -------
    float
        LPF value in [0, 1].
    """
    n = len(group_gdf)
    if n <= 1:
        return 1.0

    gdf = group_gdf.reset_index(drop=True)
    # Self-join to find touching pairs
    joined = gpd.sjoin(gdf, gdf, how="inner", predicate="intersects")
    # Remove self-matches
    joined = joined[joined.index != joined["index_right"]]
    touching_idx = set(joined.index)
    isolated_mask = ~gdf.index.isin(touching_idx)
    total_area = gdf["AreaO"].sum()
    if total_area == 0:
        return np.nan
    return gdf.loc[isolated_mask, "AreaO"].sum() / total_area


def _max_object_length(geom):
    """Longest axis of the minimum rotated bounding rectangle.

    Parameters
    ----------
    geom : shapely geometry

    Returns
    -------
    float
        Length in the geometry's CRS units (metres for projected CRS).
    """
    rect = geom.minimum_rotated_rectangle
    coords = list(rect.exterior.coords)
    # Rectangle has 5 coords (closed ring); measure two adjacent edges
    d1 = np.hypot(coords[1][0] - coords[0][0], coords[1][1] - coords[0][1])
    d2 = np.hypot(coords[2][0] - coords[1][0], coords[2][1] - coords[1][1])
    return max(d1, d2)


# ---------------------------------------------------------------------------
# Object level (O)
# ---------------------------------------------------------------------------

def object_metrics(objects_gdf):
    """Add AreaO (km²) and PerimO (km) columns to objects GeoDataFrame.

    Parameters
    ----------
    objects_gdf : GeoDataFrame
        Must have a projected CRS in metres. Each row is one LULC object.

    Returns
    -------
    GeoDataFrame with added columns: AreaO, PerimO
    """
    gdf = objects_gdf.copy()
    gdf["AreaO"] = gdf.geometry.area / 1e6     # m² → km²
    gdf["PerimO"] = gdf.geometry.length / 1e3  # m  → km
    return gdf


# ---------------------------------------------------------------------------
# Class level (Cl)  —  one row per (class, super-object) combination
# ---------------------------------------------------------------------------

def class_metrics(objects_gdf, class_col="CLASS", so_col="CUDIS"):
    """Compute class-level area/perimeter metrics within each super-object.

    Parameters
    ----------
    objects_gdf : GeoDataFrame
        Objects with AreaO, PerimO already computed (call object_metrics first).
        Must contain columns for the LULC class and the super-object ID.
    class_col : str
        Column with the LULC class identifier.
    so_col : str
        Column with the super-object identifier.

    Returns
    -------
    DataFrame with columns: CLASS, SO, AreaCl, PerimCl, NobCl, DC, TM, DB, dimB, LPF
    """
    grouped = objects_gdf.groupby([so_col, class_col])

    cl = pd.DataFrame({
        "AreaCl": grouped["AreaO"].sum(),           # km²
        "PerimCl": grouped["PerimO"].sum(),         # km
        "NobCl": grouped["AreaO"].count(),           # count
    }).reset_index()

    cl.rename(columns={so_col: "SO", class_col: "CLASS"}, inplace=True)

    # Super-object total areas for density calculation
    so_areas = objects_gdf.groupby(so_col)["AreaO"].sum()
    cl["AreaSO"] = cl["SO"].map(so_areas)

    # DC — class density: ratio of class area to super-object area
    cl["DC"] = cl["AreaCl"] / cl["AreaSO"]

    # TM — object mean size (m²): average area of objects in this class/SO
    cl["TM"] = (cl["AreaCl"] / cl["NobCl"]) * 1e6  # km² back to m²

    # DB — edge density: total perimeter / SO area (km / km² = 1/km)
    cl["DB"] = cl["PerimCl"] / cl["AreaSO"]

    # dimB — boundary dimension per class-SO group
    dimb_vals = {}
    lpf_vals = {}
    for (so, cls), grp in objects_gdf.groupby([so_col, class_col]):
        areas_m2 = grp.geometry.area
        perims_m = grp.geometry.length
        dimb_vals[(so, cls)] = _boundary_dimension(areas_m2, perims_m)
        lpf_vals[(so, cls)] = _leapfrog(grp)

    cl["dimB"] = cl.apply(lambda r: dimb_vals.get((r["SO"], r["CLASS"]), np.nan), axis=1)

    # LPF — gross leapfrog per class-SO group
    cl["LPF"] = cl.apply(lambda r: lpf_vals.get((r["SO"], r["CLASS"]), np.nan), axis=1)

    cl.drop(columns="AreaSO", inplace=True)
    return cl


# ---------------------------------------------------------------------------
# Super-object level (SO)
# ---------------------------------------------------------------------------

def super_object_metrics(objects_gdf, districts_gdf,
                         class_col="CLASS", so_col="CUDIS",
                         urban_classes=None):
    """Compute super-object level area/perimeter metrics.

    Parameters
    ----------
    objects_gdf : GeoDataFrame
        Objects with AreaO, PerimO already computed.
    districts_gdf : GeoDataFrame
        District polygons with a name/ID column matching so_col.
    class_col : str
        Column with the LULC class identifier.
    so_col : str
        Column with the super-object identifier.
    urban_classes : list or set, optional
        Class identifiers considered "urban". When provided, a DU (urban
        density) column is added: A_urban / A_SO.

    Returns
    -------
    DataFrame with columns: CUDIS, AreaSO, PerimSO, PerimT, NCl, NobSO[, DU]
    """
    # SO area and perimeter from the district polygons themselves
    so = pd.DataFrame({
        "CUDIS": districts_gdf[so_col],
        "AreaSO": districts_gdf.geometry.area / 1e6,    # km²
        "PerimSO": districts_gdf.geometry.length / 1e3,  # km
    })

    # Aggregate objects within each SO
    obj_agg = objects_gdf.groupby(so_col).agg(
        obj_perim_sum=("PerimO", "sum"),
        NCl=(class_col, "nunique"),
        NobSO=("AreaO", "count"),
    ).reset_index().rename(columns={so_col: "CUDIS"})

    so = so.merge(obj_agg, on="CUDIS", how="left")

    # PerimT — total unique edge length (without boundary duplicity).
    # In a planar tessellation each internal edge is shared by two objects,
    # so: PerimT = (sum_object_perimeters + PerimSO) / 2
    so["PerimT"] = (so["obj_perim_sum"] + so["PerimSO"]) / 2
    so.drop(columns="obj_perim_sum", inplace=True)

    # DU — urban density
    if urban_classes is not None:
        urban_mask = objects_gdf[class_col].isin(urban_classes)
        urban_area = (
            objects_gdf.loc[urban_mask]
            .groupby(so_col)["AreaO"]
            .sum()
            .rename("A_urban")
        )
        so = so.merge(
            urban_area.reset_index().rename(columns={so_col: "CUDIS"}),
            on="CUDIS", how="left",
        )
        so["A_urban"] = so["A_urban"].fillna(0.0)
        so["DU"] = so["A_urban"] / so["AreaSO"]
        so.drop(columns="A_urban", inplace=True)

    return so


# ---------------------------------------------------------------------------
# IFUP — Weighted urban fragmentation
# ---------------------------------------------------------------------------

def ifup(objects_gdf, districts_gdf, obstruction_map,
         class_col="CLASS", so_col="CUDIS"):
    """Compute weighted urban fragmentation index (IFU per SO, IFUP overall).

    Parameters
    ----------
    objects_gdf : GeoDataFrame
        Objects with AreaO already computed (call object_metrics first).
    districts_gdf : GeoDataFrame
        District polygons with a name/ID column matching so_col.
    obstruction_map : dict
        Mapping of class ID → obstruction coefficient O_c (0–1).
    class_col : str
        Column with the LULC class identifier.
    so_col : str
        Column with the super-object identifier.

    Returns
    -------
    DataFrame with columns: CUDIS, IFU, IFUP
        IFU is per super-object. IFUP is the area-weighted mean (same value
        on every row).
    """
    gdf = objects_gdf.copy()

    # L_max — longest axis of minimum rotated rectangle (metres)
    gdf["L_max"] = gdf.geometry.apply(_max_object_length)

    # AreaCl per class-SO (km²)
    area_cl = gdf.groupby([so_col, class_col])["AreaO"].sum().rename("AreaCl")
    gdf = gdf.merge(area_cl, on=[so_col, class_col], how="left")

    # Obstruction coefficient per object
    gdf["O_c"] = gdf[class_col].map(obstruction_map).fillna(0.0)

    # Contribution of each object: L_max · AreaCl · O_c
    gdf["contrib"] = gdf["L_max"] * gdf["AreaCl"] * gdf["O_c"]

    # SO area from district polygons (km²)
    so_area = pd.DataFrame({
        "CUDIS": districts_gdf[so_col],
        "AreaSO": districts_gdf.geometry.area / 1e6,
    })

    # Sum contributions per SO
    so_contrib = (
        gdf.groupby(so_col)["contrib"]
        .sum()
        .reset_index()
        .rename(columns={so_col: "CUDIS"})
    )

    result = so_area.merge(so_contrib, on="CUDIS", how="left")
    result["contrib"] = result["contrib"].fillna(0.0)

    # IFU per SO
    result["IFU"] = result["contrib"] / result["AreaSO"]

    # IFUP — area-weighted mean across all SOs
    total_area = result["AreaSO"].sum()
    if total_area > 0:
        ifup_val = (result["IFU"] * result["AreaSO"]).sum() / total_area
    else:
        ifup_val = np.nan
    result["IFUP"] = ifup_val

    return result[["CUDIS", "IFU", "IFUP"]]
