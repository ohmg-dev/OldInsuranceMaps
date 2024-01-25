<script>
    import Modal from "@components/base/Modal.svelte";
    import Link from "@components/base/Link.svelte";

    export let id;
    export let ohmUrl = null;
</script>

<Modal id={id}>
	<h3>Mosaic Downloads & Web Services</h3>
    <p>After multiple pages have been georeferenced and a multimask has been created, a single mosaic can be generated from all of this item's layers. Once created, the mosaic can be downloaded as a GeoTIFF, or integrated as a web service into any common GIS or web GIS software via the <strong>XYZ tiles URL</strong>.</p>
    <p></p>
    <h4>How to use XYZ tiles in desktop software</h4>
    <ul>
        <li><Link href="https://docs.qgis.org/3.22/en/docs/user_manual/managing_data_source/opening_data.html#using-xyz-tile-services" external=true>QGIS</Link></li>
        <li><Link href="https://esribelux.com/2021/04/16/xyz-tile-layers-in-arcgis-platform/" external=true>ArcGIS</Link></li>
    </ul>
    <h4>How to use XYZ tiles on the web</h4>
    <ul>
        <li><Link href="https://leafletjs.com/reference.html#tilelayer" external=true>Leaflet</Link></li>
        <li><Link href="https://openlayers.org/en/latest/examples/xyz.html" external=true>OpenLayers</Link></li>
        <li><Link href="https://maplibre.org/maplibre-gl-js-docs/example/map-tiles/" external=true>Mapbox/MapLibre GL JS</Link></li>
        <li><Link href="https://doc.arcgis.com/en/arcgis-online/create-maps/add-layers-from-url.htm#ESRI_SECTION1_13A68145A4F94A338AB2002AD5F9844D" external=true>ArcGIS Online</Link></li>
        <li><Link href="https://learnosm.org/en/beginner/id-editor/#configuring-the-background-layer" external=true>OpenHistoricalMap (iD Editor)</Link></li>
        {#if ohmUrl}
        <ul>
            <li><Link href="https://learnosm.org/en/beginner/id-editor/#configuring-the-background-layer" external=true>Direct link to this mosaic in (iD Editor)</Link></li>
        </ul>
        {/if}
    </ul>
</Modal>