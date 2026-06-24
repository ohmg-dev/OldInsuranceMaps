<script>
    import Queue from 'phosphor-svelte/lib/Queue';
    import CopyableText from '../shared/buttons/CopyableText.svelte';

    import { getFromAPI } from "../../lib/requests";
    import { submitPostRequest } from "../../lib/requests";
    import Link from "../base/Link.svelte";
    import ModalConfirm from '../base/ModalConfirm.svelte';
    import { openModal } from '../base/Modal.svelte';

    import DerivativeItem from '../shared/DerivativeItem.svelte';
    import DerivativeSubheader from '../shared/DerivativeSubheader.svelte';
    import ModalInfo from '../base/ModalInfo.svelte';

    export let CONTEXT;
    export let mapId;

    let layersets = []

    const orderedCategories = [
        "main-content",
        "key-map",
    ]

    const initLayersets = () => {
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
                console.log(ls)
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
                        i.cogDateDisplay = i.cogDate;
                        i.cogStale = i.multimask_date ? i.latest_cog_job.date_started < i.multimask_date : false
                    } else {
                        i.cogDateDisplay = i.latest_cog_job.stage
                    }
                } else {
                    i.cogDateDisplay = "not generated"
                }

                i.xyzStale = false;
                i.xyzDateDisplay = "---"
                if (i.latest_xyz_job) {
                    if (i.latest_xyz_job.stage == "completed") {
                        i.xyzDate = new Date(i.latest_xyz_job.date_started * 1000).toLocaleString();
                        i.xyzDateDisplay = i.xyzDate;
                        i.xyzStale = i.multimask_date ? i.latest_xyz_job.date_started < i.multimask_date : false;
                    } else {
                        i.xyzDateDisplay = i.latest_xyz_job.stage;
                    }
                } else {
                    i.xyzDateDisplay = "not generated"
                }
                console.log(i)
                console.log(CONTEXT)
                return i
            });
        });
    }
    initLayersets()

    function handleQueueRequestResponse(response) {
        initLayersets()
        openModal('modal-job-submitted')
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
        red until the mosaic artifacts are re-generated.
    </p>
</div>
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
    <dl>
    <DerivativeSubheader title="Downloads"/>
    <DerivativeItem
        title="COG (cloud-optimized GeoTIFF)"
        dateString={ls.cogDateDisplay}
        isStale={ls.cogStale}
        naMessage="not generated"
    >
        {#if ls.mosaic_cog_url}
        <Link
            href={ls.mosaic_cog_url}
            title="Download COG"
            download={true}
        >{ls.mosaic_cog_url}</Link
        >
        {:else}
        <span class="na-message">not generated</span>
        {/if}
    </DerivativeItem>
    <DerivativeItem
        title="XYZ tileset (archive)"
        dateString={ls.xyzDateDisplay}
        isStale={ls.xyzStale}
    >
        {#if ls.xyz_tiles_archive}
        <Link
            href={ls.xyz_tiles_archive}
            title="Download XYZ tiles archive file"
            download={true}
        >{ls.xyz_tiles_archive}</Link>
        {:else}
        <span class="na-message">not generated</span>
        {/if}
    </DerivativeItem>
    <DerivativeSubheader title="Service URLs"/>
    <DerivativeItem
        title="TileJSON"
        dateString={ls.cogDateDisplay}
        isStale={ls.cogStale}
    >
        {#if ls.tileJsonUrl}
        <CopyableText text={ls.tileJsonUrl} />
        {:else}
        <span class="na-message">requires COG</span>
        {/if}
    </DerivativeItem>
    <DerivativeItem
        title="XYZ dynamic tiles"
        dateString={ls.cogDateDisplay}
        isStale={ls.cogStale}
    >
        {#if ls.dynamicXyzUrl}
        <CopyableText text={ls.dynamicXyzUrl} />
        {:else}
        <span class="na-message">requires COG</span>
        {/if}
    </DerivativeItem>
    <DerivativeItem
        title="XYZ static tiles"
        dateString={ls.xyzDateDisplay}
        isStale={ls.xyzStale}
    >
        {#if ls.xyz_tiles_url}
        <CopyableText text={`${ls.xyz_tiles_url}/{z}/{x}/{y}.png`} />
        {:else}
        <span class="na-message">requires XYZ tileset</span>
        {/if}
    </DerivativeItem>
    <DerivativeItem
        title="IIIF Georef AnnotationPage"
        dateString="always current"
    >
        <Link
        href={ls.iiifAnnoUrl}
        title="View full AnnotationPage JSON for this mosaic"
        external={true}>{ls.iiifAnnoUrl}</Link
        >
    </DerivativeItem>
    <DerivativeSubheader title="Open in..."/>
    <DerivativeItem
        title="OpenHistoricalMap iD editor"
        dateString={ls.cogDateDisplay}
        isStale={ls.cogStale}
    >
    {#if ls.mosaic_cog_url}
        <Link
            href={ls.ohmUrl}
            title="Open mosaic in OpenHistoricalMap iD Editor"
            external={true}>{ls.ohmUrl}
        </Link>
        {:else}
        <span class="na-message">requires COG</span>
    {/if}
    </DerivativeItem>
    <DerivativeItem title="Allmaps" dateString="always current">
        <Link
            href={ls.allmapsUrl}
            title="Open mosaic in Allmaps Viewer"
            external={true}
            >{ls.allmapsUrl}
        </Link>
    </DerivativeItem>
    </dl>
    <div class="bottom-row" style="">
        <div class="buttons has-addons">
            <button class="button"
                disabled={!CONTEXT.user.perms.includes("core.queue_mosaic_cog")}
                title={CONTEXT.user.perms.includes("core.queue_mosaic_cog") ?
                    "Queue creation of COG" : "You do not have permission for this action"}
                on:click={() => {
                    layersetToQueueForCog=ls.id;
                    openModal('modal-confirm-cog-queue')
                }}>
                <Queue /><span>COG</span>
            </button>
            <button class="button"
                disabled={!CONTEXT.user.perms.includes("core.queue_mosaic_xyz")}
                title={CONTEXT.user.perms.includes("core.queue_mosaic_xyz") ?
                    "Queue creation of XYZ tileset" : "You do not have permission for this action"}
                on:click={() => {
                    layersetToQueueForCog=ls.id;
                    openModal('modal-confirm-xyz-queue')
                }}>
                <Queue/><span>XYZ tileset</span>
            </button>
        </div>
    </div>
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
    .bottom-row {
        display:flex;
        justify-content:end;
        background-color: #ffffff;
        border-bottom-right-radius: 6px;
        border-bottom-left-radius: 6px;
    }
    button > span {
        margin-left: 5px;
    }
    .na-message {
        font-size: .8em;
    }
    .na-message::before {
        content: "-- "
    }
</style>