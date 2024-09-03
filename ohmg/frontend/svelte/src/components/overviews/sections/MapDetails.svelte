<script>
    import Question from 'phosphor-svelte/lib/Question';
    import Link from '@components/base/Link.svelte';
    import {getModal} from '@components/base/Modal.svelte';
    import DownloadSectionModal from "../modals/ItemDownloadSectionModal.svelte";
    import SessionList from "../../lists/SessionList.svelte";

    export let CONTEXT;
    export let MAP;
    export let SESSION_SUMMARY;
    export let ANNOTATION_SETS = [];

</script>

<DownloadSectionModal id={"download-section-modal"} />
<section>
    <h3 style="margin-top:5px;">Map Details</h3>
    <Link href="https://loc.gov/item/{MAP.identifier}" external={true}>View item in LOC collection</Link>
    <table>
        <tr>
            <td>Title</td>
            <td>Sanborn Map of {MAP.title}</td>
        </tr>
        <tr>
            <td>Year</td>
            <td>{MAP.year}</td>
        </tr>
        <tr>
            <td>Locale</td>
            <td><Link href="/{MAP.locale.slug}">{MAP.locale.display_name}</Link></td>
        </tr>
    </table>
    <h3>Contributors & Attribution</h3>
    <div class="non-table-section">
        <p>
        {#if MAP.progress.loaded_pages == MAP.progress.total_pages}
        {MAP.progress.loaded_pages} of {MAP.progress.total_pages} sheet{#if MAP.progress.total_pages != 1}s{/if} loaded by <Link href={MAP.loaded_by.profile}>{MAP.loaded_by.name}</Link> - {MAP.loaded_by.date}<br>
        {/if}
        {SESSION_SUMMARY.prep_ct} sheet{#if SESSION_SUMMARY.prep_ct != 1}s{/if} prepared{#if SESSION_SUMMARY.prep_ct > 0}&nbsp;by 
        {#each SESSION_SUMMARY.prep_contributors as c, n}<Link href="/profile/{c.name}">{c.name}</Link> ({c.ct}){#if n != SESSION_SUMMARY.prep_contributors.length-1}, {/if}{/each}{/if}
        <br>
        {SESSION_SUMMARY.georef_ct} georeferencing session{#if SESSION_SUMMARY.georef_ct != 1}s{/if}{#if SESSION_SUMMARY.georef_ct > 0}&nbsp;by 
        {#each SESSION_SUMMARY.georef_contributors as c, n}<Link href="/profile/{c.name}">{c.name}</Link> ({c.ct}){#if n != SESSION_SUMMARY.georef_contributors.length-1}, {/if}{/each}{/if}
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
    <h3>Work History</h3>
    <div>
        <SessionList {CONTEXT} FILTER_PARAM={`map=${MAP.identifier}`} showResource={false} paginate={true} limit={"100"}/>
    </div>
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