# Alexandria, La. | 1900

This tutorial will walk through the entire process using the maps of [Alexandria, Louisiana from 1900](https://www.loc.gov/resource/g4014am.g032671900/?st=gallery) as an example.

The complete workflow goes like this:

1. [Load the Volume](#loading-a-volume)
2. [Prepare the Documents](#preparing-documents)
3. [Georeference the prepared Documents](#georeferencing-documents)
5. [Create the Web Map from the Layers](#creating-web-maps)
4. [Trim some of the Layers](#trimming-layers)

The end result is a web map which can be <a href="https://oldinsurancemaps.net/maps/203/view" target="_blank">viewed in the site</a> or embedded on any web page as show below.

<figure>
    <iframe height="400px;" style="max-width:700px; width:100%;" src="https://oldinsurancemaps.net/maps/203/embed"></iframe>
    <figcaption>Alexandria, Louisiana in 1900. <a href="https://oldinsurancemaps.net/maps/203" target="_blank">web map detail</a></figcaption>
</figure>

Keep in mind that these steps are designed to facilitate a collaborative and iterative environment. While you *could* complete an entire volume in one session, you can also just do individual steps here and there, allowing others to fill in around.

Also, georeferencing and trimming (3 & 5 above) are both iterative processes, so you can come back later to improve upon your own work, or someone else's.

# Load the Volume

From the [Volumes page]("https://oldinsurancemaps.net"), we begin by finding the city and year we are interested in.

[image of Alexandria volumes]

Entering the 1900 volume, we can either preview the contents in the Library of Congress IIIF viewer, or click **Load Sheets** to begin the georeferencing process.

[show image with one sheet loaded]

You can click the refresh button (or reload the page) and sheets will be added to the display as they are loaded. After one sheet is ready, we can go ahead and prepare it. The other sheets will continue to load in the background.

# Preparing Documents

On Sanborn maps, different parts of a town were often combined into the same map sheet in order to save space. This is easy to recognize because a thick black line was always used to delinate these areas. Consider the image below, the sheet 1 of Alexandria, 1900.

[image of the splitting interface with sheet 1]

In this case, there are 4 different sections. In the splitting interface, you will draw lines across the map document to determine how it will be split. Notice that the lines don't have to start or end exactly at the border; they can extend beyond. The yellow preview shows the shape of the new parts that will be made.

[image with all lines made]

Click **Split** and you will be brought to the progress overview page for this Document. Once the splitting has completed, you'll see all four new pieces.

Now we'll return to the Volume overview page. Use your browser's Back button, or go to the top nav menu **Content > Volumes** and select the volume from the list.

[image of the volume with sheet 1 prepared]

The "unprepared" sheet 1 has been turned into four "prepared" documents.

### *But what if the sheet doesn't need to be split?*

We'll now prepare sheet 3.

[splitting interface with sheet 3]

As you can see, there are no thick black lines dividing this map up; it does not need to be split. Simply click **No Split Needed** to mark this document as "prepared".

# Georeferencing Documents

Back in the volume summary, there is now 1 unprepared sheet, and 5 prepared Documents. On closer inspection, you may notice that the Document 

# Creating Web Maps

=== "Basic concept"
	Users can author their own Web Maps, and add whichever layers they want to them. This is most obviously useful for aggregating all of the layers for a single city in a single year, but you could also combine layers from different years.

=== "Tell me more..."
	Creating Web Maps is a core GeoNode functionality, and this project only scratches the surface of what these maps can do. Please see the [GeoNode documentation](https://docs.geonode.org/en/master/usage/managing_maps/index.html) to learn more. *Note - In default GeoNode parlance, what we refer to here as "Web Maps" are simply "Maps".*

# Trimming Layers
