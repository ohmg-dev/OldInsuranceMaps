# Connecting to the LOC

The approach taken here downloads scanned map images from the LOC through their [JSON API](https://libraryofcongress.github.io/data-exploration/).

# Structure of the Sanborn Collection 

When the Sanborn Map company originally published these maps, all content for a given city in a given year was released in a single edition. However, in large cities like New Orleans one edition may actually comprise multiple volumes, and in the Library of Congress collection each of these volumes is stored as a separate item. Thus, the term "volume" is used here&mdash;even though it is almost always synonymous with *edition* or *atlas*&mdash;because it more closely reflects the structure of the LOC collection.

We have chosen **Volume** as the highest level of grouping of historical maps in this project. Each volume has one or more sheets that become **[Documents](#documents)** when the volume is loaded.


# Loading Volumes

=== "Basic concept"
	To begin working on a volume, we must copy all of its scanned map files from the Libary of Congress digital collection into our system.

=== "Tell me more..."
	This loading process acquires image files through the LOC's [JSON API](https://www.loc.gov/apis/json-and-yaml/), and registers them as Documents in this content management system. Metadata like regional keywords and dates are also ingested and attached to the Documents at this time, to facilite facet searches and other lookups in the [Documents search page](https://oldinsurancemaps.net/documents).

From the [Volumes page]("https://oldinsurancemaps.net"), we begin by finding the city and year we are interested in.

[image of Alexandria volumes]

Entering the 1892 volume, we can either preview the contents in the Library of Congress IIIF viewer, or click **Load Sheets** to begin the georeferencing process.

[show image with one sheet loaded]

You can click the refresh button (or reload the page) and sheets will be added to the display as they are loaded. After one sheet is ready, we can go ahead and prepare it. The other sheets will continue to load in the background.

## Why isn't my city listed?
    
Unfortunately, if a city does not appear in the "Start a new volume" list, that means there is no item in the LOC collection for it. However, do check for old names of your city, or the names of adjacent communinities that may have combined with yours over the years.

## Why are some volumes in the list grayed out?

This means the volume does exist in the LOC collection, but we have not made it
available in this project. For now, we wanted to prove wide geographic and temporal coverage throughout Louisiana while also limiting the amount of disk space needed.

We devised the following criteria to determine which volumes to include:

- Include the earliest edition for every community, regardless of date.
- Include any editions published through 1910 for all communities outside of New Orleans.
- Include only the earliest edition of New Orleans (1885, published in two volumes).

![Mamou: 1919 available (earliest edition), 1927 and 1946 unavailable (published after 1910)](img/volumes-grayed-out.png)

Applied across the state, these criteria produce 266 volumes covering 138 communities, with a combined sheet count of 1499.

!!! note
    If you are very interested in georeferencing a volume that is not currently available, please [get in touch](mailto:acox42@lsu.edu)!