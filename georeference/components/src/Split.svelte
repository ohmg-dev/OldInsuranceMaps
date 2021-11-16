<script>

  import {onMount} from 'svelte';

  import 'ol/ol.css';
  import Map from 'ol/Map';
  import View from 'ol/View';
  import Feature from 'ol/Feature';

  import Polygon from 'ol/geom/Polygon';

  import IIIF from 'ol/source/IIIF';
  import ImageStatic from 'ol/source/ImageStatic';
  import VectorSource from 'ol/source/Vector';

  import IIIFInfo from 'ol/format/IIIFInfo';

  import TileLayer from 'ol/layer/Tile';
  import ImageLayer from 'ol/layer/Image';
  import VectorLayer from 'ol/layer/Vector';

  import Projection from 'ol/proj/Projection';


  import Zoom from 'ol/control/Zoom';
  import MousePosition from 'ol/control/MousePosition';
  import {createStringXY} from 'ol/coordinate';

  import Style from 'ol/style/Style';
  import Stroke from 'ol/style/Stroke';
  import Fill from 'ol/style/Fill';

  import Draw from 'ol/interaction/Draw';
  import Select from 'ol/interaction/Select';
  import Modify from 'ol/interaction/Modify';
  import Snap from 'ol/interaction/Snap';

  export let DOCUMENT;
  export let IMG_SIZE;
  export let CSRFTOKEN;
  export let INCOMING_DIVISIONS;
  export let INCOMING_CUTLINES;

  let polygonCount = 0;
  let showPreview = true;

  let iface = null;
  let cutLines = [];

  let currentInteraction = 'draw';
  let mapInteractions = [
    {id: 'draw', name: 'Draw'},
    {id: 'modify', name: 'Modify'}
  ];

  const imgWidth = IMG_SIZE[0];
  const imgHeight = IMG_SIZE[1];

  const extent = [0, 0, imgWidth, imgHeight];
  const mapCenter = [imgWidth/2, imgHeight/2];

  let projection = new Projection({
    code: 'whatdoesthismatter',
    units: 'pixels',
    extent: extent,
  });

  let SplitInterface = {

    init: function () {

      let mousePositionControl = new MousePosition({
        coordinateFormat: createStringXY(0),
        projection: projection,
        undefinedHTML: '&nbsp;',
        // comment the following two lines to have the mouse position
        // be placed within the map.
        // className: 'custom-mouse-position',
        // target: document.getElementById('mouse-position'),

      });

      let zoomControl = new Zoom({
        // target: 'zoom-control',
        // className: 'zoom-control',
      });

      this.map = new Map({
        target: 'doc-viewer',
        view: new View({
          projection: projection,
          center: mapCenter,
          zoom: 1,
          maxZoom: 8,
        }),
        controls: [zoomControl, mousePositionControl]
      });


      // this.map.addControl(mousePositionControl);

      this.initLayers();
      this.initInteractions(this);
      this.initSnapping(this);

      iface = this;
    },

    initLayers: function () {

      this.img_layer = new ImageLayer({
        source: new ImageStatic({
          url: DOCUMENT.urls.image,
          projection: projection,
          imageExtent: extent,
        }),
        // zIndex: 999,
      })
      this.map.addLayer(this.img_layer);

      this.previewLayer = new VectorLayer({
        source: new VectorSource(),
        style: new Style({
          fill: new Fill({ color: 'rgba(255, 29, 51, 0.1)', }),
          stroke: new Stroke({ color: 'rgba(255, 29, 51, 1)', width: 7.5, }),
        }),
        // zIndex: 1000,
      });
      this.map.addLayer(this.previewLayer);

      this.borderLayer = new VectorLayer({
        source: new VectorSource(),
        style: new Style({
          stroke: new Stroke({ color: '#fae200', width: 2, })
        }),
        // zIndex: 1001,
      });
      let border = new Feature({
        geometry: new Polygon([[
          [0,0], [imgWidth, 0], [imgWidth, imgHeight], [0, imgHeight], [0,0]
        ]]),
      });
      this.borderLayer.getSource().addFeature(border);
      this.map.addLayer(this.borderLayer);

      this.cutLayer = new VectorLayer({
        source: new VectorSource(),
        style: new Style({
          stroke: new Stroke({ color: '#fae200', width: 2, })
        }),
        // zIndex: 1002,
      });
      this.map.addLayer(this.cutLayer);

    },
    initInteractions: function (obj) {

      // create and add draw interaction
      self = obj;
      self.drawInteraction = new Draw({
        source: self.cutLayer.getSource(),
        type: 'LineString',
      });
      self.map.addInteraction(self.drawInteraction);
      self.drawInteraction.on('drawend', self.updateCutLines);

      // create and add select and modify interactions (used for modify action)
      self.selectInteraction = new Select({
        layers: [self.cutLayer],
      });
      // self.map.addInteraction(self.selectInteraction);

      // self.modifyInteraction = new Modify({
      //   features: self.selectInteraction.getFeatures(),
      // });
      self.modifyInteraction = new Modify({
        hitDetection: self.cutLayer,
        source: self.cutLayer.getSource()
      });


      let mapEl = document.getElementById('doc-viewer');
      self.modifyInteraction.on(['modifystart', 'modifyend'], function (evt) {
        mapEl.style.cursor = evt.type === 'modifystart' ? 'grabbing' : 'grab';
      });

      let overlaySource = self.modifyInteraction.getOverlay().getSource();
      overlaySource.on(['addfeature', 'removefeature'], function (evt) {
        mapEl.style.cursor = evt.type === 'addfeature' ? 'grab' : '';
      });
      self.modifyInteraction.on('modifyend', self.updateCutLines)

      self.map.addInteraction(self.modifyInteraction);


      // set events for modify action
      let selectedFeatures = self.selectInteraction.getFeatures();

      self.selectInteraction.on('change:active', function () {
        selectedFeatures.forEach(function (each) {
          selectedFeatures.remove(each);
        });
      });

    },
    initSnapping: function (obj) {
      self = obj;
      let snapToCutLines = new Snap({
        source: self.cutLayer.getSource(),
      });
      var snapToBorder = new Snap({
        source: self.borderLayer.getSource(),
      })
      self.map.addInteraction(snapToCutLines);
      self.map.addInteraction(snapToBorder);
    },
    reset: function () {
      iface.cutLayer.getSource().once('change', function() {})
      iface.cutLayer.getSource().clear();
      iface.previewLayer.getSource().clear();
      cutLines = [];
      polygonCount = 0;
    },
    refreshPreviewLayer: function(polygons) {
      iface.previewLayer.getSource().clear();
      polygonCount = polygons.length;
      polygons.forEach(function (item, index) {
        let feature = new Feature({
          geometry: new Polygon([item]),
          name: index
        });
        iface.previewLayer.getSource().addFeature(feature);
      })
    },
    updateCutLines: function (event) {
      let tempList = [];
      iface.cutLayer.getSource().forEachFeature( function(feature) {
        tempList.push(feature.getGeometry().getCoordinates())
      });
      // if this is triggered by a Draw event, then the current feature must be
      // added to the feature list because it isn't present instantaneously in cutLayer
      if (event.type == "drawend") {
        tempList.push(event.feature.getGeometry().getCoordinates())
      };
      cutLines = tempList;
      previewSplit()
    }
  }

  onMount(() => {
    SplitInterface.init();

    if (INCOMING_DIVISIONS != null) {iface.refreshPreviewLayer(INCOMING_DIVISIONS)}
  });

  $: {
    if (iface != null) {
      let mapEl = document.getElementById('doc-viewer');
      // switch interactions based on the radio buttons
      if (currentInteraction == "draw") {
        iface.drawInteraction.setActive(true);
        // iface.selectInteraction.setActive(false);
        iface.modifyInteraction.setActive(false);
        // mapEl.style.cursor = 'copy'
      } else if (currentInteraction == "modify") {


        iface.drawInteraction.setActive(false);
        // iface.selectInteraction.setActive(true);
        iface.modifyInteraction.setActive(true);
      }

      // toggle the visibility of the preview layer based on the checkbox
      iface.previewLayer.setVisible(showPreview);
    }
  }

  let key;

  function handleKeydown(event) {
    key = event.key;
    if (key == "Escape") {
      if (iface) { iface.drawInteraction.abortDrawing()}
    } else if (key == "a" || key == "A") {
      currentInteraction = "draw"
    } else if (key == "e" || key == "E") {
      currentInteraction = "modify"
    }
  }

  
  function previewSplit() { if ( cutLines.length > 0) { processCutlines("preview") } };
  function runSplit() { processCutlines("submit", false) };
  function noSplitNeeded() { processCutlines("submit", true) };

  function processCutlines(operation, noSplit) {

    let data = JSON.stringify({"lines": cutLines, "operation": operation, "no_split": noSplit});

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
        if (operation == "submit") {
          window.location.href = DOCUMENT.urls.progress_page;
        } else if (operation == "preview") {
          iface.refreshPreviewLayer(result['polygons'])
        }
      });
  }

</script>

<svelte:window on:keydown={handleKeydown}/>

<div class="svelte-component-main">
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
            {#if polygonCount > 1}
            <em>{polygonCount} {polygonCount === 1 ? 'part' : 'parts'} will be made</em>
            {/if}
            <button on:click={runSplit} disabled="{polygonCount <= 1 }">Split!</button>
            <button on:click={noSplitNeeded} disabled="{polygonCount > 1 }">Don't Split</button>
            <button title="reset interface" on:click={iface.reset}><i id="fs-icon" class="fa fa-refresh" /></button>
    </div>
  </nav>
  <div class="map-container" style="border-top: 1.5px solid rgb(150, 150, 150)">
      <div id="doc-viewer" class="map-item rounded-bottom"></div>
  </div>
</div>

<style>
</style>
