# Introduction

One of the best ways to engage with historical maps is to visually compare them against other maps, like current satellite imagery. Doing so requires the old maps to be *georeferenced*, a process that embeds latitude and longitude coordinates in the image and allows it to be overlaid directly on other spatial layers.

<figure>
    <iframe height="400px;" style="max-width:700px; width:100%;" src="https://oldinsurancemaps.net/maps/203/embed"></iframe>
    <figcaption>Alexandria, Louisiana in 1900, web map created through this project. Can you find the prize fighting ring? <a href="https://oldinsurancemaps.net/maps/203/view" target="_blank">View in LaHMG</a>
</figure>

The purpose of this project is to facilitate that georeferencing process, in a curated way based on the Library of Congress [Sanborn Maps Collection](https://www.loc.gov/collections/sanborn-maps/about-this-collection/). This collection holds historical fire insurance maps covering over 10,000 U.S. communities. This project is focused on Louisiana.

# Sanborn Maps - Briefly

The Sanborn Map Company surveyed and mapped American cities from the late 1860's through the 1950's, creating city atlases and selling them to insurance companies on a subscription basis. The extensive details they recorded for each building&mdash;commercial use, construction materials, exact locations of heat sources, to name but a few&mdash;provided insurance companies with the information they needed to geographically visualize and balance their risk.

Map production had begun to wind down in the 1950s, but usefulness of the collection as a historical reference (far beyond its original purpose) was already recognized. In all, the company mapped over 12,000 American communities, generally returning to each one every 5-7 years to create a full update. The result is an unparalled cartographic record of urban development in the U.S., and an archive with much potential.

In recent years, the advancement of geospatial and web technology has provided new ways to re-engage with these maps. For example, some companies sell access to their own georeferenced mosaics of the maps ([EDR](https://edrnet.com/introducing-sanborn-viewer/), [ERIS](https://www.erisinfo.com/eris-xplorer/), [FIMo](http://www.historicalinfo.com/fimo/)), some cities have free viewers ([Boston](https://atlascope.leventhalmap.org), [Bozeman](https://www.arcgis.com/apps/webappviewer/index.html?id=f4cf486b4d7f4988aa589e7dd989f5e9), [Milwaukee](http://webgis.uwm.edu/agsl/sanborn/)), and digital history projects use georeferenced maps as foundational materials ([Reconstructing Bloomington](https://storymaps.arcgis.com/stories/f38fd8915aa14f4e99b96455dcdad49e), [What the Tulsa Race Massacre Destroyed](https://www.nytimes.com/interactive/2021/05/24/us/tulsa-race-massacre.html), [Homestead Hebrew Maps](https://maps.homesteadhebrews.com/)).

# Structure of the Sanborn Collection 

When the Sanborn Map company originally published these maps, all content for a given city in a given year was released in a single edition. However, in large cities like New Orleans one edition may actually comprise multiple volumes, and in the Library of Congress collection each of these volumes is stored as a separate item.

Thus, we use **volume** as the highest level of grouping of historical maps. Each volume has one or more sheets, and when a user starts ("loads") a volume, those sheets are registered as [documents](https://oldinsurancemaps.net/documents) in the system.