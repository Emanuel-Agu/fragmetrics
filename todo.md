# fragmetrics — TODO

## Design principles

- Every metric should be accompanied by clear dataviz (Jonas's suggestion)
- Consistent color palette and map style across all notebooks

## Notebooks

- [~] **01_fragmentation_with_SO** — Tutorial 1: fragmentation analysis with super-objects
  - [x] Proper intersection of objects with district boundaries (not centroid join)
  - [x] Area & Perimeter metrics at object, class, and super-object levels
  - [x] Validate area/perimeter results against `reference/expected_results/`
  - [x] Shape metrics
  - [x] Aggregation metrics
  - [ ] Diversity metrics
  - [ ] Contrast metrics
- [ ] **02_fragmentation_no_SO** — Tutorial 2: fragmentation analysis without super-objects
  - Whole study area treated as a single super-object
  - Compare class-level results with Tutorial 1
- [ ] **03_multitemporal** — Tutorial 3: multi-temporal change analysis
  - Two-date comparison (T1 vs T2)
  - Growth classification: infilling, edge-expansion, outlying (LEI)
  - Concentric circle and sector analysis from centre point
  - Change rate, change proportion, centroid displacement
- [ ] **04_validation** — Systematic comparison of all our results vs IndiFrag expected outputs

## Package (`src/fragmetrics/metrics/`)

- [x] `area_perimeter.py` — Area, Perim, PerimT, DC, DU, TM, DB, dimB, LPF, IFUP (10/10 done)
- [x] `shape.py` — DF, DFP, IF, RMPA
- [x] `aggregation.py` — Nob, DO, DEP, DEM, TEM, COHE, IS, GC, CU, C
- [ ] `diversity.py` — NCl, DSHAN, USHAN, SIMP, DD, IFFR, IFFA
- [ ] `contrast.py` — RCB at object, class, and super-object levels
- [ ] `multitemporal.py` — LEI, MEI, AWMEI, LUC, CP, RC, change areas, concentric/sector
- [ ] `core.py` — FragmentationAnalysis orchestrator
- [ ] `utils.py` — concentric ring generator, sector generator, boundary helpers

## Tests & CI

- [x] Unit tests with synthetic geometries for implemented metric modules
- [x] Integration test: run pipeline on Valencia data, compare vs `reference/expected_results/`
- [x] GitHub Actions CI (`ruff` + `pytest` + `uv build`)

## Polish

- [x] README.md with project overview, install instructions, usage examples
- [ ] Add topics/tags on GitHub (`landscape-ecology`, `geopandas`, `urban-metrics`, etc.)
- [ ] Add sample output figures to README
