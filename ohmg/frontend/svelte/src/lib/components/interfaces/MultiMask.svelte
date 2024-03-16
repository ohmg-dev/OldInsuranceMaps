<script>
import {onMount} from 'svelte';

import IconContext from 'phosphor-svelte/lib/IconContext';

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

import {Draw, Snap} from 'ol/interaction';

import Style from 'ol/style/Style';
import Stroke from 'ol/style/Stroke';

import IconButton from '@components/base/IconButton.svelte';
import FullExtentButton from './buttons/FullExtentButton.svelte';
import ExpandElement from './buttons/ExpandElement.svelte';

import { iconProps, makeTitilerXYZUrl, makeBasemaps, makeModifyInteraction } from "@helpers/utils"
import Styles from '@helpers/ol-styles';

const styles = new Styles();

export let ANNOTATION_SET;
export let CSRFTOKEN;
export let DISABLED;
export let MAPBOX_API_KEY;
export let TITILER_HOST;
export let resetMosaic;

let currentLayer = null;

let leaveOkay = true;

let unchanged = true;
let mapView;

let layerLookup = {}
let layerLookupMaskedArr = [];
let layerLookupUnmaskedArr = [];
let layerLookupArr = [];

function updateLayerArr(){
  layerLookupArr = [];
  layerLookupMaskedArr = [];
  layerLookupUnmaskedArr = [];
  Object.entries(layerLookup).forEach(kV => {
    if (kV[1].feature === null) {
      layerLookupUnmaskedArr.push(kV[1])
    } else {
      layerLookupMaskedArr.push(kV[1])
    }
    layerLookupArr.push(kV[1])
  })
  layerLookupMaskedArr.sort((a, b) => a.layerDef.sort_order - b.layerDef.sort_order)
  layerLookupUnmaskedArr.sort((a, b) => a.layerDef.sort_order - b.layerDef.sort_order)
}

function addIncomingMasks() {
  if (ANNOTATION_SET.multimask_geojson) {
    const feats = new GeoJSON().readFeatures(ANNOTATION_SET.multimask_geojson, {
      featureProjection: "EPSG:3857"
    })
    feats.forEach( function (f) {
      trimShapeSource.addFeature(f)
    })
  }
}

  function createLayerLookup() {
    layerLookup = {};
    trimShapeSource.clear()
    ANNOTATION_SET.annotations.forEach( function(layerDef) {
      let newLayer = new TileLayer({
        source: new XYZ({
          url: makeTitilerXYZUrl({
            host: TITILER_HOST,
            url: layerDef.urls.cog
          }),
        }),
        extent: transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857")
      });

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

const trimShapeLayer = new VectorLayer({
    source: new VectorSource(),
    style: [styles.mmDraw, styles.vertexPoint],
    zIndex: 1001,
  });
const trimShapeSource = trimShapeLayer.getSource()
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

let map;
function MapViewer (elementId) {

  const targetElement = document.getElementById(elementId);

  // create map
  map = new Map({
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

  const modify = makeModifyInteraction(trimShapeLayer, trimShapeSource, targetElement, styles.mmModify)
  modify.on('modifyend', function (e) {
		unchanged = false;
	});
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
    if (ANNOTATION_SET.extent) {
      const extent3857 = transformExtent(ANNOTATION_SET.extent, "EPSG:4326", "EPSG:3857");
			mapView.map.getView().fit(extent3857);
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
  if (DISABLED) {
    window.alert("You do not have edit permissions for this multimask.");
    return
  }
  const outGeoJSON = {"type": "FeatureCollection", "features": []}
  layerLookupArr.forEach( function(layer) {
    if (layer.feature) {
      layer.feature.setProperties({"layer": layer.layerDef.slug})
      const wgs84feat = layer.feature.clone();
      wgs84feat.getGeometry().transform("EPSG:3857", "EPSG:4326")
      const featureGeoJSON = new GeoJSON().writeFeatureObject(wgs84feat, {
        rightHanded: true,
        decimals: 7,
      })
      outGeoJSON.features.push(featureGeoJSON);
    }
  })
  fetch(ANNOTATION_SET.urls.post, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json;charset=utf-8',
      'X-CSRFToken': CSRFTOKEN,
    },
    body: JSON.stringify({
      "operation": "set-mask",
      "multimaskGeoJSON": outGeoJSON,
      "volumeId": ANNOTATION_SET.volume_id,
      "categorySlug": ANNOTATION_SET.id,
    }),
  }).then(response => response.json())
    .then(result => {
    if (result.status == "success") {
      window.alert("Masks saved successfully.")
      unchanged = true;
      resetMosaic()
    } else {
      let errMsg = "Error! MultiMask not saved."
      errMsg += "\nYou must remove and remake the following masks:"
      result.message.forEach((e) => {
        errMsg += `\n${e[0]}\n  Reason: ${e[1]}`
      })
      window.alert(errMsg)
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
  if (!currentLayer) { currentLayer = feature.getProperties().layer }
  if (currentLayer && layerLookup[currentLayer]) {
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

</script>

<IconContext values={iconProps} >
<div id='mm-container' class="svelte-component-main">
  <div id="map-container" class="map-container" style="height: calc(100%-35px);">
    <div id="map-viewer" class="map-item rounded-bottom">

    </div>
    <div id="layer-panel" style="display: flex;">
      <div class="layer-section-header" style="border-top:none;">
        <FullExtentButton action={setMapExtent} />
        <ExpandElement elementId={'mm-container'} maps={[map]} />
      </div>
      <div id="layer-list" style="flex:2;">
        <div class="layer-section-header">
          <span>Unmasked</span>
        </div>
        <div class="layer-section-subheader" style="overflow-y:auto">
          {#each layerLookupUnmaskedArr as layer}		
            <div style="display:flex;">
              <IconButton style="tool-ui-secondary" icon="crop" title="add mask" action={() => addMask(layer)} />
              &nbsp;
              <button class="layer-entry" on:click={() => zoomToLayer(layer)} on:mouseover={() => showExtent(layer)} on:focus={null}>
                <span style="{currentLayer == layer.layerDef.slug ? 'color:red' : ''}">sheet {layer.layerDef.page_str}</span>
              </button>
            </div>
          {:else}
            <div>No layers</div>
          {/each}
        </div>
        <div class="layer-section-header">
          <span>Masked</span>
        </div>
        <div class="layer-section-subheader" style="overflow-y:auto">
          {#each layerLookupMaskedArr as layer}		
            <div style="display:flex;">
              <IconButton style="tool-ui-secondary" icon="trash" title="remove mask" action={() => layerRemoveMask(layer)} />
              &nbsp;
              <button class="layer-entry" on:click={() => zoomToLayer(layer)} on:mouseover={() => showExtent(layer)} on:focus={null}>
                <span style="{currentLayer == layer.layerDef.slug ? 'color:red' : ''}">sheet {layer.layerDef.page_str}</span>
              </button>
            </div>
          {:else}
            <div>No layers</div>
          {/each}
        </div>
      </div>
      <div class="layer-section-header">
          <IconButton style="tool-ui-secondary" icon="x" title="Cancel (reset)" action={resetInterface} disabled={unchanged || DISABLED} />
          <IconButton style="tool-ui-secondary" icon="check" title="Submit" action={submitMultiMask} disabled={unchanged || DISABLED} />
      </div>
    </div>
  </div>
</div>
</IconContext>
<style>

button.layer-entry {
  cursor: pointer;
  border: none;
  background: none;
}
button.layer-entry:hover {
  color: red;
}
</style>
