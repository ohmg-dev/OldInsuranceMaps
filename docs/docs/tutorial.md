# Alexandria, La. | 1900

This tutorial covers the entire process using the [Alexandria, La. | 1900](https://www.loc.gov/resource/g4014am.g032671900/?st=gallery) volume as an example.

The complete workflow is:

1. [Load the Volume](#loading-a-volume)
2. [Prepare the Documents](#prepare-the-documents)
3. [Georeference the prepared Documents](#georeference-the-prepared-documents)
4. [Create a Web Map from the Layers](#create-a-web-map-from-the-layers)
5. [Trim some of the Layers](#trim-some-of-the-layers)

Keep in mind that these steps are designed to facilitate a collaborative environment. While you *could* complete an entire volume in one session, you can also just do individual steps here and there, allowing others to fill in around. Georeferencing and trimming (3 & 5 above) are both iterative processes, so you can come back later to improve upon your own work, or someone else's.

<figure>
    <iframe height="400px;" style="max-width:700px; width:100%;" src="https://oldinsurancemaps.net/viewer/alexandria-la"></iframe>
    <figcaption>Alexandria, Louisiana in 1900. <a href="https://oldinsurancemaps.net/viewer/alexandria-la" target="_blank">web map detail</a></figcaption>
</figure>

The end result is a web map which can be <a href="https://oldinsurancemaps.net/maps/203/view" target="_blank">viewed in the site</a> or embedded with an `<iframe>` on any web page. Also, any of the individual layers can be used in other web maps or geospatial software (as WMS).

# Load the Volume

From the [Volumes page]("https://oldinsurancemaps.net"), we begin by finding the city and year we are interested in.

![Choosing Alexandria on the left reveals a list of all available volumes. Out of 11 total volumes, 6 are available to be loaded.](img/alex-search-volumes.png)

Selecting the 1900 volume, we are brought to the **volume summary** page.

![The volume summary presents an overview of the georeferencing progress across an entire volume.](img/alex-1900-before-load.png)

When we click **Load Sheets**, the files begin to load and are presented in the "Unprepared" section of the summary.

![2 of 6 sheets have been loaded.](img/alex-1900-two-loaded.png)

As the sheets load, you can click the refresh button (or reload the page) and newly loaded sheets will appear. After one sheet is ready, we can go ahead and prepare it. The other sheets will continue to load in the background.

![All 6 sheets have been loaded.](img/alex-1900-full-loaded.png)

# Prepare the Documents

The preparation step requires a judgment to be made as to whether
    
1. the sheet shows only **one area**, or
2. the sheet shows **multiple areas**
    
In the case of 1, then preparation just takes one button click and the sheet can be georeferenced immediately. In the case of 2, the sheet must be split into smaller pieces, so that each one can be georeferenced independently.

## Scenario 1 - No Split Needed

We'll click **prepare** on sheet 2, and we are brought to the splitting interface.

![This sheet only shows one area (there are no subdivisions), so it should not be split.](img/alex-1900-sheet-2-prepare.png)

In this case, all we need to do is click **No Split Needed**, and this sheet will be marked as "prepared". We'll be taken straight to the georeferencing interface.

For now, instead of georeferencing (which we'll do soon enough) let's return to the volume summary.

**back to document detail &rarr; Volume for this document**

or

**Content &rarr; Volumes &rarr; Alexandria 1900**

## Scenario 2 - Split

Now we'll click **prepare** on sheet 1.

![This sheet has three different sections.](img/alex-1900-sheet-1-prepare.png)

In this case, it's clear that the sheet has three different sections, delineated by **thick black lines**. We'll draw two "cut-lines" along the section boundaries, and a yellow preview will show us how the sheet will be divided up.

![With two cutlines drawn, yellow boundaries show the three new documents that will be made.](img/alex-1900-sheet-1-prepare-cutlines.png)

Once everything looks good, clicking **Split** will run the process, and redirect us to the **Georeference** tab in the document detail page.

![The Georeference tab shows the georeferencing actions that have been performed on this document.](img/alex-1900-sheet-1-doc-detail-during-split.png)

When the split is complete, we can see the new documents in this tab.

![Clicking the refresh button in the tab shows us the new documents made from the split.](img/alex-1900-sheet-1-doc-detail-after-split.png)

Once completed, we'll head back to the volume summary to check our progress.

![Volume summary with sheets 1 and 2 fully prepared.](img/alex-1900-1-2-prepared.png)

As expected, there are now 4 documents that are ready to be georeferenced, i.e. "prepared". The first three are the result of splitting sheet 1, and the fourth is sheet 2, which did not need to be split. We'll leave the 4 "unprepared" documents for now, and move on to georeferencing. 

# Georeference the Prepared Documents

Again, we'll start with sheet 2. Clicking **georeference &rarr;** brings us to the georeferencing interface.

![Sheet 2 is shown in the left-hand panel, while a web map is on the right, already zoomed to the general Alexandria area.](img/alex-1900-sheet-2-georeference.png)

We'll use street intersections as the basis for our control points. After we make 3 of them, a preview shows up and we can begin a closer inspection of our results.

![The control point is signified with an "x" symbol in each panel.](img/alex-1900-sheet-2-georeference-gcp-detail.png)

Looks pretty good! But if needed, we can click and drag either of these points closer to the center of the intersection.

Once we have 4 points, we can click **Save Control Points** to run the georeferencing process.

![The control point is signified with an "x" symbol in each panel.](img/alex-1900-sheet-2-georeference-4-gcps.png)

As with the Split process, we'll be brought to the **Georeference** tab in the document detail page.

![The georeference tab indicates that georeferencing is in progress.](img/alex-1900-sheet-1-doc-detail-during-georeference.png)

Once the process has completed (again, we can use the refresh button to get updates), we'll be shown list of all the control points we made.

![When georeferencing has completed, a list of all control points is shown.](img/alex-1900-sheet-1-doc-detail-after-georeference.png)

---

At this point, we can repeat the processes for all other sheets and documents in the volume. Keep in mind: some small pieces of Sanborn maps may be impossible to georeference if they only show a few buildings and don't have any present-day context to georeference them against.

Also, because these processes run in the background, once you are familiar with the system you'll find you can move through them quite quickly.

# Create a Web Map from the Layers

Once most of the documents have been georeferenced, you can create a web map to combine them into an interactive mosaic.

Go to the search page, and use the search facets to find the appropriate layers. In this case, we'll use:

- **Regions**: `Alexandria`
- **Date begins after**: `1900`
- **Date ends before**: `1901`

This will return all of the layers we have georeferenced so far.

![Use the search facets on the left to find the layers you will add to your map.](img/search-alex-1900.png)

With the layers narrowed down, select each one with the <i class="fa fa-plus"></i> button, and then click "Create a Map"

![With one or more layers selected, you can create a new web map from this interface.](img/search-alex-1900-selected.png)

You will be brought to a new web map. You can arrange the layer order as needed. Make sure you Save As and give the map a descriptive title before leaving the page!

![Adjust layer order in the left-hand panel, change basemaps in the bottom left corner, and save options and catalog in the top right menu.](img/new-map-alex-1900.png)

If more documents are georeferenced after you have already made this map, use the **Catalog** to find and add those layers to this map.

# Trim Some of the Layers

Once we create the web map, we may find that adjacent layers overlap and obscure each other. Consider the example below, where the layer on the left covers up the edge of the layer on the right.

![Two georeferenced layers are shown on top of an aerial imagery basemap. The left layer overlaps the right layer.](img/alex-untrim-example.jpg)

To reduce this overlap, we can trim the edges of the left layer by creating a mask. This is just a shape that will cause everything outside of it to be clipped away. The result can look like this:

![The left layer has been trimmed to create a seamless mosaic](img/alex-trim-example.jpg)

There is no need to trim _every_ layer, so it's best to approach this process in an as needed manner.