<script>
    import { getFromAPI } from "../../lib/requests";
    import { submitPostRequest } from "../../lib/requests";
    import Link from "../base/Link.svelte";
    import ModalConfirm from '../base/ModalConfirm.svelte';
    import { openModal } from '../base/Modal.svelte';

    import ModalInfo from '../base/ModalInfo.svelte';
    import LoadingEllipsis from '../shared/LoadingEllipsis.svelte';
    import DerivativeDD from '../shared/DerivativeDD.svelte';
    import MosaicStatus from '../shared/tags/MosaicStatus.svelte';
    import ArrowsClockwise from 'phosphor-svelte/lib/ArrowsClockwise';

    export let CONTEXT;
    export let mapId;

    console.log(CONTEXT)
    console.log( CONTEXT.user.perms.includes("core.queue_mosaic_cog"))

    let layersets = []
    let loading = false;

    const orderedCategories = [
        "main-content",
        "key-map",
    ]

    const initLayersets = () => {
        loading = true;
        layersets = [];
        getFromAPI(`/api/beta2/layersets/?map=${mapId}`, CONTEXT.ohmg_api_headers, (response) => {
            const orderedLayersets = []
            // first force the most important layersets to the top of the list
            orderedCategories.forEach((cat) => {
                response.forEach((ls) => {
                    if (cat == ls.id) {
                        orderedLayersets.push(ls)
                    }
                })
            })
            // then add all the rest
            response.forEach((ls) => {
                if (!orderedCategories.includes(ls.id)) {
                    orderedLayersets.push(ls)
                }
            })
            layersets = orderedLayersets.map(i => {
                i.iiifAnnoUrl = `${CONTEXT.site_url}iiif/mosaic/${mapId}/${i.id}/?trim=true`
                i.allmapsUrl = `https://viewer.allmaps.org/?url=${encodeURIComponent(i.iiifAnnoUrl)}`
                i.ohmUrl = i.mosaic_cog_url ? `${CONTEXT.site_url}map/${mapId}/${i.id}/ohm` : null;
                i.tileJsonUrl = i.mosaic_cog_url ? `${CONTEXT.site_url}map/${mapId}/${i.id}/tilejson` : null;
                i.dynamicXyzUrl = i.mosaic_cog_url ? `${CONTEXT.titiler_host}/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png?url=${encodeURIComponent(i.mosaic_cog_url)}` : null;
                i.wmsUrl = i.mosaic_cog_url ? `${CONTEXT.titiler_preview_host}/cog/wms/?LAYERS=${encodeURIComponent(i.mosaic_cog_url)}&VERSION=1.1.1` : null;
                i.masksDateDisplay = i.multimask_date ? new Date(i.multimask_date*1000).toLocaleString() : null;
                i.xyzStaticArchiveURL = i.xyz_tiles_url ? `${i.xyz_tiles_url}/archive.tar.gz` : null;
                i.xyzStaticTilesURL = i.xyz_tiles_url ? `${i.xyz_tiles_url}/{z}/{x}/{y}.png` : null;

                i.enableCogQueueBtn = CONTEXT.user.perms.includes("core.queue_mosaic_cog")
                i.cogQueueBtnTitle = CONTEXT.user.perms.includes("core.queue_mosaic_cog") ?
                    "Click to queue COG build" : "You do not have permission for this action"

                i.cogStale = false;
                if (i.latest_cog_job && i.latest_cog_job.stage == "completed") {
                    i.cogStale = i.multimask_date ? i.latest_cog_job.date_started < i.multimask_date : false
                }

                // same thing now but for the XYZ tileset build
                i.xyzQueueBtnTitle = "Click to queue XYZ tileset build";
                i.enableXyzQueue = true;
                if (!i.latest_cog_job || i.cogStale) {
                    i.enableXyzQueue = false;
                    i.xyzQueueBtnTitle = "COG must be up-to-date before tileset can be built";
                }
                if (!CONTEXT.user.perms.includes("core.queue_mosaic_xyz")) {
                    i.enableXyzQueue = false;
                    i.xyzQueueBtnTitle = "You do not have permission for this action";
                }

                
                return i
            });
            loading = false;
        });
    }
    initLayersets()

    function handleQueueRequestResponse(response) {
        openModal('modal-job-submitted')
        initLayersets()
    }

    let layersetToQueueForCog;
    function submitQueueRequest(action) {
        submitPostRequest(
            '/layerset/',
            CONTEXT.ohmg_post_headers,
            action,
            {
                'map-id': mapId,
                category: layersetToQueueForCog,
            },
            handleQueueRequestResponse,
        );
    }
</script>

<ModalInfo id="modal-job-submitted">
    <p>Job submitted. You can track its completion on the <Link href="/jobs/" external={true}>jobs page</Link>.</p>
</ModalInfo>
<ModalConfirm id="modal-confirm-cog-queue"
    yesAction={() => {submitQueueRequest('queue-cog-creation')}}
>
    <p>Submit mosaic COG generation to queue? If the current COG is up-to-date, there is no need to rebuild it.</p>
</ModalConfirm>
<ModalConfirm id="modal-confirm-xyz-queue"
    yesAction={() => {submitQueueRequest('queue-tileset-creation')}}
>
    <p>Submit XYZ tileset generation to queue? If the current XYZ tileset is up-to-date, there is no need to rebuild it.</p>
</ModalConfirm>

<div>
    <p>Once layers have been trimmed in the <strong>MultiMask</strong> they are combined into a single
    mosaic output, or "derivative". You can access these derivatives here in the form of file downloads, web service endpoints, and direct integrations
    into other platforms.</p>
    <p>To queue the creation (or recreation) of mosaics for each layerset, use the summary table below. If a derivative has been created, but
    the MultiMask has since been edited, it will be marked as <strong>stale</strong> it should be queued for a rebuild.
    Read more <Link href="https://docs.oldinsurancemaps.net/guides/generating-mosaics" rightArrow={true}>in the docs</Link></p>
</div>
{#if loading}
<LoadingEllipsis />
{/if}
{#each layersets as ls}
{#if ls.layers.length >= 2 || ls.id == "main-content"}
    <h4 class="dl-title">
        <span>
            {`${ls.name} (${ls.layers_masked_ct}/${ls.layers.length} layers masked)`}
        </span>
        <div class="dl-title-right">
            {#if ls.multimask_date}
            <span class="mask-timestamp">
                masks last edit: {ls.masksDateDisplay}
            </span>
            {/if}
            <button style="color:white" on:click={initLayersets}><ArrowsClockwise/></button>
        </div>
    </h4>
    <dl style="margin-bottom: 1em;">
        <dt class="derivative-subheader">
            Cloud Optimized GeoTIFF
            <div class="derivative-subheader-right">
                {#if ls.latest_cog_job}
                <MosaicStatus job={ls.latest_cog_job} maskDate={ls.multimask_date}/>
                {/if}
                <button
                    class="button is-small is-link"
                    disabled={!ls.enableCogQueueBtn}
                    title={ls.cogQueueBtnTitle}
                    on:click={() => {
                        layersetToQueueForCog=ls.id;
                        openModal('modal-confirm-cog-queue')
                    }}>build COG</button>
            </div>
        </dt>
        <dt>Direct download (.tif)</dt>
        <DerivativeDD
            linkUrl={ls.mosaic_cog_url}
            linkType="download"
            naMessage="requires COG"
        />
        <dt>TileJSON</dt>
        <DerivativeDD
            linkUrl={ls.tileJsonUrl}
            linkType="copytext"
            naMessage="requires COG"
        />
        <dt>Dynamic XYZ endpoint</dt>
        <DerivativeDD
            linkUrl={ls.dynamicXyzUrl}
            linkType="copytext"
            naMessage="requires COG"
        />
        <dt>WMS endpoint</dt>
        <DerivativeDD
            linkUrl={ls.wmsUrl}
            linkType="copytext"
            naMessage="requires COG"
        />
        <dt class="derivative-subheader">
            XYZ Tileset
            <div class="derivative-subheader-right">
                {#if ls.latest_xyz_job}
                <MosaicStatus job={ls.latest_xyz_job} maskDate={ls.multimask_date}/>
                {/if}
                <button
                    class="button is-small is-link"
                    disabled={!ls.enableXyzQueue}
                    title={ls.xyzQueueBtnTitle}
                    on:click={() => {
                        layersetToQueueForCog=ls.id;
                        openModal('modal-confirm-xyz-queue')
                    }}>build XYZ tileset</button>
            </div>
        </dt>
        <dt>Direct download (gzipped tarfile)</dt>
        <DerivativeDD
            linkUrl={ls.xyzStaticArchiveURL}
            linkType="download"
            naMessage="not yet generated"
        />
        <dt>Static XYZ endpoint</dt>
        <DerivativeDD
            linkUrl={ls.xyzStaticTilesURL}
            linkType="copytext"
            naMessage="not yet generated"
        />
        <dt class="derivative-subheader">
            Extensions
        </dt>
        <dt>Open in OpenHistoricalMap editor (uses dynamic XYZ endpoint)</dt>
        <DerivativeDD
            linkUrl={ls.ohmUrl}
            linkType="external"
            naMessage="requires COG"
        />
        <dt>IIIF Georef AnnotationPage</dt>
        <DerivativeDD
            linkUrl={ls.iiifAnnoUrl}
            linkType="external"
        />
        <dt>Open in Allmaps Viewer</dt>
        <DerivativeDD
            linkUrl={ls.allmapsUrl}
            linkType="external"
        />
    </dl>
{/if}
{/each}

<style>
    h4.dl-title {
        margin: 0;
        padding: .4em;
        color: #ffffff;
        background-color: var(--bulma-scheme-main);
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        flex-wrap: wrap;
    }
    .dl-title-right {
        display: flex;
        align-items: center;
        gap: .5em
    }
    span.mask-timestamp {
        font-size: .9em;
    }
    dl {
        background-color: #ffffff;
    }
    dt {
        padding: .25em .5em;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        font-weight: 700;
        font-size: .85em;
        background-color: #f6f6f6;
    }
    dt.derivative-subheader {
        background-color: rgb(188, 241, 253);
    }
    .derivative-subheader-right {
        display: flex;
        align-items: center;
        gap: .5em;
    }
</style>