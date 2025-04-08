<script>
  import ArrowCounterClockwise from 'phosphor-svelte/lib/ArrowCounterClockwise';
  import Copy from 'phosphor-svelte/lib/Copy';
  import DownloadSimple from 'phosphor-svelte/lib/DownloadSimple';
  import MapPin from 'phosphor-svelte/lib/MapPin';

  import { getModal } from '../modals/BaseModal.svelte';

  import Link from '../common/Link.svelte';

  import BaseCard from './BaseCard.svelte';

  import { copyToClipboard, getLayerOHMUrl, makeTitilerXYZUrl } from '../../lib/utils';

  export let CONTEXT;
  export let LAYERSET_CATEGORIES;
  export let layer;
  export let sessionLocks;
  export let userCanEdit;
  export let modalLyrUrl;
  export let modalExtent;
  export let modalIsGeospatial;
  export let reinitModalMap;
  export let classifyingLayers;
  export let layerToLayerSetLookup;
  export let undoGeorefLayerId;
  export let downloadEnabled = true;
  export let checkForExistingMask;
</script>

<BaseCard>
  <div slot="card-top">
    <Link href={layer.urls.resource} title={layer.title}>{layer.nickname}</Link>
  </div>
  <div slot="card-middle">
    <button
      class="thumbnail-btn"
      on:click={() => {
        modalLyrUrl = layer.urls.cog;
        modalExtent = layer.extent;
        modalIsGeospatial = true;
        getModal('modal-simple-viewer').open();
        reinitModalMap = [{}];
      }}
    >
      <img style="cursor:zoom-in" src={layer.urls.thumbnail} alt={layer.title} />
    </button>
  </div>
  <div slot="card-bottom">
    {#if sessionLocks.lyrs[layer.id]}
      <ul style="text-align:center">
        <li><em>session in progress...</em></li>
        <li>user: {sessionLocks.lyrs[layer.id].user.username}</li>
      </ul>
    {:else}
      <ul>
        {#if userCanEdit}
          <li>
            <Link href={layer.urls.georeference} title="edit georeferencing">
              <MapPin /> edit georeferencing
            </Link>
          </li>
          <li>
            <button
              disabled={!CONTEXT.user.is_staff && CONTEXT.user.username != layer.created_by}
              class="is-text-link"
              title={!CONTEXT.user.is_staff && CONTEXT.user.username != layer.created_by
                ? `Only ${layer.created_by} or an admin and can undo this layer.`
                : 'Undo all georeferencing for this layer.'}
              on:click={() => {
                undoGeorefLayerId = layer.id;
                getModal('modal-confirm-ungeoreference').open();
              }}
            >
              <ArrowCounterClockwise /> ungeoreference
            </button>
          </li>
        {/if}
        {#if downloadEnabled}
          <li>
            <input
              type="hidden"
              id="lyr-{layer.id}-xyz-link"
              value={`${makeTitilerXYZUrl({ host: CONTEXT.titiler_host, url: layer.urls.cog })}`}
            />
            <input
              type="hidden"
              id="lyr-{layer.id}-wms-link"
              value="{CONTEXT.titiler_host}/cog/wms/?LAYERS={layer.urls.cog}&VERSION=1.1.1"
            />
            <div id="lyr-{layer.id}-services" class="dropdown is-right" style="padding:0;">
              <div class="dropdown-trigger" style="padding:0;">
                <button
                  class="is-text-link"
                  aria-haspopup="true"
                  aria-controls="dropdown-menu6"
                  on:click|stopPropagation={() => {
                    document.getElementById(`lyr-${layer.id}-services`).classList.toggle('is-active');
                  }}
                >
                  <DownloadSimple />
                  <span>downloads & web services</span>
                </button>
              </div>
              <div class="dropdown-menu" id="dropdown-menu6" role="menu">
                <div class="dropdown-content">
                  <div class="dropdown-item">
                    <ul>
                      <li><Link href={layer.urls.cog}>GeoTIFF <DownloadSimple /></Link></li>
                      <li>
                        <button
                          class="is-text-link"
                          on:click={() => {
                            copyToClipboard(`lyr-${layer.id}-xyz-link`);
                          }}>XYZ Tiles URL <Copy /></button
                        >
                      </li>
                      <li>
                        <button
                          class="is-text-link"
                          on:click={() => {
                            copyToClipboard(`lyr-${layer.id}-wms-link`);
                          }}>WMS endpoint <Copy /></button
                        >
                      </li>
                      <li>
                        <Link href={getLayerOHMUrl(layer, CONTEXT.titiler_host)} external={true}
                          >OpenHistoricalMap iD</Link
                        >
                      </li>
                      <li>
                        <Link href="{CONTEXT.site_url}iiif/resource/{layer.id}/" external={true}
                          >IIIF Georef Annotation (beta)</Link
                        >
                      </li>
                      <li>
                        <Link
                          href="https://viewer.allmaps.org/?url={encodeURIComponent(
                            `${CONTEXT.site_url}iiif/resource/${layer.id}/`,
                          )}"
                          external={true}>Allmaps Viewer (beta)</Link
                        >
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </li>
        {/if}
        <li>
          <em
            >{layer.created_by}{#if layer.created_by != layer.last_updated_by}&nbsp;+ {layer.last_updated_by}{/if}</em
          >
        </li>
      </ul>
    {/if}
    {#if classifyingLayers}
      <select
        bind:value={layerToLayerSetLookup[layer.slug]}
        on:change={(e) => {
          checkForExistingMask(e.target.options[e.target.selectedIndex].value, layer.id);
        }}
      >
        {#each LAYERSET_CATEGORIES as opt}
          <option value={opt.slug}>{opt.display_name}</option>
        {/each}
      </select>
    {/if}
  </div>
</BaseCard>

<style>
  img {
    margin: 15px;
    max-height: 200px;
    max-width: 200px;
    object-fit: scale-down;
  }

  .dropdown-menu {
    background: none;
    padding: 0;
  }

  .dropdown-content {
    padding: 10px;
    background: #f7f1e1;
    box-shadow: gray 0px 0px 5px;
  }

  .dropdown-item {
    background: none;
    color: #333333;
    padding: 0;
    text-align: left;
  }
</style>
