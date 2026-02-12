"""
indifrag - Open-source implementation of IndiFrag fragmentation metrics.

Replicates the IndiFrag v2.1 toolbox (Sapena, UPV) using geopandas + shapely
instead of ArcGIS/arcpy.

Metrics are organised in five groups at three levels (Object, Class, Super-Object):
  - Area and perimeter
  - Shape
  - Aggregation
  - Diversity
  - Contrast
Plus multi-temporal change metrics.
"""
