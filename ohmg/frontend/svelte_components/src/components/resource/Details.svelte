<script>
  import { getCenter } from 'ol/extent';

  import { Download } from "phosphor-svelte";

  import Link from '../base/Link.svelte';
  import ResourceDownloadSectionModal from '../modals/ResourceDownloadSectionModal.svelte';

  import { makeTitilerXYZUrl } from '../../lib/utils';
  import InfoModalButton from '../buttons/InfoModalButton.svelte';

  export let CONTEXT;
  export let RESOURCE;
  export let MAP;

  let xyzUrl;
  let ohmUrl;
  let ll;
  let doubleEncodedXYZUrl;
  let jpegUrl;
  let cogUrl;
  let gcpsGeojsonUrl;
  let gcpsPointsUrl;
  if (RESOURCE.type == 'layer') {
    // this is a layer Resource
    jpegUrl = RESOURCE.document.urls.image;
    cogUrl = RESOURCE.urls.cog;
    xyzUrl = makeTitilerXYZUrl({
      host: CONTEXT.titiler_host,
      url: RESOURCE.urls.cog,
    });
    doubleEncodedXYZUrl = makeTitilerXYZUrl({
      host: CONTEXT.titiler_host,
      url: RESOURCE.urls.cog,
      doubleEncode: true,
    });
    ll = getCenter(RESOURCE.extent);
  } else {
    // this is a document resource
    jpegUrl = RESOURCE.urls.image;
  }
  if (RESOURCE.layer) {
    // this is a document resource that DOES have a layer (i.e. has been georeferenced)
    cogUrl = RESOURCE.layer.urls.cog;
    xyzUrl = makeTitilerXYZUrl({
      host: CONTEXT.titiler_host,
      url: RESOURCE.layer.urls.cog,
      doubleEncode: true,
    });
    doubleEncodedXYZUrl = makeTitilerXYZUrl({
      host: CONTEXT.titiler_host,
      url: RESOURCE.layer.urls.cog,
      doubleEncode: true,
    });
    ll = getCenter(RESOURCE.layer.extent);
  }
  if (doubleEncodedXYZUrl && ll) {
    ohmUrl = `https://www.openhistoricalmap.org/edit#map=16/${ll[1]}/${ll[0]}&background=custom:${doubleEncodedXYZUrl}`;
  }
</script>

<ResourceDownloadSectionModal id={'download-section-modal'} />

<h4 class="dl-title">Record</h4>
<dl>
  <dt>Title</dt>
  <dd>Sanborn Map of {RESOURCE.title}</dd>
  <dt>Status</dt>
  <dd>{RESOURCE.status}</dd>
</dl>
{#if !MAP.hidden}
<h4 class="dl-title">Downloads & Web Services</h4>
<dl>
  <dt>Image</dt>
  <dd>
    {#if jpegUrl}
      <Link href={jpegUrl} title="Download original JPEG" download={true}>JPEG</Link>
    {/if}
    {#if cogUrl}
      &bullet;
      <Link href={cogUrl} title="Download georeferenced layer as GeoTIFF" download={true}>GeoTIFF</Link>
    {/if}
  </dd>
  <dt>Ground Control Points</dt>
  <dd>
    {#if gcpsGeojsonUrl || gcpsPointsUrl}
      <!-- <Link href={gcpsGeojsonUrl} title="Download GCPs in GeoJSON format" download={`${RESOURCE.slug}.geojson`}>GeoJSON</Link> -->
      <!--&bullet;
          <Link href={gcpsPointsUrl} title="Download GCPs in .points format (QGIS)" download={`${RESOURCE.slug}.points`}>.points</Link>-->
    {:else}
      n/a
    {/if}
  </dd>
  <dt>XYZ Tiles URL</dt>
  <dd>
    {#if xyzUrl}
      <pre style="margin:0;">{xyzUrl}</pre>
    {:else}
      n/a
    {/if}
  </dd>
  <dt>OHM</dt>
  <dd>
    {#if ohmUrl}
      <Link href={ohmUrl} title="Open mosaic in OHM Editor" external={true}
        >Open in OpenHistoricalMap iD editor</Link
      >
    {:else}
      n/a
    {/if}</dd>
</dl>
{/if}

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
