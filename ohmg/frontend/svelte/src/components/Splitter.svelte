<script>
  import { onMount } from 'svelte';

  import CheckSquareOffset from 'phosphor-svelte/lib/CheckSquareOffset';
  import Scissors from 'phosphor-svelte/lib/Scissors';
  import ArrowCounterClockwise from 'phosphor-svelte/lib/ArrowCounterClockwise';
  import X from 'phosphor-svelte/lib/X';

  import 'ol/ol.css';
  import View from 'ol/View';
  import Feature from 'ol/Feature';

  import Polygon from 'ol/geom/Polygon';

  import VectorSource from 'ol/source/Vector';

  import VectorLayer from 'ol/layer/Vector';

  import Projection from 'ol/proj/Projection';

  import Draw from 'ol/interaction/Draw';
  import Modify from 'ol/interaction/Modify';
  import Snap from 'ol/interaction/Snap';
  import LineString from 'ol/geom/LineString';

  import Styles from '../lib/ol-styles';
  import { submitPostRequest } from '../lib/requests';
  import { MapViewer } from '../lib/viewers';
  import { makeImageLayer } from '../lib/layers';
  import { DocMousePosition } from '../lib/controls';

  import Link from './common/Link.svelte';
  import ExpandElement from './buttons/ExpandElement.svelte';

  import Modal, { getModal } from './modals/BaseModal.svelte';
  import ConfirmNoSplitModal from './modals/ConfirmNoSplitModal.svelte';

  import ToolUIButton from './buttons/ToolUIButton.svelte';
  import ExtendSessionModal from './modals/ExtendSessionModal.svelte';

  const styles = new Styles();

  export let CONTEXT;
  export let DOCUMENT;

  let viewer;
  let showPreview = true;

  let cutLines = [];
  let divisions = [];

  let currentInteraction = 'draw';

  let unchanged = true;

  const sessionId = DOCUMENT.lock ? DOCUMENT.lock.session_id : null;

  let disableInterface = DOCUMENT.lock && DOCUMENT.lock.user.username != CONTEXT.user.username;
  let disableReason;
  let leaveOkay = true;
  let enableButtons = false;
  if (DOCUMENT.lock && DOCUMENT.lock.user.username == CONTEXT.user.username) {
    leaveOkay = false;
    enableButtons = true;
  }

  let countdown = 10;
  let timer;
  $: {
    if (countdown === 0) {
      if (timer) {
        clearInterval(timer);
        timer = null;
      }
    }
  }

  // show the extend session prompt 10 seconds before the session expires
  setTimeout(promptRefresh, CONTEXT.session_length * 1000 - 10000);

  let autoRedirect;
  function promptRefresh() {
    if (!leaveOkay) {
      getModal('modal-extend-session').open();
      leaveOkay = true;
      autoRedirect = setTimeout(cancelSplit, 10000);
      timer = setInterval(() => {
        countdown -= 1;
      }, 1000);
    }
  }

  let currentTxt;
  $: {
    if (DOCUMENT.regions.length > 0) {
      currentTxt =
        'This document has already been prepared! (It was split into ' + DOCUMENT.regions.length + ' documents.)';
    } else if (divisions.length <= 1) {
      currentTxt =
        'If this image needs to be split, draw cut-lines across it as needed. Click once to start or continue a line, double-click to finish.';
    } else {
      const linesTxt = cutLines.length + ' ' + (cutLines.length === 1 ? 'cut-line' : 'cut-lines');
      const divsTxt =
        divisions.length + ' new ' + (divisions.length === 1 ? 'document' : 'documents') + ' will be made';
      currentTxt = 'Split summary: ' + linesTxt + ' | ' + divsTxt;
    }
  }

  const imgWidth = DOCUMENT.image_size[0];
  const imgHeight = DOCUMENT.image_size[1];
  const imgBorderPoly = [
    [
      [0, 0],
      [imgWidth, 0],
      [imgWidth, imgHeight],
      [0, imgHeight],
      [0, 0],
    ],
  ];

  const imgExtent = [0, 0, imgWidth, imgHeight];
  const projection = new Projection({
    code: 'whatdoesthismatter',
    units: 'pixels',
    extent: imgExtent,
  });

  function resetInterface() {
    cutLayerSource.clear();
    previewLayerSource.clear();
    cutLines = [];
    divisions = [];
    DOCUMENT.cutlines.forEach(function (line) {
      cutLayerSource.addFeature(new Feature({ geometry: new LineString(line) }));
    });
    unchanged = true;
    viewer.resetExtent();
  }

  const docLayer = makeImageLayer(DOCUMENT.urls.image, projection, imgExtent);

  const previewLayerSource = new VectorSource();
  const previewLayer = new VectorLayer({
    source: previewLayerSource,
    style: styles.splitPreviewStyle,
  });

  const borderLayer = new VectorLayer({
    source: new VectorSource({
      features: [
        new Feature({
          geometry: new Polygon(imgBorderPoly),
        }),
      ],
    }),
    style: styles.splitBorderStyle,
  });

  const cutLayerSource = new VectorSource();
  cutLayerSource.on('addfeature', function (e) {
    cutLines.push(e.feature.getGeometry().getCoordinates());
    unchanged = false;
    getPreview();
  });
  const cutLayer = new VectorLayer({
    source: cutLayerSource,
    style: styles.splitBorderStyle,
  });

  onMount(() => {
    // docView = new DocViewer("doc-viewer");
    viewer = new MapViewer('doc-viewer');

    viewer.setDefaultExtent(imgExtent);
    viewer.setView(
      new View({
        projection: projection,
        zoom: 1,
        maxZoom: 8,
      }),
    );
    viewer.resetExtent();

    // add control
    viewer.addControl(new DocMousePosition(imgExtent, null, 'ol-mouse-position'));

    // add layers
    viewer.addLayer(docLayer);
    viewer.addLayer(previewLayer);
    viewer.addLayer(borderLayer);
    viewer.addLayer(cutLayer);

    // add interactions
    viewer.addInteraction(
      'draw',
      new Draw({
        source: cutLayerSource,
        type: 'LineString',
        style: styles.polyDraw,
      }),
    );

    const modify = new Modify({
      source: cutLayerSource,
      style: styles.polyModify,
    });

    modify.on(['modifystart', 'modifyend'], function (evt) {
      viewer.element.style.cursor = evt.type === 'modifystart' ? 'grabbing' : 'grab';
    });

    const overlaySource = modify.getOverlay().getSource();
    overlaySource.on(['addfeature', 'removefeature'], function (evt) {
      viewer.element.style.cursor = evt.type === 'addfeature' ? 'grab' : '';
    });
    modify.on('modifyend', function (e) {
      cutLines = [];
      cutLayerSource.forEachFeature(function (feature) {
        cutLines.push(feature.getGeometry().getCoordinates());
      });
      unchanged = false;
      getPreview();
    });

    viewer.addInteraction('modify', modify);
    viewer.interactions.modify.setActive(false);

    viewer.addInteraction(
      'snapToCutlines',
      new Snap({
        source: cutLayer.getSource(),
      }),
    );
    viewer.addInteraction(
      'snapToBorder',
      new Snap({
        source: borderLayer.getSource(),
      }),
    );

    // resetInterface();
    if (!CONTEXT.user.is_authenticated) {
      getModal('modal-anonymous').open();
    }
  });

  $: {
    previewLayerSource.clear();
    divisions.forEach(function (item, index) {
      let feature = new Feature({
        geometry: new Polygon([item]),
        name: index,
      });
      previewLayerSource.addFeature(feature);
    });
  }

  $: {
    if (viewer) {
      // switch interactions based on the radio buttons
      if (currentInteraction == 'draw') {
        viewer.interactions.draw.setActive(true);
        viewer.interactions.modify.setActive(false);
      } else if (currentInteraction == 'modify') {
        viewer.interactions.draw.setActive(false);
        viewer.interactions.modify.setActive(true);
      }
    }
  }

  $: {
    previewLayer.setVisible(showPreview);
  }

  function handleKeydown(event) {
    const key = event.key;
    if (key == 'Escape') {
      if (viewer) {
        viewer.interactions.draw.abortDrawing();
      }
    } else if (key == 'a' || key == 'A') {
      currentInteraction = 'draw';
    } else if (key == 'e' || key == 'E') {
      currentInteraction = 'modify';
    }
  }

  function cancelSplit() {
    disableReason = 'cancel';
    leaveOkay = true;
    disableInterface = true;

    submitPostRequest(
      `/split/${DOCUMENT.id}/`,
      CONTEXT.ohmg_post_headers,
      'cancel',
      {
        sessionId: sessionId,
      },
      (result) => {
        if (result.success) {
          window.location.href = `/map/${DOCUMENT.map}`;
        } else {
          alert(result.message);
        }
      },
    );
  }

  function submitSplit() {
    disableReason = 'split';
    leaveOkay = true;
    disableInterface = true;

    submitPostRequest(
      `/split/${DOCUMENT.id}/`,
      CONTEXT.ohmg_post_headers,
      'split',
      {
        sessionId: sessionId,
        lines: cutLines,
      },
      (result) => {
        if (result.success) {
          window.location.href = `/map/${DOCUMENT.map}`;
        } else {
          alert(result.message);
        }
      },
    );
  }

  function getPreview() {
    if (cutLines.length == 0) {
      return;
    }

    submitPostRequest(
      `/split/${DOCUMENT.id}/`,
      CONTEXT.ohmg_post_headers,
      'preview',
      {
        sessionId: sessionId,
        lines: cutLines,
      },
      (result) => {
        divisions = result.payload.divisions;
      },
    );
  }

  function confirmLeave() {
    event.preventDefault();
    event.returnValue = '';
    return '...';
  }

  function cleanup() {
    // if this is an in-progress session for the current user
    if (DOCUMENT.lock && DOCUMENT.lock.user.username == CONTEXT.user.username && !leaveOkay) {
      cancelSplit();
    }
  }

  function handleExtendSession(response) {
    leaveOkay = false;
    clearTimeout(autoRedirect);
    setTimeout(promptRefresh, CONTEXT.session_length * 1000 - 10000);
  }
</script>

<svelte:window
  on:keydown={handleKeydown}
  on:beforeunload={() => {
    if (!leaveOkay) {
      confirmLeave();
    }
  }}
  on:unload={cleanup}
/>

<ExtendSessionModal {CONTEXT} {sessionId} callback={handleExtendSession} bind:countdown />
<Modal id="modal-anonymous">
  <p>
    Feel free to experiment with the interface, but to submit your work you must
    <Link href={'/account/login'}>sign in</Link> or
    <Link href={'/account/signup'}>sign up</Link>.
  </p>
</Modal>

<Modal id="modal-finished">
  <p>This document has already been prepared!</p>
</Modal>
<Modal id="modal-cancel">
  <p>Are you sure you want to cancel this session?</p>
  <button
    class="button is-success"
    title="Cancel and redirect"
    on:click={() => {
      cancelSplit();
      getModal('modal-cancel').close();
    }}>Yes</button
  >
  <button
    class="button is-danger"
    title="Continue session"
    on:click={() => {
      getModal('modal-cancel').close();
    }}>No - keep working</button
  >
</Modal>
<ConfirmNoSplitModal
  documentId={DOCUMENT.id}
  {CONTEXT}
  {sessionId}
  callback={() => {
    leaveOkay = true;
    window.location.href = `/map/${DOCUMENT.map}`;
  }}
/>
<div style="height:25px">
  {currentTxt}
  <Link href="https://about.oldinsurancemaps.net/guides/preparation/" external={true}>Learn more</Link>
</div>
<div id="map-container" style="height:calc(100vh - 205px)" class="svelte-component-main">
  {#if disableInterface}
    <div class="interface-mask">
      <div class="signin-reminder">
        {#if DOCUMENT.lock}
          <p>Document currently locked for processing by {DOCUMENT.lock.user.username}</p>
        {:else if disableReason == 'split'}
          <p>Processing document split... redirecting to document detail.</p>
        {:else if disableReason == 'no_split'}
          <p>Document prepared and ready to georeference.</p>
        {:else if disableReason == 'cancel'}
          <p>Cancelling preparation.</p>
        {/if}
      </div>
    </div>
  {/if}
  <nav id="hamnav">
    <div id="interaction-options" class="tb-top-item">
      <label>
        <input type="radio" bind:group={currentInteraction} value="draw" checked />
        Draw
      </label>
      <label>
        <input type="radio" bind:group={currentInteraction} value="modify" />
        Modify
      </label>
      <label>
        <input type="checkbox" bind:checked={showPreview} />
        Show Preview
      </label>
    </div>
    <div class="control-btn-group">
      <ToolUIButton action={submitSplit} title="Run split operation" disabled={divisions.length <= 1 || !enableButtons}>
        <Scissors />
      </ToolUIButton>
      <ToolUIButton
        action={() => {
          getModal('modal-confirm-no-split').open();
        }}
        title="No split needed"
        disabled={divisions.length > 0 || !enableButtons}
      >
        <CheckSquareOffset />
      </ToolUIButton>
      <ToolUIButton
        action={() => {
          getModal('modal-cancel').open();
        }}
        title="Cancel this preparation"
        disabled={sessionId == null || !enableButtons}
      >
        <X />
      </ToolUIButton>
      <ToolUIButton action={resetInterface} title="Reset interface" disabled={unchanged}>
        <ArrowCounterClockwise />
      </ToolUIButton>
      <ExpandElement elementId="map-container" />
    </div>
  </nav>
  <div class="map-container" style="border-top: 1.5px solid rgb(150, 150, 150)">
    <div id="doc-viewer" class="map-item rounded-bottom"></div>
  </div>
</div>
