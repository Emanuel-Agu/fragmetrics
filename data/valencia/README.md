# Valencia Validation Dataset

This directory contains the Valencia 2006 example layers used in the tutorials
and automated validation tests:

- `ES003L2_VALENCIA_UA2006_Revised_Clipped_to_Core.shp` — Land-use/land-cover
  polygons derived from Copernicus / EEA Urban Atlas 2006 (EPSG:3035),
  reclassified as in the IndiFrag tutorial.
- `VALENCIA_DISTR.shp` — Valencia administrative districts (super-objects,
  EPSG:25830).
- `VALENCIA_Centre_Point.shp` — City-centre reference point (EPSG:25830).
- `class_mapping.csv` — Lookup table mapping Urban Atlas 2006 codes to the
  aggregated `CLASS` IDs (1–8).

## Attribution & License

The underlying vector layers originate from the Copernicus Land Monitoring
Service / European Environment Agency (Urban Atlas 2006) as packaged for the
IndiFrag tutorial by Marta Sapena and Luis A. Ruiz (UPV,
[CGAT–UPV Software Portal](https://cgat.webs.upv.es/software/)). These data
files are included solely for reproducible examples and validation, and are
**not** covered by this package's MIT license.
