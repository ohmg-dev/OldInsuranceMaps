<script>
import { slide } from 'svelte/transition';
import {onMount} from 'svelte';

import Icon from 'svelte-icons-pack/Icon.svelte';
import FiScissors from 'svelte-icons-pack/fi/FiScissors';
import FiCheck from 'svelte-icons-pack/fi/FiCheck';
import FiCheckSquare from 'svelte-icons-pack/fi/FiCheckSquare';
import FiEdit from 'svelte-icons-pack/fi/FiEdit';
import FiRotateCcw from 'svelte-icons-pack/fi/FiRotateCcw';
import FiExternalLink from 'svelte-icons-pack/fi/FiExternalLink';
import FaSolidMapPin from 'svelte-icons-pack/fa/FaSolidMapPin';
import FiTrash2 from 'svelte-icons-pack/fi/FiTrash2';

import 'ol/ol.css';
import Map from 'ol/Map';
import View from 'ol/View';
import Feature from 'ol/Feature';

import {transformExtent, Projection} from 'ol/proj';

import {ImageStatic, XYZ} from 'ol/source';
import {Tile as TileLayer, Image as ImageLayer} from 'ol/layer';

import Utils from '../js/ol-utils';
import TitleBar from '../components/TitleBar.svelte';
import ConditionalDoubleChevron from '../components/ConditionalDoubleChevron.svelte';
const utils = new Utils();

export let CSRFTOKEN;
export let USER_AUTHENTICATED;
export let USER_STAFF;
export let RESOURCE;
export let VOLUME;
export let REFRESH_URL;
export let SPLIT_SUMMARY;
export let GEOREFERENCE_SUMMARY;
export let SESSION_HISTORY;
export let MAPBOX_API_KEY;
export let TITILER_HOST;

console.log(RESOURCE)

let xyzUrl;
let ohmUrl;
if (RESOURCE.type == "layer") {
  xyzUrl = utils.makeTitilerXYZUrl(TITILER_HOST, RESOURCE.urls.cog);
  //const ll = getCenter(VOLUME.extent);
  //ohmUrl = `https://www.openhistoricalmap.org/edit#map=16/${ll[1]}/${ll[0]}&background=custom:${mosaicUrlEncoded}`
  //ohmUrl = utils.makeTitilerXYZUrl(TITILER_HOST, RESOURCE.urls.cog, true);
} else if (RESOURCE.layer){
  xyzUrl = utils.makeTitilerXYZUrl(TITILER_HOST, RESOURCE.layer.urls.cog);
  //const ll = getCenter(VOLUME.extent);
  //ohmUrl = `https://www.openhistoricalmap.org/edit#map=16/${ll[1]}/${ll[0]}&background=custom:${mosaicUrlEncoded}`
  //ohmUrl = utils.makeTitilerXYZUrl(TITILER_HOST, RESOURCE.layer.urls.cog, true);
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
      showGeoreference = true;
      georeferenceBtnEnable = true;
      georeferenceBtnTitle = "Edit Control Points";
      break;
  }
}

function DocViewer () {

  const targetElement = document.getElementById('preview-map');

  // items needed by layers and map
  // set the extent and projection with 0, 0 at the **top left** of the image
  const docExtent = [0, -RESOURCE.image_size[1], RESOURCE.image_size[0], 0];
  const projection = new Projection({
    units: 'pixels',
    extent: docExtent,
  });

  // create layers
  const resLayer = new ImageLayer({
    source: new ImageStatic({
      url: RESOURCE.urls.image,
      projection: projection,
      imageExtent: docExtent,
    }),
  })

  // create map
  const map = new Map({
    target: targetElement,
    layers: [resLayer],
    view: new View({
      projection: projection,
      zoom: 1,
      maxZoom: 8,
    })
  });

  map.getView().fit(docExtent, {padding: [10, 10, 10, 10]});

  this.map = map;
}

function LayerViewer () {

  const targetElement = document.getElementById('preview-map');
  // function makeTitilerXYZUrl (host, cogUrl) {
    
  //   return 
  // }
  const basemaps = utils.makeBasemaps(MAPBOX_API_KEY);
  const extent = transformExtent(RESOURCE.extent, "EPSG:4326", "EPSG:3857");

  const cogUrlEncode = encodeURIComponent(RESOURCE.urls.cog)
  const resLayer = new TileLayer({
    source: new XYZ({
      url: TITILER_HOST +"/cog/tiles/{z}/{x}/{y}.png?TileMatrixSetId=WebMercatorQuad&url=" + cogUrlEncode,
    }),
    extent: extent
  });

  // create map
  const map = new Map({
    target: targetElement,
    layers: [basemaps[0].layer, resLayer],
  });

  map.getView().fit(extent);

  this.map = map;
}

let viewer;
onMount(() => {
  if (RESOURCE.type == "document") {
    // viewer = new DocViewer();
  } else if (RESOURCE.type == "layer") {
    viewer = new LayerViewer();
  }
})

// needs to be reimplented via API
function refresh() {
  fetch(REFRESH_URL)
  .then(response => response.json())
  .then(result => {
    RESOURCE = result.RESOURCE;
    SPLIT_SUMMARY = result.SPLIT_SUMMARY;
    GEOREFERENCE_SUMMARY = result.GEOREFERENCE_SUMMARY;
    SESSION_HISTORY = result.SESSION_HISTORY;
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
      console.log(result)
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
      console.log(result)
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

</script>
<main>
  <TitleBar TITLE={RESOURCE.title} SIDE_LINKS={[]} ICON_LINKS={iconLinks} />
  <div class="content" style="display:flex;">
    <div id="preview-map">
      {#if RESOURCE.type == "document"}
        <a href={RESOURCE.urls.image} title={RESOURCE.title}>
          <img style="width: 100%" src={RESOURCE.urls.image} alt={RESOURCE.title} />
        </a>
      {/if}
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
              <Icon src={FiScissors} />
            </button>
            <button
              title="This document does not need to be split"
              disabled={!noSplitBtnEnabled}
              on:click={() => {setSplit("no_split")}}
              class="control-btn{splitNeeded == false ? ' btn-chosen': ''}">
              <Icon src={FiCheckSquare} />
            </button>
            {#if USER_AUTHENTICATED}
            <button 
              class="control-btn"
              title={undoBtnTitle}
              disabled={!undoBtnEnabled}
              on:click={() => {setSplit("undo")}}>
              <Icon src={FiRotateCcw} />
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
              <Icon src={FaSolidMapPin} />{georeferenceBtnTitle}
            </button>
            {#if USER_STAFF}
            <button
              class="control-btn"
              title="Remove all georeferencing for this resource"
              disabled={RESOURCE.status != "georeferenced"}
              on:click={unGeoreference}>
              <Icon src={FiTrash2} />
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
              <!--<br><a href="{ohmUrl}" alt="Open in OHM iD editor" target="_blank">Open Historical Map iD editor<Icon src={FiExternalLink} /></a> (direct link).-->
            </p>
          {/if}
        </div>
        {/if}
      </section>
    </div>
  </div>
  <div>
    
  </div>
  <div>
    {#if SESSION_HISTORY.length > 0}
    <section>
      <table>
        <caption><h4>Session History</h4></caption>
        <tr>
          <th>#</th>
          <th>Action</th>
          <th>User</th>
          <th>Stage</th>
          <th>Status</th>
          <th>Timestamp (UTC)</th>
          <th>Details</th>
        </tr>
        {#each SESSION_HISTORY as session}
        <tr>
          <td>{session.id}</td>
          <td>{session.type}</td>
          <td><a href={session.user.profile}>{session.user.name}</a></td>
          <td>{session.stage}</td>
          <td>{session.status}</td>
          <td>{session.date_run != null ? session.date_run : '--'}</td>
          <td>{session.note != null ? session.note : '--'}</td>
        </tr>
        {/each}
      </table>
    </section>
    {/if}
  </div>

</main>

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

#preview-map {
  width: 60%;
  min-height: 500px;
}

#preview-map img {
  /* border-radius: 4px; */
  box-shadow: gray 0px 0px 5px;
}

@media screen and (max-width: 768px){
  .content {
    flex-direction: column;
  }
  #preview-map {
    width: 100%;
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

section h4 i {
  font-size: .65em;
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
