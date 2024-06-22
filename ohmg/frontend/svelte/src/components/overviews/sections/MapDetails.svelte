<script>
    import Question from 'phosphor-svelte/lib/Question';
    import Link from '@components/base/Link.svelte';
    import {getModal} from '@components/base/Modal.svelte';
    import DownloadSectionModal from "../modals/ItemDownloadSectionModal.svelte";

    export let VOLUME;
    export let ANNOTATION_SETS = [];

</script>

<DownloadSectionModal id={"download-section-modal"} />
<section>
    <h3 style="margin-top:5px;">Map Details</h3>
    <Link href="https://loc.gov/item/{VOLUME.identifier}" external={true}>View item in LOC collection</Link>
    <table>
        <tr>
            <td>Title</td>
            <td>Sanborn Map of {VOLUME.title}</td>
        </tr>
        <tr>
            <td>Year</td>
            <td>{VOLUME.year}</td>
        </tr>
        <tr>
            <td>Locale</td>
            <td><Link href="/{VOLUME.locale.slug}">{VOLUME.locale.display_name}</Link></td>
        </tr>
    </table>
    <h3>Contributors & Attribution</h3>
    <div class="non-table-section">
        <p>
        {#if VOLUME.sheet_ct.loaded == VOLUME.sheet_ct.total}
        {VOLUME.sheet_ct.loaded} of {VOLUME.sheet_ct.total} sheet{#if VOLUME.sheet_ct.total != 1}s{/if} loaded by <Link href={VOLUME.loaded_by.profile}>{VOLUME.loaded_by.name}</Link> - {VOLUME.loaded_by.date}<br>
        {/if}
        {VOLUME.sessions.prep_ct} sheet{#if VOLUME.sessions.prep_ct != 1}s{/if} prepared{#if VOLUME.sessions.prep_ct > 0}&nbsp;by 
        {#each VOLUME.sessions.prep_contributors as c, n}<Link href="{c.profile}">{c.name}</Link> ({c.ct}){#if n != VOLUME.sessions.prep_contributors.length-1}, {/if}{/each}{/if}
        <br>
        {VOLUME.sessions.georef_ct} georeferencing session{#if VOLUME.sessions.georef_ct != 1}s{/if}{#if VOLUME.sessions.georef_ct > 0}&nbsp;by 
        {#each VOLUME.sessions.georef_contributors as c, n}<Link href="{c.profile}">{c.name}</Link> ({c.ct}){#if n != VOLUME.sessions.georef_contributors.length-1}, {/if}{/each}{/if}
        <br>
        <strong>Credit Line: Library of Congress, Geography and Map Division, Sanborn Maps Collection.</strong>
            </p>
    </div>
    <div class="header-bar">
        <h3>Mosaic Download & Web Services</h3>
        <button class="is-icon-link" on:click={() => {getModal('download-section-modal').open()}} ><Question /></button>
    </div>
    <p style="font-size:.9em;"><em>
        Only layers that have been trimmed in the <strong>MultiMask</strong> will appear in the mosaic. You can access untrimmed layers individually through the <strong>Georeferenced</strong> section.
    </em></p>
    {#each ANNOTATION_SETS as annoSet}
    {#if annoSet.annotations.length > 1}
        <h4>{annoSet.name}</h4>
        {#if annoSet.mosaicUrl}
        <table>
            <tr>
                <td>XYZ Tiles URL</td>
                <td>
                    {#if annoSet.mosaicUrl}
                    <pre style="margin:0;">{annoSet.mosaicUrl}</pre>
                    {:else}
                    n/a
                    {/if}
                </td>
            </tr>
            <tr>
                <td>OHM</td>
                <td>
                    {#if annoSet.ohmUrl}
                    <Link href="{annoSet.ohmUrl}" title="Open mosaic in OHM Editor" external={true}>Open in OpenHistoricalMap iD editor</Link>
                    {:else}
                    n/a
                    {/if}</td>
            </tr>
            <tr>
                <td>GeoTIFF</td>
                <td>
                    {#if annoSet.mosaic_cog_url}
                    <Link href={annoSet.mosaic_cog_url} title="Download mosaic geotiff file">Download GeoTIFF (direct download)</Link>
                    {:else}
                    n/a
                    {/if}
                </td>
            </tr>
        </table>
        {:else}
        <p><em>Mosaic not available for this layer set.</em></p>
        {/if}
    {/if}
    {/each}
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