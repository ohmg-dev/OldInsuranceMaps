<script>
    import InfoModalButton from "../buttons/InfoModalButton.svelte";
    import Link from "../base/Link.svelte";

    export let CONTEXT;
    export let MAP;
    export let LAYERSETS;
</script>

<div class="level" style="margin-top:10px;">
    <div class="level-left">
        <p>
        Only layers that have been trimmed in the <strong>MultiMask</strong> will appear in the downloadable mosaic
        files. You can access individual layers through the <strong>Georeferenced</strong> section.
        </p>
    </div>
    <div class="level-right">
        <InfoModalButton modalId="download-section-modal" />
    </div>
</div>
{#each LAYERSETS as ls}
{#if ls.layers.length >= 1}
    <h4>{ls.name} ({ls.layers.length} layer{ls.layers.length > 1 ? 's' : ''})</h4>
    <table>
    <tbody>
        {#if ls.mosaic_cog_url}
        <tr>
            <td>TileJSON</td>
            <td>
            <Link
                href="{CONTEXT.site_url}map/{MAP.identifier}/{ls.id}/tilejson"
                title="Get TileJSON"
                external={true}>{CONTEXT.site_url}map/{MAP.identifier}/{ls.id}/tilejson</Link
            >
            </td>
        </tr>
        <tr>
            <td>OpenHistoricalMap editor</td>
            <td>
            {#if ls.mosaic_cog_url}
                <Link
                href="{CONTEXT.site_url}map/{MAP.identifier}/{ls.id}/ohm"
                title="Open mosaic in OpenHistoricalMap iD Editor"
                external={true}>{CONTEXT.site_url}map/{MAP.identifier}/{ls.id}/ohm</Link
                >
            {:else}
                n/a
            {/if}</td
            >
        </tr>
        <tr>
            <td>Download Cloud-Optimized GeoTIFF</td>
            <td>
            {#if ls.mosaic_cog_url}
                <Link href={ls.mosaic_cog_url} title="Download mosaic geotiff file"
                >{CONTEXT.site_url}map/{MAP.identifier}/{ls.id}/cog</Link
                >
            {:else}
                n/a
            {/if}
            </td>
        </tr>
        {/if}
        <tr>
        <td>IIIF Georef AnnotationPage (JSON)</td>
        <td>
            <Link
            href="{CONTEXT.site_url}iiif/mosaic/{MAP.identifier}/{ls.id}/?trim=true"
            title="View full AnnotationPage JSON for this mosaic"
            external={true}>{CONTEXT.site_url}iiif/mosaic/{MAP.identifier}/{ls.id}/?trim=true</Link
            >
        </td>
        </tr>
        <tr>
        <td>Allmaps</td>
        <td>
            <Link
            href="https://viewer.allmaps.org/?url={encodeURIComponent(
                `${CONTEXT.site_url}iiif/mosaic/${MAP.identifier}/${ls.id}/?trim=true`,
            )}"
            title="Open mosaic in Allmaps Viewer"
            external={true}
            >https://viewer.allmaps.org/?url={encodeURIComponent(
                `${CONTEXT.site_url}iiif/mosaic/${MAP.identifier}/${ls.id}/?trim=true`,
            )}</Link
            >
        </td>
        </tr>
    </tbody>
    </table>
{/if}
{/each}