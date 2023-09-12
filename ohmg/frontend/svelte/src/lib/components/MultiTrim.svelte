<script>
import {onMount} from 'svelte';

import Icon from 'svelte-icons-pack/Icon.svelte';
import FiCrop from 'svelte-icons-pack/fi/FiCrop';
import FiHome from 'svelte-icons-pack/fi/FiHome';
import FiTrash from 'svelte-icons-pack/fi/FiTrash';
import FiCheck from 'svelte-icons-pack/fi/FiCheck';
import FiX from 'svelte-icons-pack/fi/FiX';
import FiMaximize from 'svelte-icons-pack/fi/FiMaximize';
import FiMaximize2 from 'svelte-icons-pack/fi/FiMaximize2';
import FiMinimize2 from 'svelte-icons-pack/fi/FiMinimize2';

import 'ol/ol.css';
import Map from 'ol/Map';
import View from 'ol/View';

import VectorSource from 'ol/source/Vector';
import XYZ from 'ol/source/XYZ';

import {transformExtent} from 'ol/proj';

import {createEmpty, extend} from 'ol/extent';

import Feature from 'ol/Feature';

import GeoJSON from 'ol/format/GeoJSON';
import {fromExtent} from 'ol/geom/Polygon';

import TileLayer from 'ol/layer/Tile';
import VectorLayer from 'ol/layer/Vector';

import Crop from 'ol-ext/filter/Crop';

import MousePosition from 'ol/control/MousePosition';
import {createStringXY} from 'ol/coordinate';

import {Draw, Modify, Snap} from 'ol/interaction';

import Style from 'ol/style/Style';
import Stroke from 'ol/style/Stroke';

import Styles from '../../js/ol-styles';
const styles = new Styles();

import {toggleFullscreen, makeTitilerXYZUrl, makeBasemaps} from '../../js/utils';

export let VOLUME;
// export let SESSION_LENGTH;
export let CSRFTOKEN;
export let USER_TYPE;
export let MAPBOX_API_KEY;
export let TITILER_HOST;

let currentLayer = null;

let leaveOkay = true;

let unchanged = true;
let mapView;

let layerLookup = {}
let layerLookupArr = [];

function updateLayerArr(){
  layerLookupArr = []
  Object.entries(layerLookup).forEach(kV => {
    layerLookupArr.push(kV[1])
  })
}

function addIncomingMasks() {
	if (VOLUME.multimask) {
		Object.entries(VOLUME.multimask).forEach(kV => {
			currentLayer = kV[0]
			const feature = new GeoJSON().readFeature(kV[1])
			feature.getGeometry().transform("EPSG:4326", "EPSG:3857")
			trimShapeSource.addFeature(feature)
		});
		currentLayer = null;
	}
}

  function createLayerLookup() {
    layerLookup = {};
    trimShapeSource.clear()
    VOLUME.sorted_layers.main.forEach( function(layerDef, n) {
      // create the actual ol layers and add to group.
      let newLayer = new TileLayer({
        source: new XYZ({
          url: makeTitilerXYZUrl({
            host: TITILER_HOST,
            url: layerDef.urls.cog
          }),
        }),
        extent: transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857")
      });
      // zIndex for layers start from 100, should max out under 300.
      // When a layer is shuffled to the top, it's zIndex is set to 500,
      // and ally layers with a zIndex > 300 are shifted down 1.
      // This should allow for plenty of shuffling without disruption to
      // the lower-level layers.

      // make extent
      const extentGeom4326 = fromExtent(transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857"));
      const extentGeom3857 = extentGeom4326.clone()
      const extentFeature = new Feature({
          geometry: extentGeom3857,
          show: false,
          name: layerDef.slug,
      });
      extentLayer.getSource().addFeature(extentFeature)

      layerLookup[layerDef.slug] = {}
      const layer = {
        olLayer: newLayer,
        layerDef: layerDef,
        crop: null,
        feature: null
      }
      layerLookup[layerDef.slug] = layer
    });
    // now iterate the incoming mask features and apply all existing
    addIncomingMasks();
    updateLayerArr();
    unchanged = true;
  }

const basemaps = makeBasemaps(MAPBOX_API_KEY)
const osmBasemap = basemaps[0]
osmBasemap.layer.setZIndex(0)

const redOutline = new Style({
  stroke: new Stroke({ color: 'red', width: .75, lineDash: [2]}),
});

function extentLayerStyle (feature, resolution) {
    const prop = feature.getProperties();
    if (prop.show) {
      return redOutline;
    }
    return
}

var extentLayer = new VectorLayer({
    source: new VectorSource,
    style: extentLayerStyle,
    zIndex: 1000
});


const trimShapeSource = new VectorSource();
const trimShapeLayer = new VectorLayer({
    source: trimShapeSource,
    style: [styles.mmDraw, styles.vertexPoint],
    zIndex: 1001,
  });
trimShapeSource.on("addfeature", function(e) {
  layerApplyMask(e.feature);
})

function resetInterface() {
  layerLookupArr.forEach(function(layer) {
    layerRemoveMask(layer, true)
  })
  addIncomingMasks();
  unchanged = true;
}

  // this Modify interaction is created individually for each map panel
function makeModifyInteraction(hitDetection, source, targetElement) {
  const modify = new Modify({
    hitDetection: hitDetection,
    source: source,
    style: styles.mmModify,
  });

  modify.on(['modifystart', 'modifyend'], function (e) {
    targetElement.style.cursor = e.type === 'modifystart' ? 'grabbing' : 'pointer';
    if (e.type == "modifyend") {
      unchanged = false;
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
    layers: [osmBasemap.layer],
    view: new View({
    zoom: 16,
    })
  });

  layerLookupArr.forEach( function(layer) {
    map.addLayer(layer.olLayer)
  });

  map.addLayer(trimShapeLayer)
  map.addLayer(extentLayer)

  // create interactions
  const draw = new Draw({
    source: trimShapeSource,
    type: 'Polygon',
    style: styles.mmDraw,
  });
  map.addInteraction(draw)

  const modify = makeModifyInteraction(trimShapeLayer, trimShapeSource, targetElement)
  map.addInteraction(modify)

  const snap = new Snap({
    source: trimShapeSource,
    edge: false,
  });
  map.addInteraction(snap)

  // create controls
  let mousePositionControl = new MousePosition({
    projection: 'EPSG:4326',
    coordinateFormat: createStringXY(6),
    undefinedHTML: 'n/a',
  });
  map.addControl(mousePositionControl);

  // expose properties as necessary
  this.map = map;
  this.element = targetElement;
  this.drawInteraction = draw;
  this.modifyInteraction = modify

}

function setMapExtent() {
	if (mapView) {
		if (layerLookupArr.length > 0) {
			const fullExtent = createEmpty();
			layerLookupArr.forEach( function(layer) {
				const extent3857 = transformExtent(layer.layerDef.extent, "EPSG:4326", "EPSG:3857");
				extend(fullExtent, extent3857)
			});
			mapView.map.getView().fit(fullExtent);
		} else {
			mapView.map.getView().setCenter([0,0]);
			mapView.map.getView().setZoom(1)
		}
	}
}

onMount(() => {
  createLayerLookup();
  mapView = new MapViewer("map-viewer");
  setMapExtent()
});

$: {
  if (mapView) {
    mapView.drawInteraction.setActive(currentLayer != null)
    mapView.modifyInteraction.setActive(!mapView.drawInteraction.getActive())
  }
}

function submitMultiMask() {
  if (USER_TYPE == "anonymous") {
    window.alert("You must be signed to save");
    return
  }
  let multiMask = {}
  layerLookupArr.forEach( function(layer) {
    if (layer.feature) {
      const wgs84feat = layer.feature.clone();
      wgs84feat.getGeometry().transform("EPSG:3857", "EPSG:4326")
      const featureGeoJSONStr = new GeoJSON().writeFeature(wgs84feat, {
        rightHanded: true,
        decimals: 7,
      })
      multiMask[layer.layerDef.slug] = JSON.parse(featureGeoJSONStr);
    }
  })
  fetch(VOLUME.urls.trim, {
    method: 'POST',
    headers: {
    'Content-Type': 'application/json;charset=utf-8',
    'X-CSRFToken': CSRFTOKEN,
    },
    body: JSON.stringify({"multiMask": multiMask}),
  }).then(response => response.json())
    .then(result => {
    if (result.status == "ok") {
      // window.location.href = VOLUME.urls.summary
      window.alert("Masks saved successfully.")
      unchanged = true;
      VOLUME = result.volume_json;
    } else {
      window.alert("Error while saving.")
    }
  })
}

function zoomToLayer(layer) {
  if (mapView) {
    const extent3857 = transformExtent(layer.layerDef.extent, "EPSG:4326", "EPSG:3857");
    mapView.map.getView().fit(extent3857)
    layerToTop(layer);
  }
  showExtent(layer)
}

function showExtent(layer) {
  extentLayer.getSource().getFeatures().forEach(function (feature) {
    const props = feature.getProperties();
    if (props.name == layer.layerDef.slug) {
      feature.setProperties({'show': true})
    } else {
      feature.setProperties({'show': false})
    }
  })
}

function layerToTop(layer) {
  layerLookupArr.forEach( function(otherLayer) {
    const z = otherLayer.olLayer.getZIndex();
    // push down layers that have previously been shoved to the top
    if (z>300) {
      otherLayer.olLayer.setZIndex(otherLayer.olLayer.getZIndex()-1)
    }
  })
  layer.olLayer.setZIndex(500);
}

function addMask(layer){
  if (mapView) {
    zoomToLayer(layer);
    // setting the currentLayer activates the draw interaction
    // and when the feature is complete it is used for the crop
    currentLayer = layer.layerDef.slug;
  }
  showExtent(layer)
}

function layerApplyMask(feature) {
  if (currentLayer) {
    if (layerLookup[currentLayer].feature) {
      trimShapeSource.removeFeature(layerLookup[currentLayer].feature)
      layerLookup[currentLayer].feature = null;
    }
    if (layerLookup[currentLayer].crop) {
      layerLookup[currentLayer].crop = null;
    }
    const crop = new Crop({ 
        feature: feature, 
        wrapX: true,
        inner: false
    });
    layerLookup[currentLayer].olLayer.addFilter(crop);
    layerLookup[currentLayer].crop = crop;
    layerLookup[currentLayer].feature = feature;
  }
  currentLayer = null;
  updateLayerArr()
  unchanged = false;
}


function layerRemoveMask(layer, confirm) {
  if (confirm != true) {
    confirm = window.confirm("Remove this mask?")
  } 
  if (confirm) {
    if (layer.crop) {
      layer.crop.set('active', false); 
    }
    trimShapeSource.removeFeature(layer.feature)
    layer.crop = null;
    layer.feature = null;
    updateLayerArr()
    unchanged = false;
  }

}

let inFullscreen = false;

</script>

{#if USER_TYPE == "anonymous"}<div><p>Feel free to mess around; you can't save changes unless you are logged in.</p></div>{/if}
<div class="svelte-component-main">
  <div id="map-container" class="map-container" style="height: calc(100%-35px);">
    <div id="map-viewer" class="map-item rounded-bottom">

    </div>
    <div id="layer-panel" style="display: flex;">
      <div class="layer-section-header" style="border-top:none;">
        <button class="control-btn tool-ui" title="Reset extent" on:click={setMapExtent}>
          <Icon src={FiMaximize} />
        </button>
        <button class="control-btn tool-ui" title={inFullscreen ? "Exit fullscreen" : "Enter fullscreen"} on:click={() => {inFullscreen = toggleFullscreen('map-container')}}>
          {#if inFullscreen}
          <Icon src={FiMinimize2} />
          {:else}
          <Icon src={FiMaximize2} />
          {/if}
        </button>
      </div>
      <div id="layer-list" style="flex:2;">
        
        <div class="layer-section-header">
          <span>Main Layers</span>
        </div>
        <div class="layer-section-subheader" style="overflow-y:auto">
          {#each layerLookupArr as layer}		
            <div style="display:flex;">
              {#if !layer.feature }
              <button class="control-btn" title="add mask" on:click={() => addMask(layer)} style="display: inline-block;">
                <Icon src={FiCrop} />
              </button>
              {:else}
              <button class="control-btn" title="remove mask" on:click={() => layerRemoveMask(layer)} style="display: inline-block;">
                <Icon src={FiTrash} />
              </button>
              {/if}
              &nbsp;
              {#if currentLayer == layer.layerDef.slug}
              <!-- svelte-ignore a11y-mouse-events-have-key-events -->
              <div style="color:red" on:mouseover={() => showExtent(layer)}>sheet {layer.layerDef.page_str}</div>
              {:else}
              <!-- svelte-ignore a11y-mouse-events-have-key-events -->
              <div class="layer-entry" on:click={() => zoomToLayer(layer)} on:mouseover={() => showExtent(layer)}>sheet {layer.layerDef.page_str}</div>
              {/if}
            </div>
          {:else}
            <div>No layers</div>
          {/each}
        </div>
      </div>
      <div class="layer-section-header">
          <button class="control-btn" title="Cancel (reset)" on:click={resetInterface} disabled={unchanged}>
            <Icon src={FiX} />
          </button>
          <button class="control-btn" title="Submit" on:click={submitMultiMask} disabled={unchanged}>
            <Icon src={FiCheck} />
          </button>
      </div>
    </div>
  </div>
</div>

<style>

.layer-entry {
  cursor: pointer;
}
.layer-entry:hover {
  color: red;
}
</style>
