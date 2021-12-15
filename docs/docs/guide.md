# Guide

For this guide we'll walk through the example of [Alexandria, Louisiana | 1892](https://loc.gov/item/sanborn03267_002).

For clarity, certain words are capitalized herein where they refer to objects that are central to the platform structure and are used throughout the user interface.

## Process Overview

The complete workflow goes like this:

1. [Load the Volume](#loading-a-volume)
2. [Prepare the Documents](#preparing-documents) (some sheets contain must be "split" into separate Documents)
3. [Georeference the prepared Documents](#georeferencing-documents) (create ground control points)
4. [Trim the georeferenced Layers](#trimming-layers) ("trim" the edges of a sheet to allow seamless mosaics)
5. [Create a new Web Map](#creating-web-maps) (put all of the layers into a single web map and share!)

The breakdown of these steps facilitates a collaborative and iterative workflow. While you *could* complete the entire workflow in one session, it is easier to just do one or two tasks here and there. Georeferencing and trimming (3 & 4 above) both iterative processes, so you can come back later to improve upon your past work, or that of another user.

## Loading a Volume

=== "Basic concept"
	To begin working on a volume, we must copy all of its scanned map files from the Libary of Congress digital collection into our system.

=== "Tell me more..."
	This loading process acquires image files through the LOC's [JSON API](https://www.loc.gov/apis/json-and-yaml/), and registers them as Documents in this content management system. Metadata like regional keywords and dates are also ingested and attached to the Documents at this time, to facilite facet searches and other lookups in the [Documents search page](https://oldinsurancemaps.net/documents).

## Preparing Documents

=== "Basic concept"
	Before a Document can be georeferenced, it must be visually evaluated to determine whether it contains more than one part of town in it. If it does, each section must be split into separate documents.

=== "Tell me more..."
	When an image is georeferenced, as you'll see below, pixel coordinates are 

## Georeferencing Documents

=== "Basic concept"
	"Georeferencing" is the process that is needed to overlay a scanned historical map onto a modern web map, and it must be performed for each Document individually.

=== "Tell me more..."
	Georeferencing works by using "ground control points" to embed geospatial information into an image file and turn it into a geosptial dataset. A ground control point consists of two coordinate pairs: one pair that represents the XY pixel location on the document, and a corresponding latitude/longitude coordinate that represents a point on earth.

Once 

## Trimming Layers

=== "Basic concept"
	If you want, you can trim the edges of a border layer away, so that adjacent sheets on the same web map don't obscure each other.

=== "Tell me more..."
	This process is accomplished by creating a polygon "mask" that is used to crop extraneous layer content. These mask coordinates are written into an alternate layer style that is set as the new default for the Layer. This approach preserves the original style, which allows users switch back to the full style if they want to see the entire image in a web map.



## Creating Web Maps

=== "Basic concept"
	Users can author their own Web Maps, and add whichever layers they want to them. This is most obviously useful for aggregating all of the layers for a single city in a single year, but you could also combine layers from different years.

=== "Tell me more..."
	Creating Web Maps is a core GeoNode functionality, and this project only scratches the surface of what these maps can do. Please see the [GeoNode documentation](https://docs.geonode.org/en/master/usage/managing_maps/index.html) to learn more. *Note - In default GeoNode parlance, what we refer to here as "Web Maps" are simply "Maps".*