<script>
import { slide } from 'svelte/transition';

import IconContext from 'phosphor-svelte/lib/IconContext';
import { iconProps } from "../js/utils"

import Scissors from "phosphor-svelte/lib/Scissors";
import CheckSquareOffset from "phosphor-svelte/lib/CheckSquareOffset";
import ArrowCounterClockwise from "phosphor-svelte/lib/ArrowCounterClockwise";
import ArrowSquareOut from "phosphor-svelte/lib/ArrowSquareOut";
import MapPin from "phosphor-svelte/lib/MapPin";
import Trash from "phosphor-svelte/lib/Trash";

import 'ol/ol.css';

import {getCenter} from 'ol/extent';

import TitleBar from './components/TitleBar.svelte';
import ConditionalDoubleChevron from './components/ConditionalDoubleChevron.svelte';
import SessionList from './components/SessionList.svelte'
import SingleLayerViewer from './components/SingleLayerViewer.svelte';
import SingleDocumentViewer from './components/SingleDocumentViewer.svelte';

import {
  makeTitilerXYZUrl,
} from '../js/utils';

export let CSRFTOKEN;
export let USER_AUTHENTICATED;
export let USER_STAFF;
export let RESOURCE;
export let VOLUME;
export let REFRESH_URL;
export let SPLIT_SUMMARY;
export let GEOREFERENCE_SUMMARY;
export let MAPBOX_API_KEY;
export let TITILER_HOST;
export let OHMG_API_KEY;
export let SESSION_API_URL; 

let xyzUrl;
let ohmUrl;
let ll;
let doubleEncodedXYZUrl;
if (RESOURCE.type == "layer") {
  xyzUrl = makeTitilerXYZUrl({
    host: TITILER_HOST,
    url: RESOURCE.urls.cog,
  });
  doubleEncodedXYZUrl = makeTitilerXYZUrl({
    host: TITILER_HOST,
    url: RESOURCE.urls.cog,
    doubleEncode: true,
  });
  ll = getCenter(RESOURCE.extent);
} else if (RESOURCE.layer){
  xyzUrl = makeTitilerXYZUrl({
    host: TITILER_HOST,
    url: RESOURCE.layer.urls.cog,
    doubleEncode: true,
  });
  doubleEncodedXYZUrl = makeTitilerXYZUrl({
    host: TITILER_HOST,
    url: RESOURCE.layer.urls.cog,
    doubleEncode: true,
  });
  ll = getCenter(RESOURCE.layer.extent);
}
if (doubleEncodedXYZUrl && ll) {
  ohmUrl = `https://www.openhistoricalmap.org/edit#map=16/${ll[1]}/${ll[0]}&background=custom:${doubleEncodedXYZUrl}`
}

let showPrep = false;
let showGeoreference = false;
let showDownloads = false;

let splitBtnEnabled = false;
let noSplitBtnEnabled = false;
let undoBtnTitle = "Undo this determination";

let georeferenceBtnEnable = false;
let georeferenceBtnTitle = "Create Control Points";

let splitNeeded;
let undoBtnEnabled;
let processing;

// pretty clumsy but works for now. for SessionList make joined params from ids
let filterParamsList = ['sort=oldest_first']
if (RESOURCE.type === 'document') {
  filterParamsList.push(`resource=${RESOURCE.id}`)
  if (RESOURCE.layer) {
    filterParamsList.push(`resource=${RESOURCE.layer.id}`)
  }
} else if (RESOURCE.type === 'layer') {
  filterParamsList.push(`resource=${RESOURCE.id}`)
  filterParamsList.push(`resource=${RESOURCE.document.id}`)
}
const filterParam = filterParamsList.join('&')

$: {
  processing = RESOURCE.status == "splitting" || RESOURCE.status == "georeferencing"
  splitNeeded = SPLIT_SUMMARY ? SPLIT_SUMMARY.split_needed : "unknown";
  undoBtnEnabled = SPLIT_SUMMARY ? SPLIT_SUMMARY.allow_reset : false;
  switch(RESOURCE.status) {
    case "unprepared":
      showPrep = true;
      if (USER_AUTHENTICATED) {
        splitBtnEnabled = true;
        noSplitBtnEnabled = true;
      }
      showGeoreference = false;
      georeferenceBtnEnable = false;
      break
    case "splitting":
      undoBtnEnabled = false;
      break;
    case "split":
      showPrep = true;
      break;
    case "prepared":
      splitBtnEnabled = false;
      noSplitBtnEnabled = false;
      showGeoreference = true;
      georeferenceBtnEnable = true;
      break;
    case "georeferenced":
      showGeoreference = false;
      showDownloads = true;
      georeferenceBtnEnable = true;
      georeferenceBtnTitle = "Edit Control Points";
      break;
  }
}

// needs to be reimplented via API
function refresh() {
  fetch(REFRESH_URL)
  .then(response => response.json())
  .then(result => {
    RESOURCE = result.RESOURCE;
    SPLIT_SUMMARY = result.SPLIT_SUMMARY;
    GEOREFERENCE_SUMMARY = result.GEOREFERENCE_SUMMARY;
  });
}

function setSplit(operation) {

  let data = JSON.stringify({
    "operation": operation,
  });

  fetch(RESOURCE.urls.split, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json;charset=utf-8',
        'X-CSRFToken': CSRFTOKEN,
      },
      body: data,
    })
    .then(response => response.json())
    .then(result => {
      window.location = window.location
    });
}

function unGeoreference() {

  let data = JSON.stringify({
    "operation": "ungeoreference",
  });

  fetch(RESOURCE.urls.georeference, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json;charset=utf-8',
        'X-CSRFToken': CSRFTOKEN,
      },
      body: data,
    })
    .then(response => response.json())
    .then(result => {
      if (RESOURCE.type == "layer") {
        window.location = RESOURCE.document.urls.resource
      } else {
        window.location = window.location
      }
    });
}

const iconLinks = [
  {
    visible: true,
    enabled: RESOURCE.type == "layer",
    iconClass: 'document',
    alt: RESOURCE.document ? 'Go to document: ' + RESOURCE.document.title : '',
    url: RESOURCE.document ? RESOURCE.document.urls.resource : '',
  },
  {
    visible: true,
    enabled: RESOURCE.type == "document" && RESOURCE.layer,
    iconClass: 'layer',
    alt: RESOURCE.layer ? 'Go to layer: ' + RESOURCE.layer.title : 'Layer not yet made',
    url: RESOURCE.layer ? RESOURCE.layer.urls.resource : '',
  },
  {
    visible: true,
    enabled: true,
    iconClass: 'volume',
    alt: 'Go to volume: ' + VOLUME.title,
    url: VOLUME.urls.summary,
  }
]
let reinitMap = [{}]
</script>

<IconContext values={iconProps}>
<main>
  <TitleBar TITLE={RESOURCE.title} SIDE_LINKS={[]} ICON_LINKS={iconLinks} />
  <div class="content" style="display:flex;">
    <div id="map-panel">
      {#each reinitMap as key (key)}
      {#if RESOURCE.type == "document"}
        <SingleDocumentViewer  LAYER_URL={RESOURCE.urls.image} IMAGE_SIZE={RESOURCE.image_size} />
      {:else}
        <SingleLayerViewer  LAYER_URL={RESOURCE.urls.cog} EXTENT={RESOURCE.extent} MAPBOX_API_KEY={MAPBOX_API_KEY} TITILER_HOST={TITILER_HOST} />
      {/if}
      {/each}
    </div>
    <div id="sidebar">
      <section >
        <p><strong>Status:</strong> {RESOURCE.status}{processing ? " in progress..." : ""}
        </p>
      </section>
      <section>
        <h4 class="expandable" on:click={() => showPrep = !showPrep}>
          <ConditionalDoubleChevron down={showPrep} />
          Preparation</h4>
        {#if showPrep}
        <div transition:slide>
          <div class="control-btn-group">
            <button
              title="Split this document"
              disabled={!splitBtnEnabled}
              onclick="window.location.href='{RESOURCE.urls.split}'"
              class="control-btn{splitNeeded == true ? ' btn-chosen': ''}">
              <Scissors />
            </button>
            <button
              title="This document does not need to be split"
              disabled={!noSplitBtnEnabled}
              on:click={() => {setSplit("no_split")}}
              class="control-btn{splitNeeded == false ? ' btn-chosen': ''}">
              <CheckSquareOffset />
            </button>
            {#if USER_AUTHENTICATED}
            <button 
              class="control-btn"
              title={undoBtnTitle}
              disabled={!undoBtnEnabled}
              on:click={() => {setSplit("undo")}}>
              <ArrowCounterClockwise />
            </button>
            {/if}
          </div>
          <div class="section-body">
            {#if SPLIT_SUMMARY}
              <p>{SPLIT_SUMMARY.date_str} by 
                <a href={SPLIT_SUMMARY.user.profile}>{SPLIT_SUMMARY.user.name}</a>:
                {#if !SPLIT_SUMMARY.split_needed}
                No split needed.
                {:else if SPLIT_SUMMARY.child_docs.length > 0}
                Split into {SPLIT_SUMMARY.child_docs.length} new document{#if SPLIT_SUMMARY.child_docs.length != 1}s{/if},
                each must be georeferenced individually.
                {:else if SPLIT_SUMMARY.parent_doc}
                Split from <a href={SPLIT_SUMMARY.parent_doc.urls.resource}>{SPLIT_SUMMARY.parent_doc.title}</a>.
                {/if}
              </p>
              {#if SPLIT_SUMMARY.child_docs.length > 0}
              <div class="documents-column">
                {#each SPLIT_SUMMARY.child_docs as child}
                <div class="document-item">
                  <div>
                    <a href={child.urls.resource} title="{child.title}">{child.title.split(" | ")[1]}</a>
                  </div>
                  <img src={child.urls.thumbnail} alt={child.title} title={child.title}>
                  <div>
                    <ul>
                      <li><strong>Status:</strong> {child.status}</li>
                      <li><a href={child.urls.georeference} title="Document detail">
                        {#if child.status == "georeferenced"}edit georeferencing &rarr;
                        {:else}georeference &rarr;
                        {/if}
                      </a></li>
                    </ul>
                  </div>
                </div>
                {/each}
              </div>
              {/if}
            {/if}
          </div>
        </div>
        {/if}
      </section>
      <section>
        <h4 class="expandable" on:click={() => showGeoreference = !showGeoreference}>
          <ConditionalDoubleChevron down={showGeoreference} />
          Georeferencing
        </h4>
        {#if showGeoreference}
        <div transition:slide>
          <div class="control-btn-group">
            <button 
              class="control-btn"
              title={georeferenceBtnTitle}
              disabled={!georeferenceBtnEnable}
              onclick="window.location.href='{RESOURCE.urls.georeference}'">
              <MapPin />{georeferenceBtnTitle}
            </button>
            {#if USER_STAFF}
            <button
              class="control-btn"
              title="Remove all georeferencing for this resource"
              disabled={RESOURCE.status != "georeferenced"}
              on:click={unGeoreference}>
              <Trash />
            </button>
            {/if}
          </div>
          <div class="section-body">
            {#if GEOREFERENCE_SUMMARY.gcp_geojson}
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
                <td class="coord-digit">{Math.round(feat.geometry.coordinates[0]*1000000)/1000000}</td>
                <td class="coord-digit">{Math.round(feat.geometry.coordinates[1]*1000000)/1000000}</td>
                <td>{feat.properties.username}</td>
                <td>{feat.properties.note != null ? feat.properties.note : "--"}</td>
              </tr>
              {/each}
            </table>
            {/if}
            <!--
            {#if GEOREFERENCE_SUMMARY.sessions.length > 0}
            <table>
              <caption>Sessions</caption>
              <tr>
                <th>Timestamp</th>
                <th>User</th>
                <th>Stage</th>
                <th>Status</th>
                <th>GCPs</th>
              </tr>
              {#each GEOREFERENCE_SUMMARY.sessions as sesh, n}
              <tr>
                <td>{sesh.date_run != null ? sesh.date_run : "--"}</td>
                <td><a href={sesh.user.profile}>{sesh.user.name}</a></td>
                <td>{sesh.stage}</td>
                <td>{sesh.status}</td>
                <td>{sesh.data ? sesh.data.gcps.features.length : "--"}</td>
              </tr>
              {/each}
            </table>
            {/if}
            -->
          </div>
        </div>
        {/if}
        
      </section>
      <section style="border-bottom:none;">
        <h4 class="expandable" on:click={() => showDownloads = !showDownloads}>
          <ConditionalDoubleChevron down={showDownloads} />
          Downloads & Web Services
        </h4>
        {#if showDownloads}
        <div transition:slide>
          <!-- super duper messy for now...-->
          {#if RESOURCE.type == "document"}
            <p>Image: <a href="{RESOURCE.urls.image}" title="Download JPEG">JPEG</a>
              {#if RESOURCE.layer}
              &bullet;&nbsp;<a href="{RESOURCE.layer.urls.cog}" title="Download GeoTIFF">GeoTIFF</a>
              {/if}
            </p>
            {#if RESOURCE.layer}
            <p>GCPs: <a href="/mrm/{RESOURCE.layer.slug}?resource=gcps-geojson" title="Download GCPs as GeoJSON">GeoJSON</a>
              &bullet;&nbsp;<a href="/mrm/{RESOURCE.layer.slug}?resource=points" title="Download GCPs as QGIS .points file (EPSG:3857)">.points</a></p>
              
            {/if}
          {:else if RESOURCE.type == "layer"}
          <p>Image: <a href="{RESOURCE.urls.document}" title="Download JPEG">JPEG</a>
            &bullet;&nbsp;<a href="{RESOURCE.urls.cog}" title="Download GeoTIFF">GeoTIFF</a>
          </p>
          <p>GCPs: <a href="/mrm/{RESOURCE.slug}?resource=gcps-geojson" title="Download GCPs as GeoJSON">GeoJSON</a>
            &bullet;&nbsp;<a href="/mrm/{RESOURCE.slug}?resource=points" title="Download GCPs as QGIS .points file (EPSG:3857)">.points</a></p>
          XYZ URL: <pre>{xyzUrl}</pre>
            <p>Use this URL in:
              <a href="https://leafletjs.com/reference.html#tilelayer">Leaflet</a>,
              <a href="https://openlayers.org/en/latest/examples/xyz.html">OpenLayers</a>,
              <a href="https://maplibre.org/maplibre-gl-js-docs/example/map-tiles/">Mapbox/MapLibre GL JS</a>,
              <a href="https://docs.qgis.org/3.22/en/docs/user_manual/managing_data_source/opening_data.html#using-xyz-tile-services">QGIS</a>, and
              <a href="https://esribelux.com/2021/04/16/xyz-tile-layers-in-arcgis-platform/">ArcGIS</a>.
              {#if ohmUrl}
              <br><a href="{ohmUrl}" alt="View in OHM iD editor" target="_blank">View in Open Historical Map iD editor<ArrowSquareOut /></a> (direct link).
              {/if}
            </p>
          {/if}
        </div>
        {/if}
      </section>
    </div>
  </div>
  <div>
    <h3>Session History</h3>
    <SessionList OHMG_API_KEY={OHMG_API_KEY} SESSION_API_URL={SESSION_API_URL} FILTER_PARAM={filterParam} showResource={false}/>
  </div>
</main>
</IconContext>

<style>

main {
  display: flex;
  flex-direction: column;
  padding: 0px 20px;
  margin-bottom: 10px;
}

.content {
  display: flex;
  flex-direction: row;
}

#sidebar {
  width: 40%;
  background: white;
  border: 1px solid lightgrey;
  border-radius: 4px;
  margin-left: 10px;
  padding: 10px;
}

#map-panel {
  width: 100%;
  height: 500px;
}

@media screen and (max-width: 768px){
  .content {
    flex-direction: column;
  }
  main {
    padding: 0;
  }
  #sidebar {
    width: 100%;
    margin-left: 0px;
  }
}


/* i {
  width: 20px;
  text-align: center;
} */

/* button:enabled {
  color: white;
  background-color: #2c689c;
  border-radius: 4px;
  border: 1px solid transparent;
}

button:hover:enabled {
  color: white;
  background-color: #204d74;
  border-color: #193b58;
} */

.btn-chosen {
  border: 2px solid #2c2c2c;
  border-radius: 4px;
}

section {
  border-bottom: 1px dashed rgb(149,149,149);;
}

section h4.expandable {
  color: #2c689c;
  cursor: pointer;
}

.section-body {
  margin: 10px 0px;
}

table {
	min-width:100%;
  border: 1px solid #ddd;
}

table caption {
  color: #333;
  text-align: center;
}

th, td {
	padding: 4px;
}

th {
  font-variant: small-caps;
  font-size: .85em;
}

tr:nth-child(even) {
  background-color: #f6f6f6;
}

tr:nth-child(odd) {
  background-color: #ffffff;
}

.coord-digit {
  font-family: Menlo, monospace;
  font-size: .85em;
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

.document-item div:first-child, .document-item div:last-child {
  padding: 5px;
  background: #e6e6e6;
  width: 100%;
}

.document-item ul {
  list-style-type: none;
  padding: 0;
}

</style>
