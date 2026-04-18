<script>
  import Link from '../../common/Link.svelte';
  import DownloadSectionModal from '../../modals/ItemDownloadSectionModal.svelte';
  import InfoModalButton from '../../buttons/InfoModalButton.svelte';
  import MultiMask from '../../interfaces/MultiMask.svelte';

  import TabbedSection from '../../base/TabbedSection.svelte';

  import SigninReminder from '../../common/SigninReminder.svelte';

  import MapPreview from '../../interfaces/MapPreview.svelte';

  export let CONTEXT;
  export let MAP;
  export let currentLayerSet;
  export let layerSetLookup;
  export let LAYERSETS = [];
  export let previewRefreshable = false;
  export let userCanEdit;
  export let previewKey;
  export let reinitPreview;

  const tabs = [
    {id: "preview", title: "Preview"},
    {id: "multimask", title: "MultiMask"},
    {id: "download", title: "Downloads etc."},
  ]
  let activeTab = tabs[0].id;

  let multimaskKey = false;
  function reinitMultimask() {
    multimaskKey = !multimaskKey;
  }
</script>

<DownloadSectionModal id={'download-section-modal'} />
<TabbedSection {tabs} bind:activeTab>
<div>
    {#if activeTab == 'preview'}
        {#key previewKey}
            <MapPreview {CONTEXT} mapId={MAP.identifier} mapExtent={MAP.extent} bind:refreshable={previewRefreshable} />
        {/key}
    {:else if activeTab == 'multimask'}
        {#if !CONTEXT.user.is_authenticated}
          <SigninReminder csrfToken={CONTEXT.csrf_token} />
        {/if}
        <select
          class="item-select"
          bind:value={currentLayerSet}
          on:change={(e) => {
            reinitMultimask();
          }}
        >
          {#each LAYERSETS as ls}
            {#if ls.layers}
              <option value={ls.id}>{ls.name}</option>
            {/if}
          {/each}
        </select>
        <span>
          Masked layers:
          {#if layerSetLookup[currentLayerSet].multimask_geojson}
            {layerSetLookup[currentLayerSet].multimask_geojson.features.length}/{layerSetLookup[currentLayerSet].layers
              .length}
          {:else}
            0/{layerSetLookup[currentLayerSet].layers.length}
          {/if}
        </span>
        <span>
          <em
            >&mdash; <strong>Important:</strong> Do not work on a multimask while there is other work in progress on this
            map (you could lose work).</em
          >
        </span>
        {#key multimaskKey}
          <MultiMask
            LAYERSET={layerSetLookup[currentLayerSet]}
            {CONTEXT}
            DISABLED={!userCanEdit}
            resetMosaic={reinitPreview}
          />
        {/key}
    {:else if activeTab == 'download'}
    <div class="level">
    <div style="margin-top:10px;">
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
                <td>IIIf Georef AnnotationPage (JSON)</td>
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
    {/if}
</div>
</TabbedSection>

<style>
  table {
    width: 100%;
    border: 1px solid #ddd;
    border-radius: 4px;
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }

  td {
    padding: 4px;
  }

  td {
    background-color: #ffffff;
    width: 100%;
  }
  td:first-child {
    background-color: #f6f6f6;
    font-weight: 800;
    width: 150px;
  }

</style>
