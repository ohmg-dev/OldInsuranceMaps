<script>
  import Link from '../../common/Link.svelte';
  import DownloadSectionModal from '../../modals/ItemDownloadSectionModal.svelte';
  import SessionList from '../../lists/SessionList.svelte';
  import InfoModalButton from '../../buttons/InfoModalButton.svelte';

  export let CONTEXT;
  export let MAP;
  export let SESSION_SUMMARY;
  export let LAYERSETS = [];
</script>

<DownloadSectionModal id={'download-section-modal'} />
<section>
  <div class="fixed-grid has-12-cols has-1-cols-mobile">
    <div class="grid">
      <div class="cell is-col-span-5">
        <h3>Map Details</h3>
        <table>
          <tbody>
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
            <tr>
              <td>Source</td>
              <td
                ><Link href="https://loc.gov/item/{MAP.identifier}" external={true}>loc.gov/item/{MAP.identifier}</Link
                ></td
              >
            </tr>
          </tbody>
        </table>
      </div>
      <div class="cell is-col-span-7">
        <h3>Contributors & Attribution</h3>
        <table>
          <thead>
            <tr>
              <td>Initial load</td>
              <td>
                {#if MAP.progress.loaded_pages}
                  loaded by <Link href={MAP.loaded_by.profile}>{MAP.loaded_by.name}</Link> - {MAP.loaded_by.date}<br />
                {:else}--{/if}
              </td>
            </tr>
            <tr>
              <td>Prep</td>
              <td>
                {SESSION_SUMMARY.prep_ct} document{#if SESSION_SUMMARY.prep_ct != 1}s{/if} prepared{#if SESSION_SUMMARY.prep_ct > 0}&nbsp;by
                  {#each SESSION_SUMMARY.prep_contributors as c, n}<Link href="/profile/{c.name}">{c.name}</Link> ({c.ct}){#if n != SESSION_SUMMARY.prep_contributors.length - 1},
                    {/if}{/each}{/if}
              </td>
            </tr>
            <tr>
              <td>Georef</td>
              <td>
                {SESSION_SUMMARY.georef_ct} georeferencing session{#if SESSION_SUMMARY.georef_ct != 1}s{/if}{#if SESSION_SUMMARY.georef_ct > 0}&nbsp;by
                  {#each SESSION_SUMMARY.georef_contributors as c, n}<Link href="/profile/{c.name}">{c.name}</Link> ({c.ct}){#if n != SESSION_SUMMARY.georef_contributors.length - 1},
                    {/if}{/each}{/if}
              </td>
            </tr>
            <tr>
              <td>Credit line:</td>
              <td>Library of Congress, Geography and Map Division, Sanborn Maps Collection.</td>
            </tr>
          </thead>
        </table>
      </div>
    </div>
  </div>
  <div class="level">
    <div class="level-left">
      <h3>Mosaic Download & Web Services</h3>
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
  <p style="font-size:.9em;">
    <em>
      Only layers that have been trimmed in the <strong>MultiMask</strong> will appear in the downloadable mosaic files.
      You can access individual layers through the <strong>Georeferenced</strong> section.
    </em>
  </p>
  <h3>Work History</h3>
  <div>
    <SessionList {CONTEXT} mapFilter={{ id: MAP.identifier }} showMap={false} paginate={true} limit="50" />
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
