<script>
import {onMount} from 'svelte';

import CheckSquareOffset from "phosphor-svelte/lib/CheckSquareOffset";
import Scissors from "phosphor-svelte/lib/Scissors";
import ArrowCounterClockwise from "phosphor-svelte/lib/ArrowCounterClockwise";
import X from "phosphor-svelte/lib/X";

import Link from "@components/base/Link.svelte";
import ExpandElement from "./buttons/ExpandElement.svelte"

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

import Styles from '@lib/ol-styles';

import Modal, {getModal} from '@components/base/Modal.svelte';
import ToolUIButton from '@components/base/ToolUIButton.svelte';

const styles = new Styles();

export let CONTEXT;
export let DOCUMENT;

let docView;
let docViewMap;
let showPreview = true;

let cutLines = [];
let divisions = [];

let currentInteraction = 'draw';

let unchanged = true;

const session_id = DOCUMENT.lock ? DOCUMENT.lock.session_id : null;

let disableInterface = DOCUMENT.lock && (DOCUMENT.lock.user.username != CONTEXT.user.username);
let disableReason;
let leaveOkay = true;
let enableButtons = false;
if (DOCUMENT.lock && (DOCUMENT.lock.user.username == CONTEXT.user.username)) {
  leaveOkay = false;
  enableButtons = true;
}

// show the extend session prompt 10 seconds before the session expires
setTimeout(promptRefresh, (CONTEXT.session_length*1000) - 10000)

let autoRedirect;
function promptRefresh() {
  if (!leaveOkay) {
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
  if (DOCUMENT.regions.length > 0) {
    currentTxt = "This document has already been prepared! (It was split into "+DOCUMENT.regions.length+" documents.)"
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
    zoom: 1.5,
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

  docViewMap = map;
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
  if (!CONTEXT.user.is_authenticated) { getModal('modal-anonymous').open() }
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

  if (operation == "split" || operation == "no_split" || operation == "cancel") {
    disableReason = operation;
    leaveOkay = true;
    disableInterface = true;
  };

  if (operation == "extend-session") {
    leaveOkay = false;
    clearTimeout(autoRedirect)
    setTimeout(promptRefresh, (CONTEXT.session_length*1000) - 10000)
  }

  let data = JSON.stringify({
    "lines": cutLines,
    "operation": operation,
    "sesh_id": session_id,
  });

  fetch(DOCUMENT.urls.split, {
      method: 'POST',
      headers: CONTEXT.ohmg_post_headers,
      body: data,
    })
    .then(response => response.json())
    .then(result => {
      if (operation == "preview") {
        divisions = result['divisions'];
      } else if (operation == "split") {
        window.location.href = `/map/${DOCUMENT.map}`;
      } else if (operation == "no_split") {
        window.location.href = `/georeference/${result.region_id}`;
      } else if (operation == "cancel") {
        window.location.href = `/map/${DOCUMENT.map}`;
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
  if (DOCUMENT.lock && (DOCUMENT.lock.user.username == CONTEXT.user.username)) {
    process("cancel")
  }
}

</script>
<svelte:window on:keydown={handleKeydown} on:beforeunload={() => {if (!leaveOkay) {confirmLeave()}}} on:unload={cleanup}/>

<Modal id="modal-expiration">
  <p>This preparation session is expiring, and will be cancelled soon.</p>
  <button class="button is-success" on:click={() => {
    process("extend-session");
    getModal('modal-expiration').close()}
    }>Give me more time!</button>
</Modal>

<Modal id="modal-anonymous">
  <p>Feel free to experiment with the interface, but to submit your work you must 
    <Link href={"/account/login"}>sign in</Link> or
    <Link href={"/account/signup"}>sign up</Link>.
  </p>
</Modal>

<Modal id="modal-finished">
  <p>This document has already been prepared!</p>
</Modal>
<Modal id="modal-cancel">
	<p>Are you sure you want to cancel this session?</p>
  <button class="button is-success"
    on:click={() => {
      process("cancel");
      getModal('modal-cancel').close()
    }}>Yes</button>
  <button class="button is-danger"
    on:click={() => {
      getModal('modal-cancel').close()}
    }>No - keep working</button>
</Modal>
<Modal id="modal-confirm-no-split">
	<p>Are you sure this document does not need to be split?</p>
  <button class="button is-success"
    on:click={() => {
      process("no_split");
      getModal('modal-confirm-no-split').close()
    }}>Yes - it only contains one map</button>
  <button class="button is-danger"
    on:click={() => {
      getModal('modal-confirm-no-split').close()}
    }>Cancel</button>
</Modal>
<div style="height:25px">
  {currentTxt} <Link href="https://about.oldinsurancemaps.net/guides/preparation/" external={true}>Learn more</Link>
</div>
<div id="map-container" style="height:calc(100vh - 205px)" class="svelte-component-main">
  {#if disableInterface}
  <div class="interface-mask">
    <div class="signin-reminder">
      {#if DOCUMENT.lock}
      <p>Document currently locked for processing by {DOCUMENT.lock.user.username}</p>
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
      <ToolUIButton action={() => {process("split")}} title="Run split operation" disabled={divisions.length<=1 || !enableButtons}>
        <Scissors />
      </ToolUIButton>
      <ToolUIButton action={() => { getModal('modal-confirm-no-split').open() }} title="No split needed" disabled={divisions.length>0 || !enableButtons}>
        <CheckSquareOffset />
      </ToolUIButton>
      <ToolUIButton action={() => { getModal('modal-cancel').open() }} title="Cancel this preparation" disabled={session_id == null || !enableButtons}>
        <X />
      </ToolUIButton>
      <ToolUIButton action={resetInterface} title="Reset interface" disabled={unchanged}>
        <ArrowCounterClockwise />
      </ToolUIButton>
      <ExpandElement elementId="map-container" maps={[docViewMap]} />
    </div>
  </nav>
  <div class="map-container" style="border-top: 1.5px solid rgb(150, 150, 150)">
      <div id="doc-viewer" class="map-item rounded-bottom"></div>
  </div>
</div>
