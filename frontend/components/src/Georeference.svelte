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
import LayerGroup from 'ol/layer/Group';

import Projection from 'ol/proj/Projection';
import {transformExtent} from 'ol/proj';

import MousePosition from 'ol/control/MousePosition';
import ScaleLine from 'ol/control/ScaleLine';
import {createStringXY} from 'ol/coordinate';

import Draw from 'ol/interaction/Draw';
import Modify from 'ol/interaction/Modify';
import Snap from 'ol/interaction/Snap';

import Styles from './js/ol-styles-georeference';
const styles = new Styles();
import Utils from './js/ol-utils-georeference';
const utils = new Utils();

import TitleBar from './TitleBar.svelte';
import GeoreferencePreamble from './GeoreferencePreamble.svelte';

export let USER;
export let SESSION_LENGTH;
export let DOCUMENT;
export let VOLUME;
export let CSRFTOKEN;
export let MAPSERVER_ENDPOINT;
export let MAPSERVER_LAYERNAME;
export let MAPBOX_API_KEY;

// reference layers are disabled for now, but all pieces are still retained
// export let TITILER_HOST;
// export let REFERENCE_LAYERS;

let previewMode = "n/a";

let inProgress = false;
let loadingInitial = false;

let panelFocus = "equal";
let syncPanelWidth = false;

let docView;
let mapView;
let gcpList = [];

let activeGCP = null;
$: nextGCP = gcpList.length + 1;

let unchanged = true;

let docFullMaskLayer;
let mapFullMaskLayer;

let docRotate;
let mapRotate;

$: docCursorStyle = inProgress ? 'default' : 'crosshair';
$: mapCursorStyle = inProgress ? 'crosshair' : 'default';

$: {
  if (docView && mapView) {
    docView.element.style.cursor = docCursorStyle;
    mapView.element.style.cursor = mapCursorStyle;
  }
}

const session_id = DOCUMENT.lock_enabled ? DOCUMENT.lock_details.session_id : null;

let disableInterface = DOCUMENT.lock_enabled && (DOCUMENT.lock_details.user.name != USER);
let disableReason;
let leaveOkay = true;
let enableButtons = false;
if (DOCUMENT.lock_enabled && (DOCUMENT.lock_details.user.name == USER)) {
  leaveOkay = false;
  enableButtons = true;
}
$: enableSave = gcpList.length >= 3 && enableButtons;

// let disableInterface = LOCK.enabled;
// let disableReason = LOCK.type == "unauthenticated" ? LOCK.type : LOCK.stage;
// let leaveOkay = true;
// if (LOCK.stage == "in-progress") {
//   leaveOkay = false;
// }

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

const nextPage = DOCUMENT.layer ? DOCUMENT.layer.urls.resource : DOCUMENT.urls.resource;
function cancelAndRedirectToDetail() {
  process("cancel");
  window.location.href=nextPage;
}

const beginTxt = "Click a recognizable location on the map document (left panel)"
const completeTxt = "Now find and click on the corresponding location in the web map (right panel)"
$: currentTxt = !inProgress ? beginTxt : completeTxt;

const noteInputElId = "note-input";

let currentTransformation = "poly1";
const transformations = [
  {id: 'poly1', name: 'Polynomial'},
  {id: 'tps', name: 'Thin Plate Spline'},
];

let currentTargetProjection = "EPSG:3857"
const availableProjections = [
  {id: 'EPSG:3857', name: 'Pseudo Mercator'},
  {id: 'ESRI:102009', name: 'Lambert North America'},
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

const basemaps = utils.makeBasemaps(MAPBOX_API_KEY);
let currentBasemap = basemaps[0].id;

const docGCPSource = new VectorSource();
docGCPSource.on('addfeature', function (e) {

  if (!e.feature.getProperties().listId) {
    e.feature.setProperties({'listId': nextGCP})
  }
  activeGCP = e.feature.getProperties().listId;
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
      'listId': nextGCP,
      'username': USER,
      'note': '',
    });
  }
  e.feature.setStyle(styles.gcpHighlight);
  // check the loadingInitial flag to save unnecessary calls to backend
  if (!loadingInitial) {syncGCPList()}
  inProgress = false;
  activeGCP = e.feature.getProperties().listId;
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

// const refGroup = new LayerGroup();
// REFERENCE_LAYERS.forEach( function (layer) {
//   const newLayer = new TileLayer({
//     source: new TileWMS({
//       url: GEOSERVER_WMS,
//       params: {
//         'LAYERS': layer,
//         'TILED': true,
//       },
//     })
//   });
//   refGroup.getLayers().push(newLayer)
// });

// let referenceVisible = REFERENCE_LAYERS.length > 0;
// $: {
//   refGroup.setVisible(referenceVisible)
// }

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
    const fallback = targetElement.id == 'doc-viewer' ? docCursorStyle : mapCursorStyle;
    targetElement.style.cursor = e.type === 'addfeature' ? 'pointer' : fallback;
  });
  return modify
}

// this Draw interaction is created individually for each map panel
function makeDrawInteraction(source, condition) {
  const draw = new Draw({
    source: source,
    type: 'Point',
    style: styles.empty,
    condition: condition,
  });
  draw.setActive(false);
  return draw
}

function DocumentViewer (elementId) {

  const targetElement = document.getElementById(elementId);

  const imgWidth = DOCUMENT.image_size[0];
  const imgHeight = DOCUMENT.image_size[1];

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
      zoom: 1,
      maxZoom: 8,
    })
  });

  docFullMaskLayer = utils.generateFullMaskLayer(map)
  map.addLayer(docFullMaskLayer)

  function coordWithinDoc (coordinate) {
    const x = coordinate[0];
    const y = -coordinate[1];
    // set n/a if the mouse is outside of the document image itself
    if (x < 0 || x > imgWidth || y < 0 || y > imgHeight) {
      return false
    } else {
      return true
    }
  }

  // create interactions
  function drawWithinDocCondition (mapBrowserEvent) {
    return coordWithinDoc(mapBrowserEvent.coordinate)
  }
  const draw = makeDrawInteraction(docGCPSource, drawWithinDocCondition);
  map.addInteraction(draw)

  const modify = makeModifyInteraction(gcpLayer, docGCPSource, targetElement)
  modify.setActive(true);
  map.addInteraction(modify)

  // create controls
  const mousePositionControl = new MousePosition({
    coordinateFormat: function(coordinate) {
      // set n/a if the mouse is outside of the document image itself
      if (coordWithinDoc(coordinate)) {
        const x = Math.round(coordinate[0]);
        const y = -Math.round(coordinate[1]);
        return `${x}, ${y}`
      } else {
        return 'n/a'
      }
    },
    projection: docProjection,
    undefinedHTML: 'n/a',
  });
  map.addControl(mousePositionControl);

  docRotate = utils.makeRotateCenterLayer();
  map.addLayer(docRotate.layer);

  // add some click actions to the map
  map.on("click", function(e) {
    let found = false;
    e.map.forEachFeatureAtPixel(e.pixel, function(feature) {
      if (feature.getProperties().listId) {
        activeGCP = feature.getProperties().listId;
        found = true;
      }
    });
    if (!found && !draw.getActive() && !inProgress) {activeGCP = null}
  });

  // add transition actions to the map element
  function updateMapEl() {map.updateSize()}
  targetElement.style.transition = "width .5s";
  targetElement.addEventListener("transitionend", updateMapEl)

  // expose properties as necessary
  this.map = map;
  this.element = targetElement;
  this.drawInteraction = draw;
  this.modifyInteraction = modify;

  this.resetExtent = function () {
    map.getView().setRotation(0);
    map.getView().fit(docExtent, {padding: [10, 10, 10, 10]});
  }
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
      layers: [
        basemaps[0].layer,
        // refGroup,
        previewLayer,
        gcpLayer,
      ],
      view: new View(),
    });

    mapFullMaskLayer = utils.generateFullMaskLayer(map)
    map.addLayer(mapFullMaskLayer)

    // create interactions
    const draw = makeDrawInteraction(mapGCPSource);
    map.addInteraction(draw)

    const modify = makeModifyInteraction(gcpLayer, mapGCPSource, targetElement)
    modify.setActive(true)
    map.addInteraction(modify)

    // create controls
    let mousePositionControl = new MousePosition({
      projection: 'EPSG:4326',
      coordinateFormat: createStringXY(6),
      undefinedHTML: 'n/a',
    });
    map.addControl(mousePositionControl);

    let scaleLine = new ScaleLine({
      units: 'us',
    });
    map.addControl(scaleLine)

    // add some click actions to the map
    map.on("click", function(e) {
      let found = false;
      e.map.forEachFeatureAtPixel(e.pixel, function(feature) {
        if (feature.getProperties().listId) {
          activeGCP = feature.getProperties().listId;
          found = true;
        }
      });
      if (!found && !draw.getActive()) {activeGCP = null}
    });

    mapRotate = utils.makeRotateCenterLayer()
    map.addLayer(mapRotate.layer)

    // add transition actions to the map element
    function updateMapEl() {map.updateSize()}
    targetElement.style.transition = "width .5s";
    targetElement.addEventListener("transitionend", updateMapEl)

    // expose properties as necessary
    this.map = map;
    this.element = targetElement;
    this.drawInteraction = draw;
    this.modifyInteraction = modify;
    this.resetExtent = function () {
      map.getView().setRotation(0);
      if (DOCUMENT.gcps_geojson) {
        map.getView().fit(mapGCPSource.getExtent(), {padding: [100, 100, 100, 100]});
      } else if (VOLUME.extent) {
        const extent3857 = transformExtent(VOLUME.extent, "EPSG:4326", "EPSG:3857");
        map.getView().fit(extent3857);
      } else {
        // show the entire US
        map.getView().setCenter( [ -10728204.02342, 4738596.138147663 ]);
        map.getView().setZoom(5)
      }
    }
}

onMount(() => {
  docView = new DocumentViewer('doc-viewer');
  mapView = new MapViewer('map-viewer');
  setPreviewVisibility(previewMode)
  loadIncomingGCPs();
  disabledMap(disableInterface)
  inProgress = false;
});

function disabledMap(disabled) {
  if (mapView) {
    mapView.map.getInteractions().forEach(x => x.setActive(!disabled));
	  mapFullMaskLayer.setVisible(disabled);
  }
  if (docView) {
    docView.map.getInteractions().forEach(x => x.setActive(!disabled));
	  docFullMaskLayer.setVisible(disabled);
  }
}
$: disabledMap(disableInterface)

function loadIncomingGCPs() {
  loadingInitial = true;
  docGCPSource.clear();
  mapGCPSource.clear();
  if (DOCUMENT.gcps_geojson) {
    let listId = 1;
    let inGCPs = new GeoJSON().readFeatures(DOCUMENT.gcps_geojson, {
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
  }
  currentTransformation = (DOCUMENT.transformation ? DOCUMENT.transformation : "poly1")
  syncGCPList();
  docView.resetExtent()
  mapView.resetExtent()
  loadingInitial = false;
  inProgress = false;
  unchanged = true;
  activeGCP = null;
}

function removeActiveGCP() {
  if (activeGCP) { removeGCP(activeGCP) }
}

function confirmGCPRemoval(gcpId) {
  return window.confirm(`Remove GCP #${gcpId}?<br>
  NOTE: There is currently a bug that may scramble the remaining GCPs.
  If possible, move this GCP to a new location rather remove it.`);
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
    activeGCP = null;
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
  process("preview");
}

function updateNote() {
  const el = document.getElementById(noteInputElId);
  mapGCPSource.getFeatures().forEach( function (feature) {
    if (feature.getProperties().listId == activeGCP) {
      feature.setProperties({"note": el.value});
    }
  })
}

$: {
  if (syncPanelWidth) {
    panelFocus = ( inProgress ? "right" : "left" )
  }
}

$: {
  if (docView && mapView) {
    docView.drawInteraction.setActive(!inProgress);
    mapView.drawInteraction.setActive(inProgress);
  }
}

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
    previewLayer.setVisible(true)
    previewLayer.setOpacity(mode == "full" ? 1 : .6);
  } else if (mode == "none" || mode == "n/a") {
    previewLayer.setVisible(false)
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
  if (el) {
    if (inProgress) {
      el.value = "";
    } else {
      mapGCPSource.getFeatures().forEach( function (feat) {
        let props = feat.getProperties();
        if (props.listId == activeId) { el.value = props.note }
      })
    }
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

$: {
  if (docView && mapView) {
    switch(panelFocus) {
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
  if (gcpList.length < 3 && (operation == "preview" || operation == "submit")) {
    previewMode = "n/a";
    return
  };

  if (operation == "submit" || operation == "cancel") {
    leaveOkay = true;
    disableInterface = true;
    disableReason = operation;
  };

  if (operation == "extend-session") {
    leaveOkay = false;
    clearTimeout(autoRedirect)
    document.getElementById("expirationModal").style.display = "none";
    setTimeout(promptRefresh, (SESSION_LENGTH*1000) - 10000)
  }

  const data = JSON.stringify({
    "gcp_geojson": asGeoJSON(),
    "transformation": currentTransformation,
    "projection": currentTargetProjection,
    "operation": operation,
    "sesh_id": session_id,
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
      if (operation == "preview") {
        if (previewMode == "n/a") { previewMode = "transparent"};
        let sourceUrl = previewSource.getUrls()[0];
        previewSource.setUrl(sourceUrl.replace(/\/[^\/]*$/, '/'+Math.random()));
        previewSource.refresh()
      } else if (operation == "submit" || operation == "cancel") {
          window.location.href = nextPage;
      }
    });
}

let keyPressed = {};
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
  // toggle the center icon to help with rotation
  if (e.shiftKey || e.key == "Shift") {keyPressed['shift'] = true}
	if (e.altKey || e.key == "Alt") {keyPressed['alt'] = true}
	if (keyPressed.shift && keyPressed.alt) {
    if (mapView && docView) {
      utils.showRotateCenter(docView.map, docRotate.layer, docRotate.feature)
      utils.showRotateCenter(mapView.map, mapRotate.layer, mapRotate.feature)
    }
	}
}

function handleKeyup(e) {
  // remove the center point if rotation is to be disabled
	if (e.shiftKey || e.key == "Shift") {keyPressed['shift'] = false}
	if (e.altKey || e.key == "Alt") {keyPressed['alt'] = false}
	if (!keyPressed.shift && !keyPressed.alt) {
		if (mapView && docView) {
      utils.removeRotateCenter(docRotate.layer)
      utils.removeRotateCenter(mapRotate.layer)
    }
	}
};

function confirmLeave () {
  event.preventDefault();
  event.returnValue = "";
  return "...";
}

// function cleanup () {
//   // if this is an in-progress session
//   if (LOCK.stage == "in-progress") {
//     // and if a preparation submission hasn't been made and a
//     // cancel post isn't already taking place
//     if (disableReason != 'submit' && disableReason != 'cancel') {
//         // then cancel the session (delete it)
//         process("cancel")
//     }
//   }
// }
function cleanup () {
  // if this is an in-progress session for the current user
  if (DOCUMENT.lock_enabled && (DOCUMENT.lock_details.user.name == USER) && !leaveOkay) {
    process("cancel")
  }
}

const iconLinks = [
  {
    visible: true,
    enabled: true,
    iconClass: 'document',
    alt: 'Go to document: ' + DOCUMENT.title,
    url: DOCUMENT.urls.resource,
  },
  {
    visible: true,
    enabled: DOCUMENT.layer ? true : false,
    iconClass: 'layer',
    alt: DOCUMENT.layer ? 'Go to layer: ' + DOCUMENT.layer.title : 'Layer not yet made',
    url: DOCUMENT.layer ? DOCUMENT.layer.urls.resource : '',
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

<svelte:window on:keydown={handleKeydown} on:keyup={handleKeyup} on:beforeunload={() => {if (!leaveOkay) {confirmLeave()}}} on:unload={cleanup}/>
<TitleBar TITLE={DOCUMENT.title} SIDE_LINKS={[]} ICON_LINKS={iconLinks}/>
<GeoreferencePreamble />
<div id="expirationModal" class="modal">
  <div class="modal-content">
    <p>This georeferencing session is expiring, and will be cancelled soon.</p>
    <button on:click={() => {process("extend-session")}}>Give me more time!</button>
  </div>
</div>

{#if !USER}
<div id="anonymousModal" class="modal" style="display:block;">
  <div class="modal-content" style="max-width:325px;">
    <p>Feel free to experiment with the interface. To submit your work, you must
      <a href="#" data-toggle="modal" data-target="#SigninModal" role="button" >sign in</a> or
      <a href="/account/signup">sign up</a>.</p>
    <button on:click={() => {document.getElementById('anonymousModal').style.display = 'none'}}>OK</button>
  </div>
</div>
{/if}

<div class="hidden-small"><em>{currentTxt}</em></div>
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
      <!-- svelte-ignore a11y-invalid-attribute -->
      <p>Someone is already georeferencing this document (<a href="javascript:window.location.reload(true)">refresh</a>).</p>
      {:else if disableReason == "submit"}
      <p>Saving control points and georeferencing document... redirecting to document detail page.</p>
      <div id="interface-loading" class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
      {:else if disableReason == "cancel"}
      <p>Cancelling georeferencing.</p>
      <div id="interface-loading" class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
      {/if}
    </div>
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
        <button title="Save control points" disabled={!enableSave} on:click={() => { process("submit") }}>Save Control Points</button>
        <button title="Cancel georeferencing" disabled={!enableButtons} on:click={() => { process("cancel") }}>Cancel</button>
        <button title="Reset interface" disabled={unchanged} on:click={loadIncomingGCPs}><i class="fa fa-refresh" /></button>
    </div>
  </nav>
  <div class="map-container">
    <div id="doc-viewer" class="map-item"></div>
    <div id="map-viewer" class="map-item"></div>
    <div id="preview-loading" style="top: 55px; right: 35px;" class={previewLoading ? 'lds-ellipsis': ''}><div></div><div></div><div></div><div></div></div>
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
            {#if previewMode == "n/a"}<option value="n/a" disabled>n/a</option>{/if}
            <option value="none">none</option>
            <option value="transparent">1/2</option>
            <option value="full">full</option>
          </select>
        </label>
        <!-- <label title="Show reference layers">
          Reference
          <input type="checkbox" title="Show reference layers" bind:checked={referenceVisible} disabled={REFERENCE_LAYERS == 0}>
        </label> -->
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
          <select class="trans-select" style="width:151px;" bind:value={currentTransformation} on:change={() => { process("preview"); }}>
            {#each transformations as trans}
              <option value={trans.id}>{trans.name}</option>
            {/each}
          </select>
        </label>
      </div>
      <!--
      <div>
        <label style="margin-top:5px;" title="Set georeferencing transformation">
          Projection:
          <select class="trans-select" style="width:151px;" bind:value={currentTargetProjection} on:change={() => { process("preview"); }}>
            {#each availableProjections as proj}
              <option value={proj.id}>{proj.name}</option>
            {/each}
          </select>
        </label>
      </div>-->
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
