"""
fragmetrics - Open-source landscape fragmentation metrics in Python (metric definitions follow IndiFrag; Sapena & Ruiz 2015).

A Python implementation (geopandas + shapely, no ArcGIS/arcpy) of the
fragmentation metrics defined in the IndiFrag v2.1 toolbox by Sapena & Ruiz
(Universitat Politècnica de València). Cite IndiFrag alongside fragmetrics
when you use these metrics (see CITATION.cff).

Metrics are organised in five groups at three levels (Object, Class, Super-Object):
  - Area and perimeter
  - Shape
  - Aggregation
  - Diversity
  - Contrast
Plus multi-temporal change metrics.

References:
  Sapena, M., & Ruiz, L. A. (2015). Descripción y extracción de índices de
  fragmentación urbana: la herramienta IndiFrag. Revista de Teledetección, 43,
  77-90. https://doi.org/10.4995/raet.2015.3476
  Metric definitions and names follow the IndiFrag metrics reference
  (IndiFrag v2.1, Universitat Politècnica de València).
  Sapena, M., & Ruiz, L. A. (2015). Analysis of urban development by means of
  multi-temporal fragmentation metrics from LULC data. ISPRS Archives,
  XL-7/W3, 1411-1418. https://doi.org/10.5194/isprsarchives-XL-7-W3-1411-2015
"""
