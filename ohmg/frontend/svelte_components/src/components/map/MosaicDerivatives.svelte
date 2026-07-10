<script>
    import Queue from 'phosphor-svelte/lib/Queue';
    import CopyableText from '../shared/buttons/CopyableText.svelte';

    import { getFromAPI } from "../../lib/requests";
    import { submitPostRequest } from "../../lib/requests";
    import Link from "../base/Link.svelte";
    import ModalConfirm from '../base/ModalConfirm.svelte';
    import { openModal } from '../base/Modal.svelte';

    import ModalInfo from '../base/ModalInfo.svelte';
    import LoadingEllipsis from '../shared/LoadingEllipsis.svelte';
    import DerivativeDD from '../shared/DerivativeDD.svelte';

    export let CONTEXT;
    export let mapId;

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
                i.ohmUrl = `${CONTEXT.site_url}map/${mapId}/${i.id}/ohm`
                i.tileJsonUrl = `${CONTEXT.site_url}map/${mapId}/${i.id}/tilejson`
                i.dynamicXyzUrl = i.mosaic_cog_url ? `${CONTEXT.titiler_host}/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png?${encodeURIComponent(i.mosaic_cog_url)}` : null;
                i.masksDateDisplay = i.multimask_date ? new Date(i.multimask_date*1000).toLocaleString() : null;
                i.xyz_tiles_archive = i.xyz_tiles_url ? `${i.xyz_tiles_url}/archive.tar.gz` : null;
                i.cogStale = false;
                i.cogDateDisplay = "---"
                if (i.latest_cog_job) {
                    if (i.latest_cog_job.stage == "completed") {
                        i.cogDate = new Date(i.latest_cog_job.date_started * 1000).toLocaleString();
                        i.cogDateDisplay = `last updated: ${i.cogDate}`;
                        i.cogStale = i.multimask_date ? i.latest_cog_job.date_started < i.multimask_date : false
                    } else {
                        i.cogDateDisplay = i.latest_cog_job.stage;
                    }
                } else {
                    i.cogDateDisplay = "not generated"
                }
                i.enableXyzQueue = false
                if (i.mosaic_cog_url && !i.cogStale) {
                    i.enableXyzQueue = true
                }

                i.xyzStale = false;
                i.xyzDateDisplay = "---"
                if (i.latest_xyz_job) {
                    if (i.latest_xyz_job.stage == "completed") {
                        i.xyzDate = new Date(i.latest_xyz_job.date_started * 1000).toLocaleString();
                        i.xyzDateDisplay = `last updated: ${i.xyzDate}`;
                        i.xyzStale = i.multimask_date ? i.latest_xyz_job.date_started < i.multimask_date : false;
                    } else {
                        i.xyzDateDisplay = i.latest_xyz_job.stage;
                    }
                } else {
                    i.xyzDateDisplay = "not generated"
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
    <p>Submit mosaic COG generation to queue?</p>
</ModalConfirm>
<ModalConfirm id="modal-confirm-xyz-queue"
    yesAction={() => {submitQueueRequest('queue-tileset-creation')}}
>
    <p>Submit XYZ tileset generation to queue?</p>
</ModalConfirm>

<div>
    <p>
    Once layers have been trimmed in the <strong>MultiMask</strong> they can be combined into a single
    layer, which takes the form of a "cloud-optimized GeoTIFF" (COG) and/or static XYZ tileset.
    These formats form the basis for many other data access methods as displayed below.
    </p>
    <p>If the MultiMask is updated after a mosaic has been generated, dates will be shown here in
        red until the mosaic artifacts are re-generated. <button class="is-text-link" on:click={initLayersets}>reload</button>
    </p>
</div>
{#if loading}
<LoadingEllipsis />
{/if}
{#each layersets as ls}
{#if ls.layers.length >= 1}
    <h4 class="dl-title">
        <span>
            {`${ls.name} (${ls.layers_masked_ct}/${ls.layers.length} layers masked)`}
        </span>
        {#if ls.multimask_date}
        <span class="mask-timestamp">
            masks last updated: {ls.masksDateDisplay}
        </span>
        {/if}
    </h4>
    <dl style="margin-bottom: 1em;">
        <dt class="derivative-subheader">
            Cloud Optimized GeoTIFF
            <span class="timestamp{ls.cogStale ? ' stale' : ''}">
                {ls.cogDateDisplay}
                {#if ls.cogStale}
                <button class="is-text-link" on:click={() => {
                        layersetToQueueForCog=ls.id;
                        openModal('modal-confirm-cog-queue')
                    }}>queue rebuild</button>
                {/if}
            </span>
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
        <dt>XYZ tile endpoint (dynamic)</dt>
        <DerivativeDD
            linkUrl={ls.dynamicXyzUrl}
            linkType="copytext"
            naMessage="requires COG"
        />
        <dt class="derivative-subheader">
            XYZ Tileset
            <span class="timestamp{ls.xyzStale ? ' stale' : ''}">
                {ls.xyzDateDisplay}
                {#if ls.xyzStale}
                <button class="is-text-link"
                    disabled={!ls.enableXyzQueue}
                    title={ls.enableXyzQueue ? 
                        'Queue creation of XYZ tileset' :
                        'COG must be rebuilt before tileset can be created'}
                    on:click={() => {
                        layersetToQueueForCog=ls.id;
                        openModal('modal-confirm-xyz-queue')
                    }}>queue rebuild</button>
                {/if}
            </span>
        </dt>
        <dt>Direct download (.tar archive)</dt>
        <DerivativeDD
            linkUrl={ls.xyz_tiles_archive}
            linkType="download"
            naMessage="not yet generated"
        />
        <dt>XYZ tile endpoint (static)</dt>
        <DerivativeDD
            linkUrl={ls.xyz_tiles_url}
            linkType="copytext"
            naMessage="not yet generated"
        />
        <dt class="derivative-subheader">
            Extensions...
            <span class="timestamp">
                always current, unless noted
            </span>
        </dt>
        <dt>Open in OpenHistoricalMap editor (uses XYZ tile endpoint)</dt>
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
        flex-wrap: wrap;
        font-weight: 700;
        font-size: .85em;
        background-color: #f6f6f6;
    }
    dt.derivative-subheader {
        background-color: rgb(188, 241, 253);
    }
    .timestamp {
        color: rgb(128, 128, 128);
    }
    .timestamp.stale {
        color: red;
    }
</style>