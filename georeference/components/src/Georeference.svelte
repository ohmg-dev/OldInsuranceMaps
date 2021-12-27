<script>
import {onMount} from 'svelte';

import 'ol/ol.css';
import Map from 'ol/Map';
import View from 'ol/View';
import Feature from 'ol/Feature';

import Point from 'ol/geom/Point';
  
import ImageStatic from 'ol/source/ImageStatic';
import VectorSource from 'ol/source/Vector';
import OSM from 'ol/source/OSM';
import XYZ from 'ol/source/XYZ';
import TileWMS from 'ol/source/TileWMS';

import GeoJSON from 'ol/format/GeoJSON';

import TileLayer from 'ol/layer/Tile';
import ImageLayer from 'ol/layer/Image';
import VectorLayer from 'ol/layer/Vector';

import Projection from 'ol/proj/Projection';
import {transformExtent} from 'ol/proj';

import MousePosition from 'ol/control/MousePosition';
import {createStringXY} from 'ol/coordinate';

import Draw from 'ol/interaction/Draw';
import Modify from 'ol/interaction/Modify';
import Snap from 'ol/interaction/Snap';

import Styles from './js/ol-styles';
const styles = new Styles();

export let DOCUMENT;
export let IMG_SIZE;
export let CSRFTOKEN;
export let USERNAME;
export let REGION_EXTENT;
export let INCOMING_GCPS;
export let INCOMING_TRANSFORMATION;
export let MAPSERVER_ENDPOINT;
export let MAPSERVER_LAYERNAME;
export let MAPBOX_API_KEY;
export let USER_AUTHENTICATED;

console.log(DOCUMENT)

let disableInterface = !USER_AUTHENTICATED || DOCUMENT.status == "georeferencing";
console.log(disableInterface)

let previewMode = "n/a";

let activeGCP = 1;
let inProgress = false;

let panelFocus = "equal";
let syncPanelWidth = false;

let docView;
let mapView;
let gcpList = [];

let unchanged = true;

const imgWidth = IMG_SIZE[0];
const imgHeight = IMG_SIZE[1];

const beginTxt = "Click a recognizable location on the map document (left panel)"
const completeTxt = "Now find and click on the corresponding location in the web map (right panel)"

let currentTxt = beginTxt;

const noteInputElId = "note-input";

let currentTransformation = "poly1";
const transformations = [
  {id: 'poly1', name: 'Polynomial'},
  {id: 'tps', name: 'Thin Plate Spline'},
];

// generate a uuid, code from here:
// https://www.cloudhadoop.com/2018/10/guide-to-unique-identifiers-uuid-guid
function uuid() {
  var uuidValue = "", k, randomValue;
  for (k = 0; k < 32;k++) {
    randomValue = Math.random() * 16 | 0;
    if (k == 8 || k == 12 || k == 16 || k == 20) { uuidValue += "-" }
    uuidValue += (k == 12 ? 4 : (k == 16 ? (randomValue & 3 | 8) : randomValue)).toString(16);
  }
  return uuidValue;
}

const osmLayer = new TileLayer({
  source: new OSM(),
})

const imageryLayer = new TileLayer({
  source: new XYZ({
    url: 'https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v10/tiles/{z}/{x}/{y}?access_token='+MAPBOX_API_KEY,
    tileSize: 512,
  })
});

const basemaps = [
  { id: "osm", layer: osmLayer, label: "Streets" },
  { id: "satellite", layer: imageryLayer, label: "Streets+Satellite" },
]
let currentBasemap = basemaps[0].id;

const docGCPSource = new VectorSource();
docGCPSource.on('addfeature', function (e) {
  activeGCP = gcpList.length + 1;
  if (!e.feature.getProperties().listId) {
    e.feature.setProperties({'listId': activeGCP})
  }
  e.feature.setStyle(styles.gcpHighlight);
  inProgress = true;
  unchanged = false;
})

const mapGCPSource = new VectorSource();
mapGCPSource.on(['addfeature'], function (e) {

  // if this is an incoming gcp, the listID (and all other properties)
  // will already be set. Otherwise, it must be set here.
  if (!e.feature.getProperties().listId) {
    e.feature.setProperties({
      'id': uuid(),
      'listId': activeGCP,
      'username': USERNAME,
      'note': '',
    });
  }
  e.feature.setStyle(styles.gcpHighlight);
  syncGCPList();
  inProgress = false;
})

// create the preview layer from mapserver
const previewSource = new TileWMS({
  url: MAPSERVER_ENDPOINT,
  params: {
      // set this as env variable in apache conf file,
      // 'MAP': '/path/to/mapfile.map',
      'LAYERS': MAPSERVER_LAYERNAME,
      'TILED': true,
  },
  serverType: 'mapserver',
});

let startloads = 0;
let endloads = 0;
previewSource.on("tileloadstart", function (e) { startloads++ })
previewSource.on("tileloadend", function (e) { endloads++ })

const previewLayer = new TileLayer({ source: previewSource });

// this Modify interaction is created individually for each map panel
function makeModifyInteraction(hitDetection, source, targetElement) {
  const modify = new Modify({
    hitDetection: hitDetection,
    source: source,
    style: styles.gcpHover,
  });

  modify.on(['modifystart', 'modifyend'], function (e) {
    targetElement.style.cursor = e.type === 'modifystart' ? 'grabbing' : 'pointer';
    if (e.type == "modifyend") {
      activeGCP = e.features.item(0).getProperties().listId;
      unchanged = false;
      syncGCPList();
    }
  });

  let overlaySource = modify.getOverlay().getSource();
  overlaySource.on(['addfeature', 'removefeature'], function (e) {
    targetElement.style.cursor = e.type === 'addfeature' ? 'pointer' : '';
  });
  return modify
}

// this Draw interaction is created individually for each map panel
function makeDrawInteraction(source) {
  return new Draw({
    source: source,
    type: 'Point',
    style: styles.empty,
  });
}

function DocumentViewer (elementId) {

  const targetElement = document.getElementById(elementId);

  // items needed by layers and map
  // set the extent and projection with 0, 0 at the **top left** of the image
  const docExtent = [0, -imgHeight, imgWidth, 0];
  const docProjection = new Projection({
    units: 'pixels',
    extent: docExtent,
  });

  // create layers
  const docLayer = new ImageLayer({
    source: new ImageStatic({
      url: DOCUMENT.urls.image,
      projection: docProjection,
      imageExtent: docExtent,
    }),
    // zIndex: 999,
  })

  const gcpLayer = new VectorLayer({
    source: docGCPSource,
    style: styles.gcpDefault,
  });

  // create map
  const map = new Map({
    target: targetElement,
    layers: [docLayer, gcpLayer],
    view: new View({
      projection: docProjection,
      center: [imgWidth/2, -imgHeight/2],
      zoom: 1,
      maxZoom: 8,
    })
  });

  // create interactions
  const draw = makeDrawInteraction(docGCPSource);
  draw.setActive(true);
  targetElement.style.cursor = 'crosshair';
  map.addInteraction(draw)

  const modify = makeModifyInteraction(gcpLayer, docGCPSource, targetElement)
  modify.setActive(true);
  map.addInteraction(modify)

  // create controls
  const mousePositionControl = new MousePosition({
    coordinateFormat: function(coordinate) {
      const x = Math.round(coordinate[0]);
      const y = -Math.round(coordinate[1]);
      let formatted = `${x}, ${y}`;
      // set empty if the mouse is outside of the image itself
      if (x < 0 || x > imgWidth || y < 0 || y > imgHeight) {formatted = ""}
      return formatted
    },
    projection: docProjection,
    undefinedHTML: '&nbsp;',
  });
  map.addControl(mousePositionControl);

  // add some click actions to the map
  map.on("click", setActiveGCPOnClick);

  // add transition actions to the map element
  function updateMapEl() {map.updateSize()}
  targetElement.style.transition = "width .5s";
  targetElement.addEventListener("transitionend", updateMapEl)

  // expose properties as necessary
  this.map = map;
  this.element = targetElement;
  this.drawInteraction = draw;
  this.modifyInteraction = modify;
}

function MapViewer (elementId) {

    const targetElement = document.getElementById(elementId);

    const gcpLayer = new VectorLayer({
      source: mapGCPSource,
      style: styles.gcpDefault,
    });

    // create map
    const map = new Map({
      target: targetElement,
      layers: [basemaps[0].layer, gcpLayer],
      view: new View(),
    });

    // create interactions
    const draw = makeDrawInteraction(mapGCPSource);
    draw.setActive(false);
    map.addInteraction(draw)

    const modify = makeModifyInteraction(gcpLayer, mapGCPSource, targetElement)
    modify.setActive(true)
    map.addInteraction(modify)

    // create controls
    let mousePositionControl = new MousePosition({
      projection: 'EPSG:4326',
      coordinateFormat: createStringXY(6),
      undefinedHTML: '&nbsp;',
    });
    map.addControl(mousePositionControl);

    // add some click actions to the map
    map.on("click", setActiveGCPOnClick)

    // add transition actions to the map element
    function updateMapEl() {map.updateSize()}
    targetElement.style.transition = "width .5s";
    targetElement.addEventListener("transitionend", updateMapEl)

    // expose properties as necessary
    this.map = map;
    this.element = targetElement;
    this.drawInteraction = draw;
    this.modifyInteraction = modify;
}

onMount(() => {
  docView = new DocumentViewer('doc-viewer');
  mapView = new MapViewer('map-viewer');
  loadIncomingGCPs();
});

function loadIncomingGCPs() {
  docGCPSource.clear();
  mapGCPSource.clear();
  if (INCOMING_GCPS) {
    let listId = 1;
    let inGCPs = new GeoJSON().readFeatures(INCOMING_GCPS, {
      dataProjection: "EPSG:4326",
      featureProjection: "EPSG:3857",
    });

    inGCPs.forEach( function(inGCP) {

      inGCP.setProperties({"listId": listId})
      mapGCPSource.addFeature(inGCP);

      const gcpProps = inGCP.getProperties()
      const docFeat = new Feature({
        geometry: new Point([
          gcpProps.image[0],
          -gcpProps.image[1]
        ])
      });
      docFeat.setProperties({"listId": listId})
      docGCPSource.addFeature(docFeat);
      listId += 1;
    });
    previewMode = "transparent";
    mapView.map.getView().fit(mapGCPSource.getExtent(), {padding: [100, 100, 100, 100]});
  } else {
    const extent3857 = transformExtent(REGION_EXTENT, "EPSG:4326", "EPSG:3857");
    mapView.map.getView().fit(extent3857);
  }
  currentTransformation = (INCOMING_TRANSFORMATION ? INCOMING_TRANSFORMATION : "poly1")
  syncGCPList();
  activeGCP = gcpList.length + 1;
  inProgress = false;
  unchanged = true;
}

function setActiveGCPOnClick(e) {
  e.map.forEachFeatureAtPixel(e.pixel, function(feature) {
    activeGCP = feature.getProperties().listId;
  });
}

function removeActiveGCP() {
  if (activeGCP) { removeGCP(activeGCP) }
}

function confirmGCPRemoval(gcpId) {
  return window.confirm(`Remove GCP #${gcpId}?`);
}

function removeGCP(gcpListID) {
  if (confirmGCPRemoval(gcpListID)) {
    mapGCPSource.forEachFeature( function (mapFeat) {
      if (mapFeat.getProperties().listId == gcpListID) {
        mapGCPSource.removeFeature(mapFeat)
      }
    });
    docGCPSource.forEachFeature( function (docFeat) {
      if (docFeat.getProperties().listId == gcpListID) {
        docGCPSource.removeFeature(docFeat)
      }
    });
    resetListIds();
    activeGCP = (gcpList.length == 0 ? 1 : activeGCP - 1);
    inProgress = false;
  }
}

function resetListIds() {
  // iterates the features in map and doc and resets all list ids.
  // necessary if any GCP has been deleted that is not the last in the list.
  let newListId = 1;
  mapGCPSource.forEachFeature( function (mapFeat) {
    docGCPSource.forEachFeature( function (docFeat) {
      if (mapFeat.getProperties().listId == docFeat.getProperties().listId) {
        docFeat.setProperties({'listId': newListId});
        mapFeat.setProperties({'listId': newListId});
      }
    });
    newListId += 1;
  })
  syncGCPList();
};

function syncGCPList() {
  // first make sure the image coordinates match the image property in the
  // corresponding map feature
  mapGCPSource.forEachFeature( function (mapFeat) {
    docGCPSource.forEachFeature( function (docFeat) {
      if (mapFeat.getProperties().listId == docFeat.getProperties().listId) {
        mapFeat.setProperties({'image': [
            Math.round(docFeat.getGeometry().flatCoordinates[0]),
            -Math.round(docFeat.getGeometry().flatCoordinates[1])
          ]
        });
      }
    })
  })
  // now refresh the gcpList
  gcpList = [];
  mapGCPSource.getFeatures().forEach(function (mapFeat) {
    const props = mapFeat.getProperties();
    const coords = mapFeat.getGeometry().flatCoordinates;
    gcpList.unshift({
      "id": props.id,
      "listId": props.listId,
      "pixelX": props.image[0],
      "pixelY": props.image[1],
      "coordX": Math.round(coords[0] * 100) / 100,
      "coordY": Math.round(coords[1] * 100) / 100,
      "username": props.username,
      "note": props.note,
    });
  });
  previewGCPs();
}

function updateNote() {
  const el = document.getElementById(noteInputElId);
  mapGCPSource.getFeatures().forEach( function (feature) {
    if (feature.getProperties().listId == activeGCP) {
      feature.setProperties({"note": el.value});
    }
  })
}

// Triggered by the inProgress boolean
function updateInterface(gcpInProgress) {

  if (syncPanelWidth) {
    panelFocus = ( gcpInProgress ? "right" : "left" )
    setPanelWidths(panelFocus)
  }
  if (docView && mapView) {
    docView.drawInteraction.setActive(!gcpInProgress);
    mapView.drawInteraction.setActive(gcpInProgress);
    docView.element.style.cursor = ( gcpInProgress ? 'default' : 'crosshair' );
    mapView.element.style.cursor = ( gcpInProgress ? 'crosshair' : 'default' );
    currentTxt = ( gcpInProgress ? completeTxt : beginTxt );
  }
}
$: updateInterface(inProgress)

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

function setPreviewVisibility(mode) {
  if (!mapView) { return }
  if (mode == "full" || mode == "transparent") {
    // first set the opacity of the layer
    const newOpacity = ( mode == "full" ? 1 : .6 );
    previewLayer.setOpacity(newOpacity);
    // now add the layer if necessary
    if (mapView.map.getLayers().getArray().length == 2){
      mapView.map.getLayers().insertAt(1, previewLayer)
    }
  } else if (mode == "none" || mode == "n/a") {
    // remove the layer
    mapView.map.removeLayer(previewLayer);
    startloads = 0;
    endloads = 0;
  }
}
$: setPreviewVisibility(previewMode);

$: previewLoading = (previewMode == "transparent" || previewMode == "full") && 
      ( startloads != endloads) ; 

// Triggered by change of activeGCP
function displayActiveGCP(activeId) {

  // set note display content
  const el = document.getElementById(noteInputElId);
  if (inProgress) {
    el.value = "";
  } else {
    mapGCPSource.getFeatures().forEach( function (feat) {
      let props = feat.getProperties();
      if (props.listId == activeId) { el.value = props.note }
    })
  }

  // highlight features for active GCP
  docGCPSource.getFeatures().forEach( function (feat) {
    feat.setStyle(styles.gcpDefault);
    if (feat.getProperties().listId == activeId) { feat.setStyle(styles.gcpHighlight) }
  })
  mapGCPSource.getFeatures().forEach( function (feat) {
    feat.setStyle(styles.gcpDefault)
    if (feat.getProperties().listId == activeId) { feat.setStyle(styles.gcpHighlight) }
  })
}
$: displayActiveGCP(activeGCP)

// Triggered by a (manual) change in which panel should have focus
function setPanelWidths (focusOn) {
  if (docView && mapView) {
    switch(focusOn) {
      case "equal":
        docView.element.style.width = "50%";
        mapView.element.style.width = "50%";
        break;
      case "left":
        docView.element.style.width = "75%";
        mapView.element.style.width = "25%";
        break;
      case "right":
        docView.element.style.width = "25%";
        mapView.element.style.width = "75%";
        break
    }
  }
}
$: setPanelWidths(panelFocus);

function toggleFullscreen () {
  if (document.fullscreenElement == null) {
    let promise = document.getElementsByClassName('svelte-component-main')[0].requestFullscreen();
    document.getElementById("fs-icon").classList.remove("fa-arrows-alt");
    document.getElementById("fs-icon").classList.add("fa-times");
  } else {
    document.exitFullscreen();
    document.getElementById("fs-icon").classList.remove("fa-times");
    document.getElementById("fs-icon").classList.add("fa-arrows-alt");
  }
}

// convert the map features to GeoJSON for sending to georeferencing operation
$: asGeoJSON = () => {
  let featureCollection = { "type": "FeatureCollection", "features": [] };
  mapGCPSource.forEachFeature( function(feature) {
    const wgs84_geom = feature.getGeometry().clone().transform('EPSG:3857', 'EPSG:4326')
    let props = feature.getProperties();
    delete props['geometry'];
    featureCollection.features.push(
      {
        "type": "Feature",
        "properties": props,
        "geometry": {
          "type": "Point",
          "coordinates": wgs84_geom.flatCoordinates
        }
      }
    )
  });
  return featureCollection
}

function process(operation){
  if (gcpList.length < 3) {
    previewMode = "n/a";
    return
  };

  if (operation == "submit") {disableInterface = true};

  const data = JSON.stringify({
    "gcp_geojson": asGeoJSON(),
    "transformation": currentTransformation,
    "operation": operation,
  });
  fetch(DOCUMENT.urls.georeference, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json;charset=utf-8',
        'X-CSRFToken': CSRFTOKEN,
      },
      body: data,
    })
    .then(response => response.json())
    .then(result => {
      if (previewMode == "n/a") { previewMode = "transparent"};
      if (operation == "preview") {
        let sourceUrl = previewSource.getUrls()[0];
        previewSource.setUrl(sourceUrl.replace(/\/[^\/]*$/, '/'+Math.random()));
        previewSource.refresh()
      } else if (operation == "submit") {
        window.location.href = DOCUMENT.urls.detail;
      }
    });
}

// wrappers for the backend view to process GCPs
function previewGCPs() { process("preview"); }
function submitGCPs() { process("submit"); }

// A couple of functions that are attached to the window itself

// wrapper function to call view for db cleanup as needed
function cleanupOnLeave (e) { process("cleanup"); }

function handleKeydown(e) {
  // only allow these shortcuts if the maps have focus,
  // so shortcuts aren't activated while typing a note.
  if (document.activeElement.id == "") {
    switch(e.key) {
      case "Escape":
        if (document.fullscreenElement != null) {  document.exitFullscreen(); }
        break;
      case "d": case "D":
        removeActiveGCP();
        break;
      case "w": case "W":
        // cyle through the three preview level options
        if (previewMode == "none") {
          previewMode = "transparent"
        } else if (previewMode == "transparent") {
          previewMode = "full"
        } else if (previewMode == "full") {
          previewMode = "none"
        }
        break;
    }
  }
}

</script>

<svelte:window on:keydown={handleKeydown} on:beforeunload={cleanupOnLeave}/>
<div class="hidden-small"><em>{currentTxt}</em></div>
<div class="svelte-component-main">
  {#if disableInterface}
  <div class="interface-mask">
    {#if !USER_AUTHENTICATED}
    <div class="signin-reminder">
      <p><em>
        <!-- svelte-ignore a11y-invalid-attribute -->
        <a href="#" data-toggle="modal" data-target="#SigninModal" role="button" >sign in</a> or
        <a href="/account/register">sign up</a> to proceed
      </em></p>
    </div>
    {:else}
    <p>currently processing control points<br><a href={DOCUMENT.urls.detail}>redirecting to document detail</a></p>
    <div id="interface-loading" class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
    {/if}
  </div>
  {/if}
  <nav>
    <div>
      <button title="Enter fullscreen" on:click={toggleFullscreen}><i id="fs-icon" class="fa fa-arrows-alt" /></button>
      <select title="Set panel size" bind:value={panelFocus} disabled={syncPanelWidth}>
        <option value="equal">equal panels</option>
        <option value="left">more left</option>
        <option value="right">more right</option>
      </select>
      <label><input type=checkbox bind:checked={syncPanelWidth}> autosize</label>
    </div>
    <div>
        <button on:click={submitGCPs} disabled={gcpList.length < 3 || unchanged} title="Save control points">Save Control Points</button>
        <button title="Return to document detail" onclick="window.location.href='{DOCUMENT.urls.detail}'">Cancel</button>
        <button title="Reset interface" disabled={unchanged} on:click={loadIncomingGCPs}><i class="fa fa-refresh" /></button>
    </div>
  </nav>
  <div class="map-container">
    <div id="doc-viewer" class="map-item"></div>
    <div id="map-viewer" class="map-item"></div>
    <div id="preview-loading" class={previewLoading ? 'lds-ellipsis': ''}><div></div><div></div><div></div><div></div></div>
  </div>
  <nav>
    <div style="display:flex; flex-direction:column;">
      {#if gcpList.length == 0}
      <div>
        <em>no control points added yet...</em>
      </div>
      {:else}
      <div id="summary-panel" style="display:flex; flex-direction:row">
        <select class="gcp-select" bind:value={activeGCP}>
          {#each gcpList as gcp}
            <option value={gcp.listId}>
              {gcp.listId} | ({gcp.pixelX}, {gcp.pixelY}) ({gcp.coordX}, {gcp.coordY}) | {gcp.username}
            </option>
          {/each}
        </select>
        <button title="Remove control point {activeGCP} (d)" on:click={removeActiveGCP}><i class="fa fa-trash" /></button>
      </div>
      <label style="margin-top:5px;" title="Add note about control point {activeGCP}">
        <span class="">Note:</span>
        <input type="text" id="{noteInputElId}" style="height:30px; width:250px;" disabled={gcpList.length == 0} on:change={updateNote}>
      </label>
      {/if}
    </div>
    <div style="display:flex; flex-direction:column; text-align:right;">
      <div>
        <span style="color:lightgray">{startloads}/{endloads}</span>
        <label title="Change basemap">
          Preview
          <select title="Set preview (w)" bind:value={previewMode} disabled={previewMode == "n/a"}>
            {#if previewMode == "n/a"}<option value="n/a" disabled>preview n/a</option>{/if}
            <option value="none">none</option>
            <option value="transparent">1/2</option>
            <option value="full">full</option>
          </select>
        </label>
        <label title="Change basemap">
          Basemap
          <select  style="width:151px;" bind:value={currentBasemap}>
            {#each basemaps as basemap}
            <option value={basemap.id}>{basemap.label}</option>
            {/each}
          </select>
        </label>
      </div>
      <div>
        <label style="margin-top:5px;" title="Set georeferencing transformation">
          Transformation:
          <!-- svelte-ignore a11y-no-onchange -->
          <select class="trans-select" style="width:151px;" bind:value={currentTransformation} on:change={previewGCPs}>
            {#each transformations as trans}
              <option value={trans.id}>{trans.name}</option>
            {/each}
          </select>
        </label>
      </div>
    </div>
  </nav>
</div>

<style>

label {
  margin: 0px;
}

.map-item {
  width: 50%;
}

.gcp-select {
    max-width: 400px;
  }

@media screen and (max-width: 768px){
  .gcp-select {
    max-width: 300px;
  }
}

</style>
