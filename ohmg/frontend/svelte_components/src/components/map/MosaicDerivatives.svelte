<script>

    import Queue from 'phosphor-svelte/lib/Queue';
    import Copy from 'phosphor-svelte/lib/Copy';
    import CopyableText from '../shared/buttons/CopyableText.svelte';
  import ArrowSquareOut from 'phosphor-svelte/lib/ArrowSquareOut';
  import ArrowRight from 'phosphor-svelte/lib/ArrowRight';
  import DownloadSimple from 'phosphor-svelte/lib/DownloadSimple';

    import { getFromAPI } from "../../lib/requests";
    import { submitPostRequest } from "../../lib/requests";
    import Link from "../base/Link.svelte";
    import ModalConfirm from '../base/ModalConfirm.svelte';
    import { openModal } from '../base/Modal.svelte';
    import { onMount } from 'svelte';

    import DerivativeItem from '../shared/DerivativeItem.svelte';
    import DerivativeSubheader from '../shared/DerivativeSubheader.svelte';

    export let CONTEXT;
    export let mapId;

    let layersets = []

    const orderedCategories = [
        "main-content",
        "key-map",
    ]

    const initLayersets = () => {
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
                i.localeDateMasks = i.multimask_date ? new Date(i.multimask_date*1000).toLocaleString() : null;
                i.localeDateCog = i.mosaic_geotiff_date ? new Date(i.mosaic_geotiff_date*1000).toLocaleString() : null;
                i.localeDateTiles = i.xyz_tiles_date ? new Date(i.xyz_tiles_date*1000).toLocaleString() : null;
                i.cogStale = i.mosaic_geotiff_date < i.multimask_date
                i.tilesStale = i.xyz_tiles_date < i.multimask_date
                console.log(i)
                return i
            });
        });
    }

    initLayersets()

    function handleQueueRequestResponse(response) {
        console.log(response)
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

<ModalConfirm id="modal-confirm-cog-queue"
    yesAction={() => {submitQueueRequest('queue-cog-creation')}}
>
    <p>Submit mosaic COG generation to queue?</p>
</ModalConfirm>
<ModalConfirm id="modal-confirm-xyz-queue"
    yesAction={() => {submitQueueRequest('queue-tileset-creation')}}
>
    <p>Submit tileset generation to queue?</p>
</ModalConfirm>

<div>
    <p>
    Once layers have been trimmed in the <strong>MultiMask</strong>, a background process can be run
    to combine them into a single mosaic file, which serves as a basis for downloads and web services.
    If you see <strong>n/a</strong> below, the mosaic has not yet been created. You can still access 
    individual layers through the <strong>Georeferenced</strong> section, or view the mosaic in Allmaps
    (powered by IIIF).
    </p>
</div>
{#each layersets as ls}
{#if ls.layers.length >= 1}
    <h4 class="dl-title">
        <span>
            {`${ls.name} (${ls.layers.length} layer${ls.layers.length > 1 ? 's' : ''})`}
        </span>
        {#if ls.multimask_date}
        <span class="mask-timestamp">
            masks last updated: {ls.localeDateMasks}
        </span>
        {/if}
    </h4>
    <dl>
    <DerivativeSubheader title="Downloads"/>
    <DerivativeItem
        title="COG (cloud-optimized GeoTIFF)"
        dateTimestamp={ls.mosaic_geotiff_date}
        dateStale={ls.mosaic_geotiff_date < ls.multimask_date}
    >
        {#if ls.mosaic_cog_url}
        <Link
            href={ls.mosaic_cog_url}
            title="Download COG"
            download={true}
        >{ls.mosaic_cog_url}</Link
        >
        {/if}
    </DerivativeItem>
    <DerivativeItem
        title="XYZ tileset (archive)"
        dateTimestamp={ls.xyz_tiles_date}
        dateStale={ls.xyz_tiles_date < ls.multimask_date}
    >
        {#if ls.xyz_tiles_archive}
        <Link
            href={ls.xyz_tiles_archive}
            title="Download XYZ tiles archive file"
            download={true}
        >{ls.xyz_tiles_archive}</Link>
        {/if}
    </DerivativeItem>
    <DerivativeSubheader title="Service URLs"/>
    <DerivativeItem
        title="XYZ dynamic tiles"
        dateTimestamp={ls.mosaic_geotiff_date}
        dateStale={ls.mosaic_geotiff_date < ls.multimask_date}
        naMessage="requires COG"
    >
        {#if ls.tileJsonUrl}
        <CopyableText text={ls.tileJsonUrl} />
        {/if}
    </DerivativeItem>
    <DerivativeItem
        title="XYZ dynamic tiles"
        dateTimestamp={ls.mosaic_geotiff_date}
        dateStale={ls.mosaic_geotiff_date < ls.multimask_date}
        naMessage="requires COG"
    >
        {#if ls.mosaic_cog_url}
        <CopyableText text={ls.mosaic_cog_url} />
        {/if}
    </DerivativeItem>
    <DerivativeItem
        title="XYZ static tiles"
        dateTimestamp={ls.xyz_tiles_date}
        dateStale={ls.xyz_tiles_date < ls.multimask_date}
        naMessage="requires XYZ tileset"
    >
        {#if ls.xyz_tiles_url}
        <CopyableText text={`${ls.xyz_tiles_url}/{z}/{x}/{y}.png`} />
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
        dateTimestamp={ls.mosaic_geotiff_date}
        dateStale={ls.mosaic_geotiff_date < ls.multimask_date}
        naMessage="requires COG"
    >
    {#if ls.mosaic_cog_url}
        <Link
            href={ls.ohmUrl}
            title="Open mosaic in OpenHistoricalMap iD Editor"
            external={true}>{ls.ohmUrl}
        </Link>
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
</style>