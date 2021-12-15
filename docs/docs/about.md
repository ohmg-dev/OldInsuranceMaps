# About

## Tech Overview

This platform is the result of a few layered applications. The primary application is [GeoNode](https://geonode.org), an open source geospatial content management system. On top of GeoNode are two custom applications, [georeference](#georeference) and [loc_insurancemaps](#loc_insurancemaps).

### GeoNode

GeoNode is built from (or otherwise incorporates) the following major components:

[Django](https://django.org) &#8226; 
[GeoServer](https://geoserver.org) &#8226; 
[PostgreSQL](https://postgresql.org)/[PostGIS](https://postgis.net) &#8226;
[OpenLayers](https://openlayers.org) &#8226;
[RabbitMQ](https://rabbitmq.com)

For more, visit [GeoNode's documentation](https://docs.geonode.org).

### georeference

This application is designed as a generic GeoNode extension that allows one to georeference Document resources (i.e. turn them into Layer resources). On the front end, it provides the following urls:

```python
/split/<doc_id>			# the splitting interface for a Document
/georeference/<doc_id>	# the georeferencing interface for a Document
/trim/<layer_alternate>	# the trimming interface for a Layer
/progress/<doc_id>		# the georeferencing progress page for a Document
```

All interfaces are written using [Svelte](https://svelte.dev). [Mapserver](https://mapserver.org) is used to generate the WMS preview used during georeferencing from a VRT that is dynamically updated with ground control points.

Earlier iterations of this extension incorporated [IIIF](https://iiif.org) and work from Bert Spaan at [allmaps.org](https://allmaps.org). Some remnants of this work remain, and reincorporating IIIF may be good a direction for future work.

### loc_insurancemaps

This application creates database models and scaffolding to support the structure of the LOC Sanborn Map collection. On the front end, it provides the following urls:

```python
/						# the home page with branding, etc.
/loc/<volume_doi>		# overall progress page for sheets of a volume
/loc/volumes			# access point to load and explore volumes
```

Svelte is used for the page interfaces. A custom GeoNode theme was created as well to manage general color branding, etc.

### Icons

Icons in `loc-insurancemaps` are by [Alex Muravev](https://thenounproject.com/alex2900/) and [Olga](https://thenounproject.com/olgamur_2015/) from the [Noun Project](https://thenounproject.com).

### Documentation

See footer.