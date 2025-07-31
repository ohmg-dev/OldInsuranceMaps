<script>
  import { slide } from 'svelte/transition';

  import MapPin from 'phosphor-svelte/lib/MapPin';

  import 'ol/ol.css';

  import { getCenter } from 'ol/extent';

  import Link from './common/Link.svelte';
  import SessionList from './lists/SessionList.svelte';
  import BasicDocViewer from './interfaces/BasicDocViewer.svelte';
  import BasicLayerViewer from './interfaces/BasicLayerViewer.svelte';
  import ConditionalDoubleChevron from './buttons/ConditionalDoubleChevron.svelte';
  import ToolUIButton from './buttons/ToolUIButton.svelte';

  import ResourceDetails from './overviews/sections/ResourceDetails.svelte';

  import ResourceBreadcrumbs from './breadcrumbs/ResourceBreadcrumbs.svelte';

  import { makeTitilerXYZUrl } from '../lib/utils';

  export let CONTEXT;
  export let RESOURCE;
  export let MAP;
  export let LOCALE;
  export let GEOREFERENCE_SUMMARY;

  const EXTENT = RESOURCE.type == 'layer' ? RESOURCE.extent : [0, -RESOURCE.image_size[1], RESOURCE.image_size[0], 0];
  const LAYER_URL = RESOURCE.type == 'layer' ? RESOURCE.urls.cog : RESOURCE.urls.image;

  let ll;
  let doubleEncodedXYZUrl;
  let viewerUrl;
  let xyzUrl;
  let ohmUrl;
  if (RESOURCE.type == 'layer') {
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
    viewerUrl = `/viewer/${LOCALE.slug}/?${MAP.identifier}=100#/center/${ll[0]},${ll[1]}/zoom/18`;
  } else if (RESOURCE.layer) {
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

  const sectionVis = {
    summary: true,
    preview: true,
    prep: true,
    georef: true,
    history: true,
  };

  function toggleSection(sectionId) {
    sectionVis[sectionId] = !sectionVis[sectionId];
  }

  let georeferenceBtnEnable = false;
  let georeferenceBtnTitle = 'Create Control Points';

  let processing;

  let filterParamsList = ['sort=oldest_first'];
  filterParamsList.push(`${RESOURCE.type}=${RESOURCE.id}`);
  const filterParam = filterParamsList.join('&');

  $: upperCaseType = RESOURCE.type[0].toUpperCase() + RESOURCE.type.substring(1, RESOURCE.type.length);

  $: {
    processing = RESOURCE.status == 'splitting' || RESOURCE.status == 'georeferencing';
    switch (RESOURCE.status) {
      case 'unprepared':
        sectionVis['georef'] = false;
        sectionVis['download'] = false;
        georeferenceBtnEnable = false;
        break;
      case 'prepared':
        georeferenceBtnEnable = true;
        break;
      case 'georeferenced':
        sectionVis['georef'] = false;
        georeferenceBtnEnable = true;
        georeferenceBtnTitle = 'Edit Control Points';
        break;
    }
  }

  let reinitMap = [{}];
</script>

<main>
  <ResourceBreadcrumbs {LOCALE} {MAP} {RESOURCE} />
  <section>
    <button
      class="section-toggle-btn"
      on:click={() => toggleSection('summary')}
      disabled={false}
      title={sectionVis['summary'] ? 'Collapse section' : 'Expand section'}
    >
      <ConditionalDoubleChevron down={sectionVis['summary']} size="md" />
      <h2>Summary</h2>
    </button>
    {#if sectionVis['summary']}
      <div transition:slide|global>
        <ResourceDetails {CONTEXT} {RESOURCE} {MAP} />
      </div>
    {/if}
  </section>
  <section>
    <button
      class="section-toggle-btn"
      on:click={() => toggleSection('preview')}
      disabled={false}
      title={sectionVis['preview'] ? 'Collapse section' : 'Expand section'}
    >
      <ConditionalDoubleChevron down={sectionVis['preview']} size="md" />
      <h2>{upperCaseType} Preview</h2>
    </button>
    {#if sectionVis['preview']}
      <div transition:slide|global>
        <div id="map-panel">
          {#each reinitMap as key (key)}
            {#if RESOURCE.type == 'layer'}
              <BasicLayerViewer {CONTEXT} {LAYER_URL} {EXTENT} />
            {:else}
              <BasicDocViewer {LAYER_URL} {EXTENT} />
            {/if}
          {/each}
        </div>
      </div>
    {/if}
  </section>
  <section>
    <button
      class="section-toggle-btn"
      on:click={() => toggleSection('prep')}
      disabled={false}
      title={sectionVis['prep'] ? 'Collapse section' : 'Expand section'}
    >
      <ConditionalDoubleChevron down={sectionVis['prep']} size="md" />
      <h2>Preparation</h2>
    </button>
    {#if sectionVis['prep']}
      <div transition:slide|global>
        <div class="section-body">
          {#if RESOURCE.prep_sessions.length > 0}
            Initial preparation by <a href={RESOURCE.prep_sessions[0].user.profile}
              >{RESOURCE.prep_sessions[0].user.username}</a
            >: Split needed?
            <strong
              >{RESOURCE.prep_sessions[0].data.split_needed
                ? `Yes: ${RESOURCE.document.title} has been split into ${RESOURCE.regions.length} regions.`
                : 'No.'}</strong
            >
          {/if}
          <div class="documents-column">
            {#if RESOURCE.regions}
              {#each RESOURCE.regions as region}
                <div class="document-item">
                  <div>
                    <Link href={region.urls.resource} title={region.title}
                      >p{region.page_number}{region.division_number ? ` [${region.division_number}]` : ''}</Link
                    >
                  </div>
                  <img src={region.urls.thumbnail} alt={region.title} title={region.title} />
                  <div>
                    <ul>
                      <li><strong>Georeferenced?</strong> {region.georeferenced ? 'Yes.' : 'Not yet...'}</li>
                      <li>
                        <Link href={region.urls.georeference} title="Georeference this region">
                          {region.georeferenced ? 'edit georeferencing' : 'georeference'} &rarr;
                        </Link>
                      </li>
                    </ul>
                  </div>
                </div>
              {/each}
            {:else}
              <div class="document-item">
                <div>
                  <Link href={RESOURCE.document.urls.resource} title={RESOURCE.document.title}
                    >p{RESOURCE.document.page_number}</Link
                  >
                </div>
                <img
                  src={RESOURCE.document.urls.thumbnail}
                  alt={RESOURCE.document.title}
                  title={RESOURCE.document.title}
                />
              </div>
            {/if}
          </div>
        </div>
      </div>
    {/if}
  </section>
  <section>
    <button
      class="section-toggle-btn"
      on:click={() => toggleSection('georef')}
      disabled={false}
      title={sectionVis['georef'] ? 'Collapse section' : 'Expand section'}
    >
      <ConditionalDoubleChevron down={sectionVis['georef']} size="md" />
      <h2>Georeferencing</h2>
    </button>
    {#if sectionVis['georef']}
      <div transition:slide|global>
        <div class="control-btn-group">
          <ToolUIButton
            onlyIcon={false}
            title={georeferenceBtnTitle}
            disabled={!georeferenceBtnEnable}
            action={() => {
              window.location.href = RESOURCE.urls.georeference;
            }}
          >
            <MapPin />{georeferenceBtnTitle}
          </ToolUIButton>
        </div>
        <div class="section-body">
          {#if GEOREFERENCE_SUMMARY}
            <table>
              <caption>{GEOREFERENCE_SUMMARY.gcp_geojson.features.length} Control Points</caption>
              <tr>
                <th>X</th>
                <th>Y</th>
                <th>Lng</th>
                <th>Lat</th>
                <th>User</th>
                <th>Note</th>
              </tr>
              {#each GEOREFERENCE_SUMMARY.gcp_geojson.features as feat}
                <tr>
                  <td class="coord-digit">{feat.properties.image[0]}</td>
                  <td class="coord-digit">{feat.properties.image[1]}</td>
                  <td class="coord-digit">{Math.round(feat.geometry.coordinates[0] * 1000000) / 1000000}</td>
                  <td class="coord-digit">{Math.round(feat.geometry.coordinates[1] * 1000000) / 1000000}</td>
                  <td>{feat.properties.username}</td>
                  <td>{feat.properties.note != null ? feat.properties.note : '--'}</td>
                </tr>
              {/each}
            </table>
          {/if}
        </div>
      </div>
    {/if}
  </section>
  <section style="border-bottom:none;">
    <button
      class="section-toggle-btn"
      on:click={() => toggleSection('history')}
      disabled={false}
      title={sectionVis['history'] ? 'Collapse section' : 'Expand section'}
    >
      <ConditionalDoubleChevron down={sectionVis['history']} size="md" />
      <h2>Session History</h2>
    </button>
    {#if sectionVis['history']}
      <div transition:slide|global>
        <SessionList
          {CONTEXT}
          FILTER_PARAM={filterParam}
          showResource={false}
          paginate={false}
          limit="0"
          allowRefresh={false}
        />
      </div>
    {/if}
  </section>
</main>

<style>
  #map-panel {
    width: 100%;
    height: 500px;
  }

  section {
    border-bottom: 1px solid rgb(149, 149, 149);
  }

  button.section-toggle-btn {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    background: none;
    border: none;
    color: #2c689c;
    padding: 0;
  }

  button.section-toggle-btn {
    text-decoration: none;
  }

  button.section-toggle-btn:hover {
    color: #1b4060;
  }

  button.section-toggle-btn:disabled {
    color: grey;
  }

  /* button.section-toggle-btn:disabled > a {
	color: grey;
} */

  .section-body {
    margin: 10px 0px;
  }

  table {
    min-width: 100%;
    border: 1px solid #ddd;
  }

  table caption {
    color: #333;
    text-align: center;
  }

  th,
  td {
    padding: 4px;
  }

  th {
    font-variant: small-caps;
    font-size: 0.85em;
  }

  tr:nth-child(even) {
    background-color: #f6f6f6;
  }

  tr:nth-child(odd) {
    background-color: #ffffff;
  }

  .coord-digit {
    font-family: Menlo, monospace;
    font-size: 0.85em;
  }

  .documents-column {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 20px;
  }

  .document-item {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    border: 1px solid gray;
    background: white;
    max-width: 45%;
    /* height: 150px; */
  }

  .document-item img {
    margin: 10px;
    max-height: 200px;
    max-width: 200px;
  }

  .document-item div:first-child {
    text-align: center;
  }

  .document-item div:first-child,
  .document-item div:last-child {
    padding: 5px;
    background: #e6e6e6;
    width: 100%;
  }

  .document-item ul {
    list-style-type: none;
    padding: 0;
  }

  @media screen and (max-width: 768px) {
    main {
      max-width: none;
    }
    .documents-column {
      flex-direction: column;
    }
  }
</style>
