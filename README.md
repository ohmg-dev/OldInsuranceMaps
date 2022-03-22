# Louisiana Historical Map Georeferencer (LaHMG)

This app is a customized deployment of [GeoNode](https://geonode.org), built from [geonode-project](https://github.com/GeoNode/geonode-project). It is a crowdsourcing platform for georeferencing maps of Louisiana from the Library of Congress [Sanborn Maps Collection](https://loc.gov/collections/sanborn-maps).

- **Main Site:** [oldinsurancemaps.net](https://oldinsurancemaps.net)
- **Documentation:** [docs.oldinsurancemaps.net](https://docs.oldinsurancemaps.net)

---

You can browse volumes of fire insurance maps from the home page.

![Homepage](./loc_insurancemaps/static/img/homepage-031922.jpg)

---

Each volume's summary page has an interactive Map Overview showing all of the sheets that have been georeferenced so far.

![Volume Summary - Map Overview](./loc_insurancemaps/static/img/vsummary-031922.jpg)

Each volume's summary page also lists the progress and georeferencing stage of each sheet.

![Volume Summary - Georeferencing Overview](./loc_insurancemaps/static/img/vsummary2-031922.jpg)

---

The georeferencing process generally consists of three operations.

Document preparation (sometimes they must be split into multiple pieces):

![Splitting interface](./docs/docs/img/alex-1900-sheet-1-prepare-cutlines.png)

Ground control point creation (these are used to warp the document into a geotiff):

![Georeferencing interface](./docs/docs/img/alex-1900-sheet-2-georeference-4-gcps.png)

Trimming the edges off of a layer (optional, useful for handling overlapping sheets):

![Trimming interface](./docs/docs/img/trim-interface.png)

---

Please don't hesitate to [open a ticket](https://github.com/mradamcox/loc-insurancemaps/issues/new/choose) if you have trouble with the site or find a bug.
