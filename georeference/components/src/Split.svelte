<script>
import {onMount} from 'svelte';

import 'ol/ol.css';
import Map from 'ol/Map';
import View from 'ol/View';
import Feature from 'ol/Feature';

import Polygon from 'ol/geom/Polygon';

import ImageStatic from 'ol/source/ImageStatic';
import VectorSource from 'ol/source/Vector';

import ImageLayer from 'ol/layer/Image';
import VectorLayer from 'ol/layer/Vector';

import Projection from 'ol/proj/Projection';

import MousePosition from 'ol/control/MousePosition';
import {createStringXY} from 'ol/coordinate';

import Draw from 'ol/interaction/Draw';
import Select from 'ol/interaction/Select';
import Modify from 'ol/interaction/Modify';
import Snap from 'ol/interaction/Snap';

import Styles from './js/ol-styles';
import LineString from 'ol/geom/LineString';
const styles = new Styles();

export let DOCUMENT;
export let IMG_SIZE;
export let CSRFTOKEN;
export let INCOMING_CUTLINES;
export let USER_AUTHENTICATED;

let docView;
let showPreview = true;

let cutLines = [];
let divisions = [];

let currentInteraction = 'draw';

let unchanged = true;

let splitBtnLabel;
$: {
  if (divisions.length > 0) {
    splitBtnLabel = "Split";
  } else {
    splitBtnLabel = "No Split Needed";
  }
}

let disableInterface = !USER_AUTHENTICATED;

let currentTxt;
$: {
  if (divisions.length <= 1) {
    currentTxt = "If this image needs to be split, draw cut-lines across it as needed. Click once to start or continue a line, double-click to finish."
  } else {
    const linesTxt = cutLines.length + " " + (cutLines.length === 1 ? 'cut-line' : 'cut-lines');
    const divsTxt = divisions.length + " new " + (divisions.length === 1 ? 'document' : 'documents') + " will be made";
    currentTxt = "Split summary: " + linesTxt + " | " + divsTxt;
  }
}

const imgWidth = IMG_SIZE[0];
const imgHeight = IMG_SIZE[1];
const imgBorderPoly = [[[0,0], [imgWidth, 0], [imgWidth, imgHeight], [0, imgHeight], [0,0]]];

const borderFeature = new Feature({
  geometry: new Polygon(imgBorderPoly),
});

const projection = new Projection({
  code: 'whatdoesthismatter',
  units: 'pixels',
  extent: [0, 0, imgWidth, imgHeight],
});

function resetInterface() {
  const mapCenter = [imgWidth/2, imgHeight/2];
  const view = new View({
    projection: projection,
    center: mapCenter,
    zoom: 1,
    maxZoom: 8,
  })
  docView.map.setView(view)

  docView.cutLayerSource.clear();
  docView.previewLayerSource.clear();
  cutLines = [];
  divisions = [];
  INCOMING_CUTLINES.forEach(function(line) {
    docView.cutLayerSource.addFeature(
      new Feature({ geometry: new LineString(line) })
    );
  });
  unchanged = true;
}

function DocViewer(elementId) {

  const targetElement = document.getElementById(elementId);

  const mousePositionControl = new MousePosition({
    coordinateFormat: createStringXY(0),
    projection: projection,
    undefinedHTML: '&nbsp;',
  });

  const map = new Map({
    target: targetElement,
    view: new View(),
  });
  map.addControl(mousePositionControl);

  // add layers to map
  const img_layer = new ImageLayer({
    source: new ImageStatic({
      url: DOCUMENT.urls.image,
      projection: projection,
      imageExtent: projection.getExtent(),
    }),
  })
  map.addLayer(img_layer);

  const previewLayer = new VectorLayer({
    source: new VectorSource(),
    style: styles.splitPreviewStyle,
  });
  map.addLayer(previewLayer);

  const borderLayer = new VectorLayer({
    source: new VectorSource(),
    style: styles.splitBorderStyle,
  });
  borderLayer.getSource().addFeature(borderFeature);
  map.addLayer(borderLayer);

  const cutLayerSource = new VectorSource();
  cutLayerSource.on('addfeature', function (e) {
    cutLines.push(e.feature.getGeometry().getCoordinates())
    unchanged = false;
    previewSplit()
  })
  const cutLayer = new VectorLayer({
    source: cutLayerSource,
    style: styles.splitBorderStyle,
  });
  map.addLayer(cutLayer);

  // add interactions
  const draw = new Draw({
    source: cutLayerSource,
    type: 'LineString',
    style: styles.polyDraw,
  });
  map.addInteraction(draw);

  const selectInteraction = new Select({
    layers: [cutLayer],
  });

  const modify = new Modify({
    hitDetection: cutLayer,
    source: cutLayerSource,
    style: styles.polyModify,
  });

  modify.on(['modifystart', 'modifyend'], function (evt) {
    targetElement.style.cursor = evt.type === 'modifystart' ? 'grabbing' : 'grab';
  });

  const overlaySource = modify.getOverlay().getSource();
  overlaySource.on(['addfeature', 'removefeature'], function (evt) {
    targetElement.style.cursor = evt.type === 'addfeature' ? 'grab' : '';
  });
  modify.on('modifyend', function(e) {
    cutLines = [];
    cutLayerSource.forEachFeature( function(feature) {
      cutLines.push(feature.getGeometry().getCoordinates())
    });
    unchanged = false;
    previewSplit()
  });
  map.addInteraction(modify)

  const snapToCutLines = new Snap({
    source: cutLayer.getSource(),
  });
  const snapToBorder = new Snap({
    source: borderLayer.getSource(),
  })
  map.addInteraction(snapToCutLines);
  map.addInteraction(snapToBorder);

  this.draw = draw;
  this.modify = modify;
  this.cutLayerSource = cutLayerSource;
  this.previewLayerSource = previewLayer.getSource();
  this.previewLayer = previewLayer;
  this.map = map;
}

// function refreshPreviewLayer(polygons) e
$: {
  if (docView) {
    docView.previewLayerSource.clear();
    divisions.forEach(function (item, index) {
      let feature = new Feature({
        geometry: new Polygon([item]),
        name: index
      });
      docView.previewLayerSource.addFeature(feature);
    })
  }
}
// $: refreshPreviewLayer(divisions)

onMount(() => {
  docView = new DocViewer("doc-viewer");
  resetInterface();
});

$: {
  if (docView) {
    // switch interactions based on the radio buttons
    if (currentInteraction == "draw") {
      docView.draw.setActive(true);
      docView.modify.setActive(false);
    } else if (currentInteraction == "modify") {
      docView.draw.setActive(false);
      docView.modify.setActive(true);
    }

    // toggle the visibility of the preview layer based on the checkbox
    docView.previewLayer.setVisible(showPreview);
  }
}

function handleKeydown(event) {
  const key = event.key;
  if (key == "Escape") {
    if (docView) { docView.draw.abortDrawing()}
  } else if (key == "a" || key == "A") {
    currentInteraction = "draw"
  } else if (key == "e" || key == "E") {
    currentInteraction = "modify"
  }
}

function process(operation) {

  if (operation == "split") {disableInterface = true};

  let data = JSON.stringify({
    "lines": cutLines,
    "operation": operation,
  });

  fetch(DOCUMENT.urls.split, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json;charset=utf-8',
        'X-CSRFToken': CSRFTOKEN,
      },
      body: data,
    })
    .then(response => response.json())
    .then(result => {
      if (operation == "split") {
        window.location.href = DOCUMENT.urls.detail;
      } else if (operation == "no_split") {
        window.location.href = DOCUMENT.urls.georeference;
      } else if (operation == "preview") {
        divisions = result['divisions'];
      }
    });
}

function previewSplit() { if ( cutLines.length > 0) { process("preview") } };

</script>

<svelte:window on:keydown={handleKeydown}/>
<div><em>{currentTxt}</em></div>
<div class="svelte-component-main">
  {#if disableInterface}
  <div class="interface-mask">
    {#if !USER_AUTHENTICATED}
    <div class="signin-reminder">
      <p><em>
        <!-- svelte-ignore a11y-invalid-attribute -->
        <a href="#" data-toggle="modal" data-target="#SigninModal" role="button" >sign in</a> or
        <a href="/account/signup">sign up</a> to proceed
      </em></p>
    </div>
    {:else}
    <p>currently splitting document<br><a href={DOCUMENT.urls.detail}>redirecting to document detail</a></p>
    <div id="interface-loading" class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
    {/if}
  </div>
  {/if}
  <nav id="hamnav">
    <div id="interaction-options" class="tb-top-item">
    
    <label>
      <input type=radio bind:group={currentInteraction} value="draw" checked>
      Draw
    </label>
    <label>
      <input type=radio bind:group={currentInteraction} value="modify">
      Modify
    </label>
    <label>
      <input type="checkbox" bind:checked={showPreview} />
      Show Preview
    </label>
    </div>
    
    <div class="tb-top-item">
      <button on:click={() => {process("split")}} disabled={divisions.length<=1}>Split</button>
      <button on:click={() => {process("no_split")}} disabled={divisions.length>0}>No Split Needed</button>
      <button title="Return to document detail" onclick="window.location.href='{DOCUMENT.urls.detail}'">Cancel</button>
      <button title="reset interface" disabled={unchanged} on:click={resetInterface}><i id="fs-icon" class="fa fa-refresh" /></button>
    </div>
  </nav>
  <div class="map-container" style="border-top: 1.5px solid rgb(150, 150, 150)">
      <div id="doc-viewer" class="map-item rounded-bottom"></div>
  </div>
</div>
