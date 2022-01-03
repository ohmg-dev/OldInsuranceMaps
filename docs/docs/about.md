# Project Background

This platform is the basis of my MS Geography thesis at Louisiana State University. The impetus behind this project was, most generally, two-fold:

- Create a platform for collaborative map georeferencing
- Provide open access to existing online map archives

Neither of these ideas are new, but I was especially inspired by the idea of the archival commons[^1] [^2] and wanted to build something with elements of that concept in mind&mdash;open access, public curation, and extensibility. Building around the LOC Sanborn collection was a natural fit, as it is a massive collection of archival content in the public domain.

Technologically, this platform is the result of a few layered applications. The base application is the geospatial content management system [GeoNode](https://geonode.org), on top of which two custom applications were built, [georeference](#georeference-app) and [loc_insurancemaps](#loc_insurancemaps-app).

I have presented about the project a couple of times during the development process:

**"Extending GeoNode to Support Historical Map Georeferencing"**

[GeoNode Virtual Summit - 2020](https://summit.geonode.org/schedule/#session-110) ~ [slides](https://docs.google.com/presentation/d/e/2PACX-1vSwbTO3jKrwGFKwouZdPSWfQVB3sws8I7bdH_CiSoNTt3l3wefu3s50NAxXn4N7M9CkW09hf9xZh63j/pub?start=false&loop=false&delayms=3000)

**"Creating a Public Space for Georeferencing Sanborn Maps"**

[NACIS 2021 - Oklahoma City](https://nacis2021.sched.com/event/lXOu/cartographic-resources) ~ [video](https://www.youtube.com/watch?v=g7agzL4G5q8) ~ [slides](https://docs.google.com/presentation/d/10khtmm8TOkZpsWNo-Yfvip4HqXHhwrPycIJYsBg1mA4/edit?usp=sharing)

## GeoNode

[GeoNode](https://geonode.org) is an open source geospatial content management system that can act as a geospatial data portal, allowing organizations to publish and curate their spatial datasets. It has been implemented by non-profit and governmental enitities [around the world](https://geonode.org/gallery/).

GeoNode is built from the following major open source projects:

[Django](https://django.org) &#8226; 
[GeoServer](https://geoserver.org) &#8226; 
[PostgreSQL](https://postgresql.org)/[PostGIS](https://postgis.net) &#8226;
[OpenLayers](https://openlayers.org)

Choosing GeoNode as the base for this georeferencing platform provided the following advantages, to name a few:

- A robust open source tech stack to build from
- A content management system (CMS) for spatial and non-spatial datasets
- Content integration with a geospatial data server (GeoServer)
- User registration, account, and permissions management
- Interactive web map authoring by users
- An active developer community to join

## `georeference` app

The first custom piece added to GeoNode is the `georeference` app, which is designed as a standalone GeoNode extension. In theory, anyone can add this app to their own GeoNode installation (please [open a ticket](https://github.com/mradamcox/loc-insurancemaps/issues) if you are interested in doing so).

This app facilitates the actual georeferencing steps, i.e. the process by which Documents are turned into Layers. It consists of three user-accessible tool interfaces, as well as a new summary tab in the Layer and Document detail pages and links in the search results page. A quick summary of these tools follows, but detailed documentation can be foundin the [Georeferencing Process](/georeferencing-process) section.

### Split

```python
/split/<document_id>		# the splitting interface for a Document
```

This interface allows users to "split" a document into smaller pieces, which is necessary if the document has two different maps on it (as each must be georeferenced separately). If a Document is split, it is set as `metadata_only` so it no longer appears in search results (though it can still be accessed through the georeference tab of one of its child documents).

If a document does not need to be split, this evaluation can be recorded and it will be ready for georeferencing.

### Georeference

```python
/georeference/<document_id>	# the georeferencing interface for a Document
```

### Trim

```python
/trim/<layer_alternate>	    # the trimming interface for a Layer
```

### Overview tab

In the Document detail and Layer detail pages a new tab is added labled **Georeference**. This tab provides a summary of all the georeferencing actions that have been performed on that Document or Layer. You can also access the next step in the georeferencing process for the resource from this tab.

### Search result links

In the search results pages, a list of links are added to each item, allowing quick access to any of the above pages. These links are deactivated if that action is not possible for the item. For example, the link for Trimming will not be accessible until a Layer exists (i.e. the Document has been georeferenced).

<hr>

All interfaces are written using [Svelte](https://svelte.dev). [Mapserver](https://mapserver.org) is used to generate the WMS preview used during georeferencing from a VRT that is dynamically updated with ground control points.

!!! note
    Earlier iterations of this app incorporated [IIIF](https://iiif.org) were meant to build from Bert Spaan's work at [allmaps.org](https://allmaps.org). Remnants of this approach have been moved into a separate app called `iiif_support`, and could be reincorporated in the future.

## `loc_insurancemaps` app

This application creates database models and scaffolding to support the acquisition and management of content from the LOC Sanborn Map collection. On the front end, it provides the following urls:

```python
/						# the home page with branding, etc.
/loc/<volume_doi>		# overall progress page for sheets of a volume
/loc/volumes			# access point to load and explore volumes
```

All interfaces are written using [Svelte](https://svelte.dev). A custom GeoNode theme was created as well to manage general color branding, etc.

Icons in this app are by [Alex Muravev](https://thenounproject.com/alex2900/) and [Olga](https://thenounproject.com/olgamur_2015/) from the [Noun Project](https://thenounproject.com).

## Documentation

This documentation is built with [MkDocs](https://mkdocs.org) using [CustomMill](https://github.com/Siphalor/mkdocs-custommill), and hosted on [ReadTheDocs](https://readthedocs.com). See page footer for more information.

[^1]:
    Anderson, Scott, and Robert Allen. 2009. “Envisioning the Archival Commons.” The American Archivist 72 (2): 383–400. https://doi.org/10.17723/aarc.72.2.g54085061q586416.
[^2]:
    Eveleigh, Alexandra. 2014. “Crowding out the Archivist? Locating Crowdsourcing within the Broader Landscape of Participatory Archives.” In Crowdsourcing Our Cultural Heritage, 211–29. Ashgate Publishing Farnham.
