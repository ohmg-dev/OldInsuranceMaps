<script>
import {onMount} from 'svelte';

import 'ol/ol.css';
import Map from 'ol/Map';
import View from 'ol/View';

import VectorSource from 'ol/source/Vector';
import OSM from 'ol/source/OSM';
import XYZ from 'ol/source/XYZ';
import TileWMS from 'ol/source/TileWMS';

import {transformExtent} from 'ol/proj';

import Feature from 'ol/Feature';

import Polygon from 'ol/geom/Polygon';

import TileLayer from 'ol/layer/Tile';
import VectorLayer from 'ol/layer/Vector';

import MousePosition from 'ol/control/MousePosition';
import {createStringXY} from 'ol/coordinate';

import Draw from 'ol/interaction/Draw';
import Modify from 'ol/interaction/Modify';

import Styles from './js/ol-styles';
const styles = new Styles();
import Utils from './js/ol-utils';
const utils = new Utils();

export let LOCK;
export let SESSION_ID;
export let SESSION_LENGTH;
export let CSRFTOKEN;
export let LAYER;
export let MAPBOX_API_KEY;
export let GEOSERVER_WMS;
export let INCOMING_MASK_COORDINATES;

let disableInterface = LOCK.enabled;
let disableReason = LOCK.type == "unauthenticated" ? LOCK.type : LOCK.stage;
let leaveOkay = true;
if (LOCK.stage == "in-progress") {
  leaveOkay = false;
}

// show the extend session prompt 15 seconds before the session expires
setTimeout(promptRefresh, (SESSION_LENGTH*1000) - 15000)

let autoRedirect;
function promptRefresh() {
  if (!leaveOkay) {
    const modal = document.getElementById("expirationModal");
    modal.style.display = "block";
    leaveOkay = true;
    autoRedirect = setTimeout(cancelAndRedirectToDetail, 15000);
  }
}

function cancelAndRedirectToDetail() {
  process("cancel");
  window.location.href=LAYER.urls.detail;
}

let previewMode = "n/a";
let maskPolygonCoords = [];
let maskSLDContent;

let submitBtnLabel;
$: {
  if (INCOMING_MASK_COORDINATES.length == 0) {
    submitBtnLabel = "Set Mask";
  } else if (maskPolygonCoords.length == 0) {
    submitBtnLabel = "Remove Mask";
  } else {
    submitBtnLabel = "Update Mask";
  }
}

$: unchanged = JSON.stringify(maskPolygonCoords) == JSON.stringify(INCOMING_MASK_COORDINATES);
$: maskToRemove = INCOMING_MASK_COORDINATES.length > 0;


let drawTxt = "Draw a polygon around the content you wish to retain. Click to begin, double-click to finish.";
let modifyTxt = "Click and drag on the polygon edges to modify it.";
let currentTxt = drawTxt;

let mapView;

function defaultSLD() {
  let sld = '<?xml version="1.0" encoding="UTF-8"?>'
  sld += '<StyledLayerDescriptor version="1.0.0"'
  sld += ' xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"'
  sld += ' xmlns="http://www.opengis.net/sld"'
  sld += ' xmlns:ogc="http://www.opengis.net/ogc"'
  sld += ' xmlns:xlink="http://www.w3.org/1999/xlink"'
  sld += ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
  sld += '<NamedLayer>'
  sld += ` <Name>${LAYER.geoserver_id}</Name>`
  sld += ' <UserStyle IsDefault="true">'
  sld += '  <FeatureTypeStyle>'
  sld += '   <Rule>'
  sld += '    <RasterSymbolizer>'
  sld += '      <Opacity>1</Opacity>'
  sld += '    </RasterSymbolizer>'
  sld += '   </Rule>'
  sld += '  </FeatureTypeStyle>'
  sld += ' </UserStyle>'
  sld += '</NamedLayer>'
  sld += '</StyledLayerDescriptor>'
  return sld
}

const trimmedLayer = new TileLayer({
  source: new TileWMS({
    url: GEOSERVER_WMS,
    params: {
      'LAYERS': LAYER.geoserver_id,
      'TILED': true,
      'SLD_BODY': defaultSLD(),
      // Strangely, STYLES needs to have some random value in it, so that
      // the "Library Mode" will find the corresponding style in the SLD_BODY,
      // instead of the default for this layer that is stored in Geoserver.
      'STYLES': 'placeholder',
    },
  })
});

const basemaps = utils.makeBasemaps(MAPBOX_API_KEY)
basemaps[1].layer.setOpacity(.75)
let currentBasemap = basemaps[0].id;

const trimShapeSource = new VectorSource();
const trimShapeLayer = new VectorLayer({
    source: trimShapeSource,
    style: styles.polyDraw,
  });
trimShapeSource.on("addfeature", function(e) {
  updateMaskPolygon(e.feature.getGeometry().getCoordinates()[0]);
  currentTxt = modifyTxt;
})
trimShapeSource.on("removefeature", function(e) {
  currentTxt = drawTxt;
})

function removeMask() {
  trimShapeSource.clear();
  maskSLDContent = defaultSLD();
  const extent3857 = transformExtent(LAYER.extent, "EPSG:4326", "EPSG:3857");
  mapView.map.getView().fit(extent3857);
  mapView.drawInteraction.setActive(true)

}

function resetInterface() {
  removeMask();
  if (INCOMING_MASK_COORDINATES.length > 0) {
    const feat = new Feature({
      geometry: new Polygon([INCOMING_MASK_COORDINATES])
    });
    trimShapeSource.addFeature(feat);
  }
  // maskPolygonCoords = INCOMING_MASK_COORDINATES;
  mapView.drawInteraction.setActive(true)
}

function updateMaskPolygon(coordinates) {
  if (coordinates) {
    maskPolygonCoords = [];
    coordinates.forEach( function(coord) {
      const lng = Math.round(coord[0]*10)/10;
      const lat = Math.round(coord[1]*10)/10;
      maskPolygonCoords.push([lng, lat])
    })
    process("preview");
  }
}

// triggered whenever the maskSLDContent is changed
function refreshPreview(sldBody) {
  if (sldBody) {
    trimmedLayer.getSource().updateParams({
      "SLD_BODY": sldBody,
    });
  }
}
$: refreshPreview(maskSLDContent);

  // this Modify interaction is created individually for each map panel
function makeModifyInteraction(hitDetection, source, targetElement) {
  const modify = new Modify({
  hitDetection: hitDetection,
  source: source,
  style: styles.polyModify,
  });

  modify.on(['modifystart', 'modifyend'], function (e) {
  targetElement.style.cursor = e.type === 'modifystart' ? 'grabbing' : 'pointer';
  if (e.type == "modifyend") {
    updateMaskPolygon(e.features.item(0).getGeometry().getCoordinates()[0]);
    process("preview");
  }
  });

  let overlaySource = modify.getOverlay().getSource();
  overlaySource.on(['addfeature', 'removefeature'], function (e) {
  targetElement.style.cursor = e.type === 'addfeature' ? 'pointer' : '';
  });
  return modify
}

function MapViewer (elementId) {

  const targetElement = document.getElementById(elementId);

  // create map
  const map = new Map({
    target: targetElement,
    layers: [
      basemaps[0].layer,
      trimmedLayer,
      trimShapeLayer,
    ],
    view: new View({
    zoom: 16,
    })
  });

  // create interactions
  const draw = new Draw({
    source: trimShapeSource,
    type: 'Polygon',
    style: styles.polyDraw,
  });
  draw.setActive(true);
  map.addInteraction(draw)

  const modify = makeModifyInteraction(trimShapeLayer, trimShapeSource, targetElement)
  modify.setActive(true)
  map.addInteraction(modify)

  // create controls
  let mousePositionControl = new MousePosition({
    projection: 'EPSG:4326',
    coordinateFormat: createStringXY(6),
    undefinedHTML: '&nbsp;',
  });
  map.addControl(mousePositionControl);

  // expose properties as necessary
  this.map = map;
  this.element = targetElement;
  this.drawInteraction = draw;
}

onMount(() => {
  mapView = new MapViewer("map-viewer");
  resetInterface();
});

// triggered by a change in the basemap id
function setBasemap(basemapId) {
  if (mapView) {
    mapView.map.getLayers().removeAt(0);
    basemaps.forEach( function(item) {
      if (item.id == basemapId) {
        mapView.map.getLayers().insertAt(0, item.layer);
      }
    });
  }
}
$: setBasemap(currentBasemap);

$: {
  if (mapView) {
    mapView.drawInteraction.setActive(maskPolygonCoords.length == 0); 
  }
}

function process(operation) {

  if (operation == "remove-mask") {
    removeMask()
  }

  if (operation == "submit" || operation == "cancel" || operation == "remove-mask") {
    disableReason = operation;
    leaveOkay = true;
    disableInterface = true;
  };

  if (operation == "extend-session") {
    leaveOkay = false;
    clearTimeout(autoRedirect)
    document.getElementById("expirationModal").style.display = "none";
    setTimeout(promptRefresh, (SESSION_LENGTH*1000) - 10000)
  }

  const data = JSON.stringify({
    "mask_coords": maskPolygonCoords,
    "operation": operation,
    "sesh_id": SESSION_ID,
  });
  fetch(LAYER.urls.trim, {
    method: 'POST',
    headers: {
    'Content-Type': 'application/json;charset=utf-8',
    'X-CSRFToken': CSRFTOKEN,
    },
    body: data,
  })
  .then(response => response.json())
  .then(result => {
    if (operation == "preview") {
      // this will trigger a refresh of the preview layer
      if (result['sld_content'] == null) {
        maskSLDContent = defaultSLD();
      } else {
        maskSLDContent = result['sld_content'];
      }
    }
    if (operation == "submit" || operation == "cancel" || operation == "remove-mask") {
      window.location.href = LAYER.urls.detail;
    }
  });
}

function confirmLeave () {
  event.preventDefault();
  event.returnValue = "";
  return "...";
}

function cleanup () {
  // if this is an in-progress session
  if (LOCK.stage == "in-progress") {
    // and if a preparation submission hasn't been made
    if (disableReason != 'submit' && disableReason != 'remove-mask') {
        // then cancel the session (delete it)
        process("cancel")
    }
  }
}

</script>

<svelte:window on:beforeunload={() => {if (!leaveOkay) {confirmLeave()}}} on:unload={cleanup}/>

<div id="expirationModal" class="modal">
  <div class="modal-content">
    <p>This trimming session is expiring, and will be cancelled soon.</p>
    <button on:click={() => {process("extend-session")}}>Give me more time!</button>
  </div>
</div>

<div class="tb-top-item"><em>{currentTxt}</em></div>
<div class="svelte-component-main">
  {#if disableInterface}
  <div class="interface-mask">
    <div class="signin-reminder">
      {#if disableReason == "unauthenticated"}
      <p><em>
        <!-- svelte-ignore a11y-invalid-attribute -->
        <a href="#" data-toggle="modal" data-target="#SigninModal" role="button" >Sign in</a> or
        <a href="/account/signup">sign up</a> to proceed.
      </em></p>
      {:else if disableReason == "input" || disableReason == "processing"}
      <p>Someone else is already trimming this layer (<a href="javascript:window.location.reload(true)">refresh</a>).</p>
      {:else if disableReason == "submit"}
      <p>Applying layer mask... redirecting to layer detail when finished.</p>
      <div id="interface-loading" class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
      {:else if disableReason == "remove-mask"}
      <p>Removing layer mask... redirecting to layer detail when finished.</p>
      <div id="interface-loading" class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
      {:else if disableReason == "cancel"}
      <p>Cancelling layer trimming.</p>
      <div id="interface-loading" class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
      {/if}
    </div>
  </div>
  {/if}
  <nav>
    <label title="Change basemap">
      Basemap
      <select bind:value={currentBasemap}>
        {#each basemaps as basemap}
        <option value={basemap.id}>{basemap.label}</option>
        {/each}
      </select>
    </label>
    <div>
      <button title={submitBtnLabel} on:click={() => {process("submit")}} disabled={unchanged}>{submitBtnLabel}</button>
      <button title="Cancel trimming" on:click={() => {process("cancel")}}>Cancel</button>
      <button title="Reset interface" on:click={resetInterface} disabled={unchanged}><i class="fa fa-refresh" /></button>
      <button title="Remove mask" on:click={() => {process("remove-mask")}} disabled={!maskToRemove}><i class="fa fa-trash" /></button>
    </div>
  </nav>
  <div class="map-container">
    <div id="map-viewer" class="map-item rounded-bottom"></div>
  </div>
</div>
