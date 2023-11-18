<script>
import {onMount} from 'svelte';

import IconContext from 'phosphor-svelte/lib/IconContext';
import { iconProps } from "../js/utils"

import ArrowSquareOut from "phosphor-svelte/lib/ArrowSquareOut";
import ArrowsOutSimple from "phosphor-svelte/lib/ArrowsOutSimple";
import ArrowsInSimple from "phosphor-svelte/lib/ArrowsInSimple";
import CheckSquareOffset from "phosphor-svelte/lib/CheckSquareOffset";
import Scissors from "phosphor-svelte/lib/Scissors";
import ArrowCounterClockwise from "phosphor-svelte/lib/ArrowCounterClockwise";
import X from "phosphor-svelte/lib/X";

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
import LineString from 'ol/geom/LineString';

import Styles from '../js/ol-styles';
import {toggleFullscreen} from '../js/utils';

import TitleBar from './components/TitleBar.svelte';
import Modal, {getModal} from './components/Modal.svelte';

const styles = new Styles();

export let USER;
export let SESSION_LENGTH;
export let DOCUMENT;
export let CSRFTOKEN;
export let VOLUME;

let docView;
let showPreview = true;

let cutLines = [];
let divisions = [];

let currentInteraction = 'draw';

let unchanged = true;

const session_id = DOCUMENT.lock_enabled ? DOCUMENT.lock_details.session_id : null;

let disableInterface = DOCUMENT.lock_enabled && (DOCUMENT.lock_details.user.name != USER);
let disableReason;
let leaveOkay = true;
let enableButtons = false;
if (DOCUMENT.lock_enabled && (DOCUMENT.lock_details.user.name == USER)) {
  leaveOkay = false;
  enableButtons = true;
}

// show the extend session prompt 10 seconds before the session expires
setTimeout(promptRefresh, (SESSION_LENGTH*1000) - 10000)

let autoRedirect;
function promptRefresh() {
  if (!leaveOkay) {
    if (document.fullscreenElement != null) {  document.exitFullscreen(); }
    getModal('modal-expiration').open()
    leaveOkay = true;
    autoRedirect = setTimeout(cancelAndRedirectToDetail, 10000);
  }
}

function cancelAndRedirectToDetail() {
  process("cancel");
}

let currentTxt;
$: {
  if (DOCUMENT.status == "prepared" || DOCUMENT.status == "georeferenced") {
    if (DOCUMENT.parent) {
      currentTxt = "This document has already been prepared! (It was split from another document.)"
    } else {
      "This document has already been prepared! (It did not need to be split.)"
    }
  } else if (DOCUMENT.status == "split") {
    currentTxt = "This document has already been prepared! (It was split into "+DOCUMENT.children.length+" documents.)"
  } else if (divisions.length <= 1) {
    currentTxt = "If this image needs to be split, draw cut-lines across it as needed. Click once to start or continue a line, double-click to finish."
  } else {
    const linesTxt = cutLines.length + " " + (cutLines.length === 1 ? 'cut-line' : 'cut-lines');
    const divsTxt = divisions.length + " new " + (divisions.length === 1 ? 'document' : 'documents') + " will be made";
    currentTxt = "Split summary: " + linesTxt + " | " + divsTxt;
  }
}


const imgWidth = DOCUMENT.image_size[0];
const imgHeight = DOCUMENT.image_size[1];
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
  DOCUMENT.cutlines.forEach(function(line) {
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

onMount(() => {
  docView = new DocViewer("doc-viewer");
  resetInterface();
  if (!USER) { getModal('modal-anonymous').open() }
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

  if (operation == "no_split") {
    if (!confirm("Are you sure this document does not need to be split?")) {
      return
    }
  }

  if (operation == "split" || operation == "no_split" || operation == "cancel") {
    disableReason = operation;
    leaveOkay = true;
    disableInterface = true;
  };

  if (operation == "extend-session") {
    leaveOkay = false;
    clearTimeout(autoRedirect)
    setTimeout(promptRefresh, (SESSION_LENGTH*1000) - 10000)
  }

  let data = JSON.stringify({
    "lines": cutLines,
    "operation": operation,
    "sesh_id": session_id,
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
      if (operation == "preview") {
        divisions = result['divisions'];
      } else if (operation == "split") {
        window.location.href = VOLUME.urls.summary;
      } else if (operation == "no_split") {
        window.location.href = DOCUMENT.urls.georeference;
      } else if (operation == "cancel") {
        window.location.href = VOLUME.urls.summary;
      }
    });
}

function previewSplit() { if ( cutLines.length > 0) { process("preview") } };

function confirmLeave () {
  event.preventDefault();
  event.returnValue = "";
  return "...";
}

function cleanup () {
  // if this is an in-progress session for the current user
  if (DOCUMENT.lock_enabled && (DOCUMENT.lock_details.user.name == USER)) {
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
    enabled: false,
    iconClass: 'layer',
    alt: '',
    url: '',
  },
  {
    visible: true,
    enabled: true,
    iconClass: 'volume',
    alt: 'Go to volume: ' + VOLUME.title,
    url: VOLUME.urls.summary,
  }
]

let inFullscreen = false;

</script>
<svelte:window on:keydown={handleKeydown} on:beforeunload={() => {if (!leaveOkay) {confirmLeave()}}} on:unload={cleanup}/>
<IconContext values={iconProps}>
<Modal id="modal-expiration">
  <p>This preparation session is expiring, and will be cancelled soon.</p>
  <button on:click={() => {
    process("extend-session");
    getModal('modal-expiration').close()}
    }>Give me more time!</button>
</Modal>

<Modal id="modal-anonymous">
  <p>Feel free to experiment with the interface, but submit your work you must 
    <a href="/account/login">sign in</a> or
    <a href="/account/signup">sign up</a>.
  </p>
</Modal>

<Modal id="modal-finished">
  <p>This document has already been prepared!</p>
</Modal>

<TitleBar TITLE={DOCUMENT.title} SIDE_LINKS={[]} ICON_LINKS={iconLinks}/>
<p>{currentTxt} <a href="https://ohmg.dev/docs/making-the-mosaics/preparation" target="_blank">Learn more<ArrowSquareOut /></a></p>
<div id="map-container" class="svelte-component-main">
  {#if disableInterface}
  <div class="interface-mask">
    <div class="signin-reminder">
      {#if DOCUMENT.lock_enabled}
      <p>Document currently locked for processing by {DOCUMENT.lock_details.user.name}</p>
      {:else if disableReason == "split"}
      <p>Processing document split... redirecting to document detail.</p>
      <div id="interface-loading" class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
      {:else if disableReason == "no_split"}
      <p>Document prepared and ready to georeference.</p>
      <div id="interface-loading" class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
      {:else if disableReason == "cancel"}
      <p>Cancelling preparation.</p>
      <div id="interface-loading" class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
      {/if}
    </div>
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
    
    <div class="control-btn-group">
      <button class="control-btn tool-ui" title="Run split operation" disabled={divisions.length<=1 || !enableButtons} on:click={() => {process("split")}}>
        <Scissors />
      </button>
      <button class="control-btn tool-ui" title="No split needed" disabled={divisions.length>0 || !enableButtons} on:click={() => {process("no_split")}}>
        <CheckSquareOffset />
      </button>
      <button class="control-btn tool-ui" title="Cancel this preparation" disabled={session_id == null || !enableButtons} on:click={() => {process("cancel")}}>
        <X />
      </button>
      <button class="control-btn tool-ui" title="Reset interface" disabled={unchanged} on:click={resetInterface}>
        <ArrowCounterClockwise />
      </button>
      <button class="control-btn tool-ui" title={inFullscreen ? "Exit fullscreen" : "Enter fullscreen"} on:click={() => {inFullscreen = toggleFullscreen('map-container')}}>
        {#if inFullscreen}
        <ArrowsInSimple />
        {:else}
        <ArrowsOutSimple />
        {/if}
      </button>
    
    </div>
  </nav>
  <div class="map-container" style="border-top: 1.5px solid rgb(150, 150, 150)">
      <div id="doc-viewer" class="map-item rounded-bottom"></div>
  </div>
</div>
</IconContext>