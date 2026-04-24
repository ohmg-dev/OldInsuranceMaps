<script>
    import Link from "../base/Link.svelte";

    export let CONTEXT;
    export let MAP;
    export let LAYERSETS;

    const orderedCategories = [
        "main-content",
        "key-map",
    ]

    const orderedLayersets = []

    orderedCategories.forEach((cat) => {
        LAYERSETS.forEach((ls) => {
            if (cat == ls.id) {
                orderedLayersets.push(ls)
            }
        })
    })

    LAYERSETS.forEach((ls) => {
        if (!orderedCategories.includes(ls.id)) {
            orderedLayersets.push(ls)
        }
    })
</script>

<div>
    <p>
    Once layers have been trimmed in the <strong>MultiMask</strong>, a background process can be run
    to combine them into a single mosaic file, which serves as a basis for downloads and web services.
    If you see <strong>n/a</strong> below, the mosaic has not yet been created. You can still access 
    individual layers through the <strong>Georeferenced</strong> section, or view the mosaic in Allmaps
    (powered by IIIF).
    </p>
</div>
{#each orderedLayersets as ls}
{#if ls.layers.length >= 1}
    <h4 class="dl-title">{`${ls.name} (${ls.layers.length} layer${ls.layers.length > 1 ? 's' : ''})`}</h4>
    <dl>
    <dt>TileJSON</dt>
    <dd>
        {#if ls.mosaic_cog_url}
        <Link
            href="{CONTEXT.site_url}map/{MAP.identifier}/{ls.id}/tilejson"
            title="Get TileJSON"
            external={true}>{CONTEXT.site_url}map/{MAP.identifier}/{ls.id}/tilejson</Link
        >
        {:else}
        n/a
        {/if}
    </dd>
    <dt>OpenHistoricalMap iD editor</dt>
    <dd>{#if ls.mosaic_cog_url}
        <Link
            href="{CONTEXT.site_url}map/{MAP.identifier}/{ls.id}/ohm"
            title="Open mosaic in OpenHistoricalMap iD Editor"
            external={true}>{CONTEXT.site_url}map/{MAP.identifier}/{ls.id}/ohm</Link
            >
        {:else}
        n/a
        {/if}</dd>
    <dt>Cloud-Optimized GeoTIFF</dt>
    <dd>
    {#if ls.mosaic_cog_url}
        <Link
            href={ls.mosaic_cog_url}
            title="Download mosaic geotiff file"
            download={true}
        >{CONTEXT.site_url}map/{MAP.identifier}/{ls.id}/cog</Link
        >
    {:else}
        n/a
    {/if}
    </dd>
    <dt>IIIF Georef AnnotationPage (JSON)</dt>
    <dd>
        <Link
        href="{CONTEXT.site_url}iiif/mosaic/{MAP.identifier}/{ls.id}/?trim=true"
        title="View full AnnotationPage JSON for this mosaic"
        external={true}>{CONTEXT.site_url}iiif/mosaic/{MAP.identifier}/{ls.id}/?trim=true</Link
        >
    </dd>
    <dt>Allmaps</dt>
    <dd>
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
    </dd>
    </dl>
{/if}
{/each}

<style>
    h4.dl-title {
        margin: 0;
        padding: .4em;
        color: white;
        background-color: var(--bulma-scheme-main);
    }
    dl {
        background-color: #ffffff;
    }
    dt, dd {
        padding-top: .25em;
        padding-bottom: .25em;
    }
    dt {
        font-weight: 700;
        font-size: .85em;
        background-color: #f6f6f6;
        padding-left: .5em;
    }
    dd {
        padding-left: 1em;
    }
</style>