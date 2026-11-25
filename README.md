# fragmetrics

[![DOI](https://zenodo.org/badge/1156564374.svg)](https://doi.org/10.5281/zenodo.19635208)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python ≥3.10](https://img.shields.io/badge/python-%E2%89%A53.10-blue.svg)](pyproject.toml)

Open-source landscape fragmentation metrics in Python, built on `geopandas` and `shapely`, with no ArcGIS/`arcpy` dependency. The metrics are those defined in the [IndiFrag](https://doi.org/10.4995/raet.2015.3476) toolbox by Marta Sapena and Luis A. Ruiz (Universitat Politècnica de València); see [Relationship to IndiFrag](#relationship-to-indifrag).

Metrics are computed at three levels — **Object** (polygon), **Class** (land-use class within a super-object), **Super-Object** (district / administrative unit) — across five groups plus multi-temporal change.

## Status

| Group | Module | Metrics | Status |
|---|---|---|---|
| Area & perimeter | `metrics.area_perimeter` | Area, Perim, PerimT, DC, DU, TM, DB, dimB, LPF, IFUP | ✅ implemented |
| Shape | `metrics.shape` | DF, DFP, IF, RMPA | ✅ implemented |
| Aggregation | `metrics.aggregation` | Nob, DO, DEP, DEM, TEM, COHE, IS, GC, CU, C | 🚧 planned |
| Diversity | `metrics.diversity` | NCl, DSHAN, USHAN, SIMP, DD, IFFR, IFFA | 🚧 planned |
| Contrast | `metrics.contrast` | RCB (O / Cl / SO) | 🚧 planned |
| Multi-temporal | `metrics.multitemporal` | LEI, MEI, AWMEI, LUC, CP, RC, concentric/sector | 🚧 planned |

Validation against IndiFrag's published Valencia expected outputs lives in `reference/expected_results/`.

## Install

```bash
git clone https://github.com/Emanuel-Agu/fragmetrics.git
cd fragmetrics
pip install -r requirements.txt
pip install -e .
```

Requires Python ≥ 3.10 with `geopandas`, `shapely` 2.x, `pandas`, `numpy`, `scipy`, `matplotlib`, `pyproj`.

## Quickstart

```python
import geopandas as gpd
from fragmetrics.metrics import area_perimeter, shape

# Load a Land-Use/Land-Cover polygon layer and the administrative districts
# (super-objects) that partition the study area. Both must share the same
# projected CRS in metres.
objects = gpd.read_file("data/valencia/ES003L2_VALENCIA_UA2006_Revised_Clipped_to_Core.shp")
districts = gpd.read_file("data/valencia/VALENCIA_DISTR.shp")

# Object-level area/perimeter
objects = area_perimeter.object_metrics(objects)
objects = shape.object_metrics(objects)

# Class-level (one row per class × super-object)
cl_ap = area_perimeter.class_metrics(objects, class_col="CLASS", so_col="CUDIS")
cl_sh = shape.class_metrics(objects, class_col="CLASS", so_col="CUDIS")

# Super-object level (one row per district)
so_ap = area_perimeter.super_object_metrics(objects, districts,
                                            class_col="CLASS", so_col="CUDIS")
```

See [`notebooks/01_fragmentation_with_SO.ipynb`](notebooks/01_fragmentation_with_SO.ipynb) for an end-to-end tutorial on the Valencia urban atlas data, including maps of every implemented metric.

## Data conventions

- Input geometries must be in a **projected CRS in metres**.
- Output areas are reported in **km²**, perimeters in **km** (IndiFrag convention).
- `IFUP` requires an `obstruction_map: dict[class_id → coefficient ∈ [0, 1]]` reflecting how obstructive each land-use class is.

## Example data & validation reference

- `data/valencia/` contains the Valencia 2006 Urban Atlas LULC layer, district boundaries, and the city-centre reference point used in the IndiFrag tutorial — enough to run the notebooks end-to-end (see [`data/valencia/README.md`](data/valencia/README.md)).
- `reference/expected_results/` holds the published numeric outputs of the IndiFrag tutorial used here for validation (see [`reference/README.md`](reference/README.md)). The IndiFrag software distribution and manuals are not redistributed in this repository; obtain them directly from the [CGAT–UPV Software Portal](https://cgat.webs.upv.es/software/).

## Relationship to IndiFrag

`fragmetrics` is a separate Python package with its own design: metrics are functions organized by level (object, class, super-object) that operate on `geopandas` data frames.

- **Metric definitions.** The metric names, definitions and conventions (levels; areas in km², perimeters in km) follow the IndiFrag metrics reference (Sapena & Ruiz 2015). Please cite IndiFrag alongside this package; see [Citing](#citing).
- **Validation.** Results are checked against the published outputs of the IndiFrag tutorial (Valencia, Urban Atlas 2006), kept in `reference/expected_results/`.
- **Code.** `fragmetrics` is an independent Python implementation with no code copied from IndiFrag.
- **Third-party files.** `data/valencia/` and `reference/expected_results/` are third-party data/validation materials and are not covered by this package's MIT license.
- **AI-assisted development.** Code and documentation were developed by the author with the assistance of Anthropic's Claude (via Claude Code), as recorded in the commit history. The author reviewed, tested, and validated all code and outputs against the reference results.

## Citing

If you use `fragmetrics` in academic work, please cite both this package (see [`CITATION.cff`](CITATION.cff)) and the original IndiFrag toolbox paper:

> Sapena, M., & Ruiz, L. A. (2015). Descripción y extracción de índices de fragmentación urbana: la herramienta IndiFrag. *Revista de Teledetección*, (43), 77–90. [doi:10.4995/raet.2015.3476](https://doi.org/10.4995/raet.2015.3476)

If you use multi-temporal metrics, also cite:

> Sapena, M., & Ruiz, L. A. (2015). Analysis of urban development by means of multi-temporal fragmentation metrics from LULC data. *ISPRS Archives*, XL-7/W3, 1411–1418. [doi:10.5194/isprsarchives-XL-7-W3-1411-2015](https://doi.org/10.5194/isprsarchives-XL-7-W3-1411-2015)

## License

MIT — see [`LICENSE`](LICENSE).

`fragmetrics` is an independent package and is not affiliated with or endorsed by the IndiFrag authors or Universitat Politècnica de València.
