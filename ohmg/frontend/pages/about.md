---
page_title: About
header: About this site...
---

### Background

The first iteration of OldInsuranceMaps.net was made publicly available as LaHMG (Louisiana Historical Map Georeferencer) in early 2022 through a four-month pilot project, focusing on maps of Louisiana. This work formed the bulk my master's thesis at Louisiana State University: ["Creating a Public Space for Georeferencing Sanborn Maps: A Louisiana Case Study"](https://digitalcommons.lsu.edu/gradschool_theses/5641/).

Since then, I have worked hard to refactor, restructure, and streamline the platform, into what is now just called OldInsuranceMaps.net (I had hoped for a better name but one has yet to come along...). I am also slowly spinning out the software into a more generic georeferencing app called [OHMG](https://ohmg.dev) (Online Historical Map Georeferencer), because a lot of characteristics of what I had to build to facilitate crowdsourcing for this particular map collection can be applied to other georeferencing work as well.

Over the course of the project's development I have given a handful of presentations at conferences and the like:

- ["Mapping the turn of the Century with OHM and OldInsuranceMaps.net"](https://www.youtube.com/watch?v=rKkAzJr25YU) -- [slides](http://tiny.cc/sotmus23-ac)
	- State of the Map US, 2023. Presentation with Jeff Meyer of [OpenHistoricalMap](https://openhistoricalmap.org)
- ["Crowdsourced Georeferencing Sanborn Maps of Louisiana"](https://www.youtube.com/watch?v=WmxzfZFfChg&pp=ygUOYWRhbSBjb3ggbmFjaXM%3D) -- [slides](https://tiny.cc/nacis2022-ac)
	- NACIS, 2022 *this one has the most about the pilot project*
- ["Creating a Public Space for Georeferencing Sanborn Maps"](https://www.youtube.com/watch?v=g7agzL4G5q8) -- [slides](https://docs.google.com/presentation/d/10khtmm8TOkZpsWNo-Yfvip4HqXHhwrPycIJYsBg1mA4/edit?usp=sharing)
	- NACIS, 2021
- "Extending GeoNode to Support Historical Map Georeferencing" -- [slides](https://docs.google.com/presentation/d/e/2PACX-1vSwbTO3jKrwGFKwouZdPSWfQVB3sws8I7bdH_CiSoNTt3l3wefu3s50NAxXn4N7M9CkW09hf9xZh63j/pub?start=false&loop=false&delayms=3000)
	- GeoNode Developer Summit, 2020

### Acknowledgments

The platform is built from many different open source projects, and would not exist without all the hard work of the folks behind:

- [Django](https;//djangoproject.com)
- [OpenLayers](https://openlayers.org) & [ol-ext](https://viglino.github.io/ol-ext/)
- [Svelte](https://svelte.dev)
- [GDAL](https://gdal.org)
- [TiTiler](https://developmentseed.org/titiler)
- [GeoNode](https://geonode.org) (though no longer part of the codebase, GeoNode was the foundation of LaHMG in [its first iteration](https://github.com/mradamcox/ohmg/releases/tag/v0.0.0-lahmg)).

A special shoutout to other web georeferencing apps that have been inspirational through this development process: [MapWarper](https://mapwarper.net), [Allmaps](https://allmaps.org), [Virtuelles KartenForum](https://kartenforum.slub-dresden.de/), and [Georeferencer](https://georeferencer.com).

I'd also like to acknowledge [Historical Information Gatherers](https://historicalinfo.org) for carrying out the [massive scanning effort](http://www.historicalinfo.com/about-us/library-of-congress-digital-map-project/) that created the digital collection this site is based on.

### Credits

Software design and development: Adam Cox

Icons & Logo: [Alex Muravev](https://thenounproject.com/alex2900/) (via Noun Project), [Feather Icons](https://feathericons.com/), [Phosphor Icons](https://phosphoricons.com/)

All maps on this site are in the public domain, pulled from the Library of Congress [Sanborn Map Collection](https://loc.gov/collections/sanborn-maps).

All georeferencing work performed by [our contributors](/profiles). For each volume, a list of contributors appears at the bottom of the summary page.
