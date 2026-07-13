
# Downloads & web services

Historical map content can be accessed in a number of different ways and used in many different applications. Throughout the platform you will find places to download or link to:

1. Individual layers that have been georeferenced
    - Find these within a map's **Georeferenced** section: https://oldinsurancemaps.net/map/sanborn03375_001#georeferenced
2. Unified mosaics made from multiple layers
    - Find these within a map's **Mosaic** &rarr; **Derivatives** section: https://oldinsurancemaps.net/map/sanborn03375_001#mosaic

!!! warning

    When downloading or otherwise accessing maps, please keep in mind that **OldInsuranceMaps.net provides no guarantee as to the accuracy of georeferenced content.**

!!! important

    Over time, someone may come along and improve the georeferencing on a layer, or update multimask boundaries and regenerated a mosaic. When this happens the original file is deleted and a new one is created. Because many of the endpoints described below contain the actual filename, **tile service links in 3rd-party integrations may need to be updated after the source layer or mosaic has been updated**.

## Downloadable geotiffs (COGs)

OIM relies heavily on [cloud optimized geotiffs](https://cogeo.org/), or "COGs", and you can download these files at any time and easily use them directly in software like QGIS or ArcGIS Desktop. All COGs use JPEG compression in order to keep file sizes manageable.

## Tile services

OIM provides service endpoints that can be used in many different applications. The particular service endpoint you use will largely depend on where you are trying to use it, as not all applications support all types of endpoints.

Generally speaking, XYZ tiles are the most widely supported, TileJSON is a superset spec that wraps an XYZ tile endpoint with some extra information, and WMS is an older standard still in use in many applications.

OIM uses TiTiler to dynamically produce tiled services from the same source COG files that you can download as described above.

### XYZ tiles

XYZ tiles are a very widely supported standard supported by most geospatial software and mapping applications. Here is more info for how to use these URLs in desktop software like [QGIS](https://docs.qgis.org/3.22/en/docs/user_manual/managing_data_source/opening_data.html#using-xyz-tile-services) and [ArcGIS](https://esribelux.com/2021/04/16/xyz-tile-layers-in-arcgis-platform/), as well as web mapping applications like [Leaflet](https://leafletjs.com/reference.html#tilelayer), [OpenLayers](https://openlayers.org/en/latest/examples/xyz.html), [Mapbox/Maplibre GL JS](https://maplibre.org/maplibre-gl-js-docs/example/map-tiles/), [ArcGIS Online](https://doc.arcgis.com/en/arcgis-online/create-maps/add-layers-from-url.htm#ESRI_SECTION1_13A68145A4F94A338AB2002AD5F9844D), and [OpenHistoricalMap (iD Editor)](https://learnosm.org/en/beginner/id-editor/#configuring-the-background-layer).

!!! note

    Some mosaics will also have an **Static XYZ Tileset** available. This is a static, pre-rendered tileset that you can download, unpack, and host on your own infrastructure. It is different from the XYZ tiles endpoints in that it does not rely on any dynamic tiling service, like TiTiler.

### TileJSON

[TileJSON](https://github.com/mapbox/tilejson-spec) is a useful spec that wraps an XYZ endpoint with a few other pieces of information.

Currently, this is the most reliable OIM-provided endpoint to use because while the underlying XYZ url which may change (as described above), the TileJSON url itself will not change. However, TileJSON is not as widely supported as XYZ tiles.


## IIIF Georeference Extension

For each layer and mosaic you can also access a collection of the georeferencing information formatted as the [IIIF Georeference Extension](https://iiif.io/api/extension/georef/). This annotation will includes the IIIF URLs from the source resources in the Library of Congress and when you open it in Allmaps Viewer, the tiles will be coming directly from LOC and being warped in the browser according to control points and masks created in OIM. Learn more in this slideshow: [creating IIIF georeference annotations](https://docs.google.com/presentation/d/18FRpq1Lcz3T7WincZNRvTjdL87ULy1bU68BCxr425dk/edit?usp=sharing).