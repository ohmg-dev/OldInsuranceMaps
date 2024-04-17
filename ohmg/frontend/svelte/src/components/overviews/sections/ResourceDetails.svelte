<script>
    import {getCenter} from 'ol/extent';
    import { makeTitilerXYZUrl } from '@lib/utils';
    import Link from '@components/base/Link.svelte';
    import OpenModalButton from '@components/base/OpenModalButton.svelte';
    import ResourceDownloadSectionModal from "../modals/ResourceDownloadSectionModal.svelte";
    import IconButton from '@components/base/IconButton.svelte';

    export let CONTEXT;
    export let RESOURCE;

    let xyzUrl;
    let ohmUrl;
    let ll;
    let doubleEncodedXYZUrl;
    let jpegUrl;
    let cogUrl;
    let gcpsGeojsonUrl;
    let gcpsPointsUrl;
    if (RESOURCE.type == "layer") {
        // this is a layer Resource
        jpegUrl = RESOURCE.document.urls.image;
        cogUrl = RESOURCE.urls.cog;
        xyzUrl = makeTitilerXYZUrl({
            host: CONTEXT.titiler_host,
            url: RESOURCE.urls.cog,
        });
        doubleEncodedXYZUrl = makeTitilerXYZUrl({
            host: CONTEXT.titiler_host,
            url: RESOURCE.urls.cog,
            doubleEncode: true,
        });
        ll = getCenter(RESOURCE.extent);
        gcpsGeojsonUrl = `/mrm/${RESOURCE.slug}?resource=gcps-geojson`;
        gcpsPointsUrl = `/mrm/${RESOURCE.slug}?resource=points`;
    } else {
        // this is a document resource
        jpegUrl = RESOURCE.urls.image;
    }
    if (RESOURCE.layer) {
        // this is a document resource that DOES have a layer (i.e. has been georeferenced)
        cogUrl = RESOURCE.layer.urls.cog;
        gcpsGeojsonUrl = `/mrm/${RESOURCE.layer.slug}?resource=gcps-geojson`;
        gcpsPointsUrl = `/mrm/${RESOURCE.layer.slug}?resource=points`;
        xyzUrl = makeTitilerXYZUrl({
            host: CONTEXT.titiler_host,
            url: RESOURCE.layer.urls.cog,
            doubleEncode: true,
        });
        doubleEncodedXYZUrl = makeTitilerXYZUrl({
            host: CONTEXT.titiler_host,
            url: RESOURCE.layer.urls.cog,
            doubleEncode: true,
        });
        ll = getCenter(RESOURCE.layer.extent);
    }
    if (doubleEncodedXYZUrl && ll) {
        ohmUrl = `https://www.openhistoricalmap.org/edit#map=16/${ll[1]}/${ll[0]}&background=custom:${doubleEncodedXYZUrl}`
    }
</script>

<ResourceDownloadSectionModal id={"download-section-modal"} />

<h3 style="margin-top:5px;">Resource Details</h3>
<table>
    <tr>
        <td>Title</td>
        <td>Sanborn Map of {RESOURCE.title}</td>
    </tr>
    <tr>
        <td>Status</td>
        <td>{RESOURCE.status}</td>
    </tr>
</table>
<div class="header-bar">
    <h3>Downloads & Web Services</h3>
    <OpenModalButton modalId="download-section-modal" />
</div>
<table>
    <tr>
        <td>Image</td>
        <td>
            {#if jpegUrl}
            <Link href="{jpegUrl}" title="Download original JPEG">JPEG</Link>
            {/if}
            {#if cogUrl}
            &bullet;
            <Link href={cogUrl} title="Download georeferenced layer as GeoTIFF">GeoTIFF</Link>
            {/if}
        </td>
    </tr>
    <tr>
        <td>Ground Control Points</td>
        <td>
            {#if gcpsGeojsonUrl}
            <Link href={gcpsGeojsonUrl} title="Download GCPs in GeoJSON format" download={`${RESOURCE.slug}.geojson`}>GeoJSON</Link>
            <!--&bullet;
            <Link href={gcpsPointsUrl} title="Download GCPs in .points format (QGIS)" download={`${RESOURCE.slug}.points`}>.points</Link>-->
            {:else}
            n/a
            {/if}
        </td>
    </tr>
    <tr>
        <td>XYZ Tiles URL</td>
        <td>
            {#if xyzUrl}
            <pre style="margin:0;">{xyzUrl}</pre>
            {:else}
            n/a
            {/if}
        </td>
    </tr>
    <tr>
        <td>OHM</td>
        <td>
            {#if ohmUrl}
            <Link href="{ohmUrl}" title="Open mosaic in OHM Editor" external={true}>Open in OpenHistoricalMap iD editor</Link>
            {:else}
            n/a
            {/if}</td>
    </tr>
</table>

<style>
    table {
        width: 100%;
        border: 1px solid #ddd;
        border-radius: 4px;
        display: block;
        overflow-x: auto;
        white-space: nowrap;
    }

    .header-bar {
        display:flex;
        justify-content:space-between;
    }

    /* .non-table-section {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 4px;
    }

    table caption {
        color: #333;
        text-align: left;
    } */

    td {
        padding: 4px;
    }

    /* tr:nth-child(even) {
        background-color: #f6f6f6;
    }

    tr:nth-child(odd) {
        background-color: #ffffff;
    } */
    td {
        background-color: #ffffff;
        width: 100%;
    }
    td:first-child {
        background-color: #f6f6f6;
        font-weight: 800;
        width: 150px;
    }
</style>