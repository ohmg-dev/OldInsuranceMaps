<script>
    import Link from '@components/base/Link.svelte';
    import OpenModalButton from '@components/base/OpenModalButton.svelte';
    import DownloadSectionModal from "../modals/ItemDownloadSectionModal.svelte";

    export let ITEM;
    export let mosaicUrl = null;
    export let ohmUrl = null;
</script>

<DownloadSectionModal id={"download-section-modal"} />
<section>
    <h3 style="margin-top:5px;">Map Details</h3>
    <Link href="https://loc.gov/item/{ITEM.identifier}" external={true}>View item in LOC collection</Link>
    <table>
        <tr>
            <td>Title</td>
            <td>Sanborn Map of {ITEM.title}</td>
        </tr>
        <tr>
            <td>Year</td>
            <td>{ITEM.year}</td>
        </tr>
        <tr>
            <td>Locale</td>
            <td><Link href="/{ITEM.locale.slug}">{ITEM.locale.display_name}</Link></td>
        </tr>
    </table>
    <h3>Contributors & Attribution</h3>
    <div class="non-table-section">
        <p>
        {#if ITEM.sheet_ct.loaded == ITEM.sheet_ct.total}
        {ITEM.sheet_ct.loaded} of {ITEM.sheet_ct.total} sheet{#if ITEM.sheet_ct.total != 1}s{/if} loaded by <Link href={ITEM.loaded_by.profile}>{ITEM.loaded_by.name}</Link> - {ITEM.loaded_by.date}<br>
        {/if}
        {ITEM.sessions.prep_ct} sheet{#if ITEM.sessions.prep_ct != 1}s{/if} prepared{#if ITEM.sessions.prep_ct > 0}&nbsp;by 
        {#each ITEM.sessions.prep_contributors as c, n}<Link href="{c.profile}">{c.name}</Link> ({c.ct}){#if n != ITEM.sessions.prep_contributors.length-1}, {/if}{/each}{/if}
        <br>
        {ITEM.sessions.georef_ct} georeferencing session{#if ITEM.sessions.georef_ct != 1}s{/if}{#if ITEM.sessions.georef_ct > 0}&nbsp;by 
        {#each ITEM.sessions.georef_contributors as c, n}<Link href="{c.profile}">{c.name}</Link> ({c.ct}){#if n != ITEM.sessions.georef_contributors.length-1}, {/if}{/each}{/if}
        <br>
        <strong>Credit Line: Library of Congress, Geography and Map Division, Sanborn Maps Collection.</strong>
            </p>
    </div>
    <div class="header-bar">
        <h3>Download & Web Services</h3>
        <OpenModalButton modalId="download-section-modal" />
    </div>
    <p style="font-size:.9em;"><em>
        Only layers that have been trimmed in the <strong>MultiMask</strong> will appear in the mosaic. You can access untrimmed layers individually through the <strong>Georeferenced</strong> section.
    </em></p>
    <table>
        <tr>
            <td>XYZ Tiles URL</td>
            <td>
                {#if mosaicUrl}
                <pre style="margin:0;">{mosaicUrl}</pre>
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
        <tr>
            <td>GeoTIFF</td>
            <td>
                {#if ITEM.urls.mosaic_geotiff}
                <Link href={ITEM.urls.mosaic_geotiff} title="Download mosaic geotiff file">Download GeoTIFF (direct download)</Link>
                {:else}
                n/a
                {/if}
            </td>
        </tr>
    </table>
</section>

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

    .non-table-section {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 4px;
    }

    /* caption {
        width: 100%;
        font-size: .9em;
    }

    table caption {
        color: #333;
        text-align: left;
    } */

    td {
        padding: 4px;
    }

    /* th {
        font-variant: small-caps;
        font-size: .85em;
        padding: 4px;
    } */

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

    /* button.thumbnail-btn {
        border: none;
        background: none;
        cursor: zoom-in;
    } */
</style>