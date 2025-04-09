<script>
  import { onMount } from 'svelte';

  import X from 'phosphor-svelte/lib/X';
  import Check from 'phosphor-svelte/lib/Check';
  import CropIcon from 'phosphor-svelte/lib/Crop';
  import MapPin from 'phosphor-svelte/lib/MapPin';
  import Trash from 'phosphor-svelte/lib/Trash';
  import CornersOut from 'phosphor-svelte/lib/CornersOut';

  import 'ol/ol.css';

  import VectorSource from 'ol/source/Vector';
  import XYZ from 'ol/source/XYZ';

  import { transformExtent } from 'ol/proj';

  import Feature from 'ol/Feature';

  import GeoJSON from 'ol/format/GeoJSON';
  import { fromExtent } from 'ol/geom/Polygon';

  import TileLayer from 'ol/layer/Tile';
  import VectorLayer from 'ol/layer/Vector';

  import Crop from 'ol-ext/filter/Crop';

  import { Draw, Snap, Modify } from 'ol/interaction';

  import ToolUIButton from '../buttons/ToolUIButton.svelte';
  import ExpandElement from '../buttons/ExpandElement.svelte';

  import { makeTitilerXYZUrl, usaExtent } from '../../lib/utils';
  import { submitPostRequest } from '../../lib/requests';
  import { MapViewer } from '../../lib/viewers';
  import { LyrMousePosition } from '../../lib/controls';
  import Styles from '../../lib/ol-styles';

  const styles = new Styles();

  export let CONTEXT;
  export let LAYERSET;
  export let DISABLED;
  export let resetMosaic;

  let currentLayer = null;

  let unchanged = true;

  let layerLookup = {};
  let layerLookupMaskedArr = [];
  let layerLookupUnmaskedArr = [];
  let layerLookupArr = [];

  const fullExtent = LAYERSET.extent ? transformExtent(LAYERSET.extent, 'EPSG:4326', 'EPSG:3857') : usaExtent;

  function updateLayerArr() {
    layerLookupArr = [];
    layerLookupMaskedArr = [];
    layerLookupUnmaskedArr = [];
    Object.entries(layerLookup).forEach((kV) => {
      if (kV[1].feature === null) {
        layerLookupUnmaskedArr.push(kV[1]);
      } else {
        layerLookupMaskedArr.push(kV[1]);
      }
      layerLookupArr.push(kV[1]);
    });
    layerLookupMaskedArr.sort((a, b) => a.layerDef.sort_order - b.layerDef.sort_order);
    layerLookupUnmaskedArr.sort((a, b) => a.layerDef.sort_order - b.layerDef.sort_order);
  }

  function addIncomingMasks() {
    if (LAYERSET.multimask_geojson) {
      const feats = new GeoJSON().readFeatures(LAYERSET.multimask_geojson, {
        featureProjection: 'EPSG:3857',
      });
      feats.forEach(function (f) {
        trimShapeSource.addFeature(f);
      });
    }
  }

  function createLayerLookup() {
    layerLookup = {};
    trimShapeSource.clear();
    LAYERSET.layers.forEach(function (layerDef) {
      let newLayer = new TileLayer({
        source: new XYZ({
          url: makeTitilerXYZUrl({
            host: CONTEXT.titiler_host,
            url: layerDef.urls.cog,
          }),
        }),
        extent: transformExtent(layerDef.extent, 'EPSG:4326', 'EPSG:3857'),
      });

      // make extent
      const extentGeom4326 = fromExtent(transformExtent(layerDef.extent, 'EPSG:4326', 'EPSG:3857'));
      const extentGeom3857 = extentGeom4326.clone();
      const extentFeature = new Feature({
        geometry: extentGeom3857,
        show: false,
        name: layerDef.slug,
      });
      extentLayer.getSource().addFeature(extentFeature);

      layerLookup[layerDef.slug] = {};
      const layer = {
        olLayer: newLayer,
        layerDef: layerDef,
        crop: null,
        feature: null,
        georeferenceUrl: layerDef.urls.georeference,
      };
      layerLookup[layerDef.slug] = layer;
    });
    // now iterate the incoming mask features and apply all existing
    addIncomingMasks();
    updateLayerArr();
    unchanged = true;
  }

  function extentLayerStyle(feature, resolution) {
    const prop = feature.getProperties();
    if (prop.show) {
      return styles.redDashOutline;
    }
    return;
  }

  var extentLayer = new VectorLayer({
    source: new VectorSource(),
    style: extentLayerStyle,
    zIndex: 1000,
  });

  const trimShapeLayer = new VectorLayer({
    source: new VectorSource(),
    style: [styles.mmDraw, styles.vertexPoint],
    zIndex: 1001,
  });
  const trimShapeSource = trimShapeLayer.getSource();
  trimShapeSource.on('addfeature', function (e) {
    layerApplyMask(e.feature);
  });

  function resetInterface() {
    layerLookupArr.forEach(function (layer) {
      layerRemoveMask(layer, true);
    });
    addIncomingMasks();
    unchanged = true;
  }

  let viewer;
  onMount(() => {
    createLayerLookup();
    viewer = new MapViewer('map-viewer');
    viewer.setDefaultExtent(fullExtent);

    // add layers
    viewer.addBasemaps(CONTEXT.mapbox_api_token);
    viewer.addLayers(layerLookupArr.map((item) => item.olLayer));
    viewer.addLayer(trimShapeLayer);
    viewer.addLayer(extentLayer);

    // add control
    viewer.addControl(new LyrMousePosition(null, 'ol-mouse-position'));

    // create interactions
    const draw = new Draw({
      source: trimShapeSource,
      type: 'Polygon',
      style: styles.mmDraw,
    });
    viewer.addInteraction('draw', draw);

    const modify = new Modify({
      source: trimShapeSource,
      style: styles.mmModify,
    });
    modify.on('modifystart', function (e) {
      viewer.element.style.cursor = 'grabbing';
    });
    modify.on('modifyend', function (e) {
      unchanged = false;
    });
    viewer.addInteraction('modify', modify);

    const snap = new Snap({
      source: trimShapeSource,
      edge: false,
    });
    viewer.addInteraction('snap', snap);

    // add pointer style
    viewer.map.on('pointermove', function (e) {
      if (e.dragging) {
        return;
      }
      trimShapeLayer.getFeatures(e.pixel).then(function (features) {
        features.length > 0 ? (viewer.element.style.cursor = 'pointer') : (viewer.element.style.cursor = 'default');
      });
    });

    viewer.resetExtent();
  });

  $: {
    if (viewer) {
      viewer.interactions.draw.setActive(currentLayer != null);
      viewer.interactions.modify.setActive(!viewer.interactions.draw.getActive());
    }
  }

  function handleMultimaskSubmitResponse(response) {
    if (response.success) {
      window.alert('Masks saved successfully.');
      unchanged = true;
      resetMosaic();
    } else {
      let errMsg = 'Error! MultiMask not saved. You must remove and remake the following masks:\n';
      errMsg += response.message;
      alert(errMsg);
    }
  }
  function submitMultiMask() {
    if (DISABLED) {
      window.alert('You do not have edit permissions for this multimask.');
      return;
    }
    const outGeoJSON = { type: 'FeatureCollection', features: [] };
    layerLookupArr.forEach(function (layer) {
      if (layer.feature) {
        layer.feature.setProperties({ layer: layer.layerDef.slug });
        const wgs84feat = layer.feature.clone();
        wgs84feat.getGeometry().transform('EPSG:3857', 'EPSG:4326');
        const featureGeoJSON = new GeoJSON().writeFeatureObject(wgs84feat, {
          rightHanded: true,
          decimals: 7,
        });
        outGeoJSON.features.push(featureGeoJSON);
      }
    });

    submitPostRequest(
      '/layerset/',
      CONTEXT.ohmg_post_headers,
      'set-mask',
      {
        'multimask-geojson': outGeoJSON,
        'map-id': LAYERSET.map_id,
        category: LAYERSET.id,
      },
      handleMultimaskSubmitResponse,
    );
  }

  function zoomToLayer(layer) {
    if (viewer) {
      const extent3857 = transformExtent(layer.layerDef.extent, 'EPSG:4326', 'EPSG:3857');
      viewer.setExtent(extent3857);
      layerToTop(layer);
    }
    showExtent(layer);
  }

  function showExtent(layer) {
    extentLayer
      .getSource()
      .getFeatures()
      .forEach(function (feature) {
        const props = feature.getProperties();
        if (props.name == layer.layerDef.slug) {
          feature.setProperties({ show: true });
        } else {
          feature.setProperties({ show: false });
        }
      });
  }

  function layerToTop(layer) {
    layerLookupArr.forEach(function (otherLayer) {
      const z = otherLayer.olLayer.getZIndex();
      // push down layers that have previously been shoved to the top
      if (z > 300) {
        otherLayer.olLayer.setZIndex(otherLayer.olLayer.getZIndex() - 1);
      }
    });
    layer.olLayer.setZIndex(500);
  }

  function addMask(layer) {
    if (viewer) {
      zoomToLayer(layer);
      // setting the currentLayer activates the draw interaction
      // and when the feature is complete it is used for the crop
      currentLayer = layer.layerDef.slug;
    }
    showExtent(layer);
  }

  function layerApplyMask(feature) {
    if (!currentLayer) {
      currentLayer = feature.getProperties().layer;
    }
    if (currentLayer && layerLookup[currentLayer]) {
      if (layerLookup[currentLayer].feature) {
        trimShapeSource.removeFeature(layerLookup[currentLayer].feature);
        layerLookup[currentLayer].feature = null;
      }
      if (layerLookup[currentLayer].crop) {
        layerLookup[currentLayer].crop = null;
      }
      const crop = new Crop({
        feature: feature,
        wrapX: true,
        inner: false,
      });
      layerLookup[currentLayer].olLayer.addFilter(crop);
      layerLookup[currentLayer].crop = crop;
      layerLookup[currentLayer].feature = feature;
    }
    currentLayer = null;
    updateLayerArr();
    unchanged = false;
  }

  function layerRemoveMask(layer, confirm) {
    if (confirm != true) {
      confirm = window.confirm('Remove this mask?');
    }
    if (confirm) {
      if (layer.crop) {
        layer.crop.set('active', false);
      }
      trimShapeSource.removeFeature(layer.feature);
      layer.crop = null;
      layer.feature = null;
      updateLayerArr();
      unchanged = false;
    }
  }
</script>

<div id="mm-container" class="svelte-component-main">
  <div id="map-container" class="map-container" style="height: calc(100%-35px);">
    <div id="map-viewer" class="map-item rounded-bottom"></div>
    <div id="layer-panel" style="display: flex;">
      <div class="layer-section-header" style="border-top:none;">
        <ToolUIButton
          action={() => {
            if (viewer) {
              viewer.resetExtent();
            }
          }}
          title="Go to full extent"
        >
          <CornersOut />
        </ToolUIButton>
        <ExpandElement elementId={'mm-container'} />
      </div>
      <div id="layer-list" style="flex:2;">
        <div class="layer-section-header">
          <span>Unmasked</span>
        </div>
        <div class="layer-section-subheader" style="overflow-y:auto">
          {#each layerLookupUnmaskedArr as layer}
            <div style="display:flex;">
              <ToolUIButton title="add mask for this layer" action={() => addMask(layer)}>
                <CropIcon />
              </ToolUIButton>
              {#if CONTEXT.user.is_authenticated}
                <ToolUIButton
                  title="edit georeferencing for this layer"
                  action={() => {
                    window.location.href = layer.georeferenceUrl;
                  }}
                >
                  <MapPin />
                </ToolUIButton>
              {/if}
              &nbsp;
              <button
                class="layer-entry"
                title="Zoom to layer"
                on:click={() => zoomToLayer(layer)}
                on:mouseover={() => showExtent(layer)}
                on:focus={null}
              >
                <span style={currentLayer == layer.layerDef.slug ? 'color:red' : ''}>{layer.layerDef.nickname}</span>
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
              <ToolUIButton action={() => layerRemoveMask(layer)} title="remove this mask">
                <Trash />
              </ToolUIButton>
              {#if CONTEXT.user.is_authenticated}
                <ToolUIButton
                  title="Edit georeferencing for this layer"
                  action={() => {
                    window.location.href = layer.georeferenceUrl;
                  }}
                >
                  <MapPin />
                </ToolUIButton>
              {/if}
              &nbsp;
              <button
                class="layer-entry"
                title="Zoom to layer"
                on:click={() => zoomToLayer(layer)}
                on:mouseover={() => showExtent(layer)}
                on:focus={null}
              >
                <span style={currentLayer == layer.layerDef.slug ? 'color:red' : ''}>{layer.layerDef.nickname}</span>
              </button>
            </div>
          {:else}
            <div>No layers</div>
          {/each}
        </div>
      </div>
      <div class="layer-section-header">
        <ToolUIButton action={resetInterface} title="Cancel (reset)" disabled={unchanged || DISABLED}>
          <X />
        </ToolUIButton>
        <ToolUIButton action={submitMultiMask} title="Submit" disabled={unchanged || DISABLED}>
          <Check />
        </ToolUIButton>
      </div>
    </div>
  </div>
</div>

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
