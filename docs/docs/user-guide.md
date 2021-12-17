# Process Overview

The complete workflow goes like this:

1. [Load the Volume](#loading-a-volume)
2. [Prepare the Documents](#preparing-documents)
3. [Georeference the prepared Documents](#georeferencing-documents)
4. [Trim the georeferenced Layers](#trimming-layers)
5. [Add the georeferenced Layers to a Web Map](#creating-web-maps)

These steps are designed to facilitate a collaborative and iterative environment. While you *could* complete an entire volume in one session, you can also just do individual steps here and there, allowing others to fill in around.

Georeferencing and trimming (3 & 4 above) are both iterative processes, so you can come back later to improve upon your past work, or that of another user.

<hr>

To illustrate the steps, we'll walk through the process with [Alexandria, Louisiana | 1892](https://loc.gov/item/sanborn03267_002).

For clarity, certain words are capitalized herein where they refer to objects that are central to the platform structure and are used throughout the user interface.


## Loading a Volume

=== "Basic concept"
	To begin working on a volume, we must copy all of its scanned map files from the Libary of Congress digital collection into our system.

=== "Tell me more..."
	This loading process acquires image files through the LOC's [JSON API](https://www.loc.gov/apis/json-and-yaml/), and registers them as Documents in this content management system. Metadata like regional keywords and dates are also ingested and attached to the Documents at this time, to facilite facet searches and other lookups in the [Documents search page](https://oldinsurancemaps.net/documents).

From the [Volumes page]("https://oldinsurancemaps.net"), we begin by finding the city and year we are interested in.

[image of Alexandria volumes]

Entering the 1892 volume, we can either preview the contents in the Library of Congress IIIF viewer, or click **Load Sheets** to begin the georeferencing process.

[show image with one sheet loaded]

You can click the refresh button (or reload the page) and sheets will be added to the display as they are loaded. After one sheet is ready, we can go ahead and prepare it. The other sheets will continue to load in the background.

## Preparing Documents

=== "Basic concept"
	Before a Document can be georeferenced, it must be visually evaluated to determine whether it contains more than one part of town in it. If it does, each of these parts must be split into separate Documents.

=== "Tell me more..."
	When an image is georeferenced, as you'll see below, control points are made that link pixel coordinates on the image with latitude/longitude coordinates on the earth. This means that a set of control points must only be linked to a specific geographic area.

On Sanborn maps, different parts of a town were often combined into the same map sheet in order to save space. These is easy to recognize because a thick black line was always used to delinate these areas. Consider the image below, the sheet 1 of Alexandria, 1892.

[image of the splitting interface with sheet 1]

In this case, there are 4 different sections. In the splitting interface, you will draw lines across the map document to determine how it will be split. Notice that the lines don't have to start or end exactly at the border; they can extend beyond. The yellow preview shows the shape of the new parts that will be made.

[image with all lines made]

Click **Split** and you will be brought to the progress overview page for this Document. Once the splitting has completed, you'll see all four new pieces.

Now we'll return to the Volume overview page. Use your browser's Back button, or go to the top nav menu **Content > Volumes** and select the volume from the list.

[image of the volume with sheet 1 prepared]

The "unprepared" sheet 1 has been turned into four "prepared" documents.

##### *But what if the sheet doesn't need to be split?*

We'll now prepare sheet 3.

[splitting interface with sheet 3]

As you can see, there are no thick black lines dividing this map up; it does not need to be split. Simply click **No Split Needed** to mark this document as "prepared".

## Georeferencing Documents

=== "Basic concept"
	"Georeferencing" is the process that is needed to overlay a scanned historical map onto a modern web map, and it must be performed for each Document individually.

=== "Tell me more..."
	Georeferencing works by using "ground control points" to embed geospatial information into an image file and turn it into a geosptial dataset. A ground control point consists of two coordinate pairs: one pair that represents the XY pixel location on the document, and a corresponding latitude/longitude coordinate that represents a point on earth.

Back in the volume summary, there is now 1 unprepared sheet, and 5 prepared Documents. One closer inspection, you may notice that the Document 

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