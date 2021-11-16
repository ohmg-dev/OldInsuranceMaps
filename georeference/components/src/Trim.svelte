<script>
  import {onMount} from 'svelte';
  
  import 'ol/ol.css';
  import Map from 'ol/Map';
  import View from 'ol/View';

  import VectorSource from 'ol/source/Vector';
  import OSM from 'ol/source/OSM';
  import XYZ from 'ol/source/XYZ';
  import TileWMS from 'ol/source/TileWMS';

  import {transformExtent} from 'ol/proj';

  import GeoJSON from 'ol/format/GeoJSON';

  import Feature from 'ol/Feature';

  import Polygon from 'ol/geom/Polygon';

  import TileLayer from 'ol/layer/Tile';
  import VectorLayer from 'ol/layer/Vector';

  import MousePosition from 'ol/control/MousePosition';
  import {createStringXY} from 'ol/coordinate';

  import Style from 'ol/style/Style';
  import Stroke from 'ol/style/Stroke';
  import Fill from 'ol/style/Fill';
  import RegularShape from 'ol/style/RegularShape';
  
  import Draw from 'ol/interaction/Draw';
  import Modify from 'ol/interaction/Modify';
  import Snap from 'ol/interaction/Snap';

  export let CSRFTOKEN;
  export let LAYER;
  export let MAPBOX_API_KEY;
  // export let LAYER_ID;
  export let GEOSERVER_WMS;
  export let LAYER_EXTENT;
  export let INCOMING_MASK_COORDINATES;

  let previewMode = "n/a";
  let maskPolygonCoords = [];
  let maskSLDContent;

  $: unchanged = JSON.stringify(maskPolygonCoords) == JSON.stringify(INCOMING_MASK_COORDINATES);
  $: submitBtnLabel = INCOMING_MASK_COORDINATES.length == 0 ? "Save Mask" : "Update Mask";
  $: maskToRemove = INCOMING_MASK_COORDINATES.length > 0 || maskPolygonCoords.length > 0;

  let mapView;

  let currentTxt = "still under construction!";

  const gcpDefault = new Style({
    image: new RegularShape({
    radius1: 10,
    radius2: 1,
    points: 4,
    rotation: .79,
    fill: new Fill({color: 'black'}),
    stroke: new Stroke({
      color: 'black', width: 2
    })
    })
  });
  const gcpHighlight = new Style({
    image: new RegularShape({
    radius1: 10,
    radius2: 1,
    points: 4,
    rotation: .79,
    fill: new Fill({color: 'rgb(0, 255, 0)'}),
    stroke: new Stroke({
      color: 'rgb(0, 255, 0)', width: 2
    })
    })
  });
  const gcpHover = new Style({
    image: new RegularShape({
    radius1: 10,
    radius2: 1,
    points: 4,
    rotation: .79,
    fill: new Fill({color: 'red'}),
    stroke: new Stroke({
      color: 'red', width: 2
    })
    })
  });

  const outlineStyle = new Style({
      stroke: new Stroke({ color: '#fae200', width: 2, })
    })

  function defaultSLD() {
    let sld = '<?xml version="1.0" encoding="UTF-8"?>'
    sld += '<StyledLayerDescriptor version="1.0.0"'
    sld += ' xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"'
    sld += ' xmlns="http://www.opengis.net/sld"'
    sld += ' xmlns:ogc="http://www.opengis.net/ogc"'
    sld += ' xmlns:xlink="http://www.w3.org/1999/xlink"'
    sld += ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
    sld += '<NamedLayer>'
    sld += ` <Name>${LAYER.geoserver_id}</Name>`
    sld += ' <UserStyle IsDefault="true">'
    sld += '  <FeatureTypeStyle>'
    sld += '   <Rule>'
    sld += '    <RasterSymbolizer>'
    sld += '      <Opacity>1</Opacity>'
    sld += '    </RasterSymbolizer>'
    sld += '   </Rule>'
    sld += '  </FeatureTypeStyle>'
    sld += ' </UserStyle>'
    sld += '</NamedLayer>'
    sld += '</StyledLayerDescriptor>'
    return sld
  }

  const trimmedLayer = new TileLayer({
    source: new TileWMS({
      url: GEOSERVER_WMS,
      params: {
        'LAYERS': LAYER.geoserver_id,
        'TILED': true,
        'SLD_BODY': defaultSLD(),
        // Strangely, STYLES needs to have some random value in it, so that
        // the "Library Mode" will find the corresponding style in the SLD_BODY,
        // instead of the default for this layer that is stored in Geoserver.
        'STYLES': 'placeholder',
      },
    })
  });

  const osmLayer = new TileLayer({
    source: new OSM(),
  })
  
  const imageryLayer = new TileLayer({
    opacity: .75,
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
  
  const trimShapeSource = new VectorSource();
  const trimShapeLayer = new VectorLayer({
      source: trimShapeSource,
      style: outlineStyle,
    });
  trimShapeSource.on("addfeature", function(e) {
    updateMaskPolygon(e.feature.getGeometry().getCoordinates()[0]);
    mapView.drawInteraction.setActive(false)
  })

  function removeMask() {
    maskPolygonCoords = [];
    trimShapeSource.clear();
    maskSLDContent = defaultSLD();
    const extent3857 = transformExtent(LAYER.extent, "EPSG:4326", "EPSG:3857");
    mapView.map.getView().fit(extent3857);
    mapView.drawInteraction.setActive(true)
  }

  function resetInterface() {
    removeMask();
    if (INCOMING_MASK_COORDINATES.length > 0) {
      const feat = new Feature({
        geometry: new Polygon([INCOMING_MASK_COORDINATES])
      });
      trimShapeSource.addFeature(feat);
    }
    // maskPolygonCoords = INCOMING_MASK_COORDINATES;
    mapView.drawInteraction.setActive(true)
  }

  function updateMaskPolygon(coordinates) {
    if (coordinates) {
      maskPolygonCoords = [];
      coordinates.forEach( function(coord) {
        const lng = Math.round(coord[0]*10)/10;
        const lat = Math.round(coord[1]*10)/10;
        maskPolygonCoords.push([lng, lat])
      })
      updateSLDContent();
    }
  }

  // triggered whenever the maskSLDContent is changed
  function refreshPreview(sldBody) {
    if (sldBody) {
      trimmedLayer.getSource().updateParams({
        "SLD_BODY": sldBody,
      });
    }
  }
  $: refreshPreview(maskSLDContent);

    // this Modify interaction is created individually for each map panel
  function makeModifyInteraction(hitDetection, source, targetElement) {
    const modify = new Modify({
    hitDetection: hitDetection,
    source: source,
    style: gcpHover,
    });
  
    modify.on(['modifystart', 'modifyend'], function (e) {
    targetElement.style.cursor = e.type === 'modifystart' ? 'grabbing' : 'pointer';
    if (e.type == "modifyend") {
      updateMaskPolygon(e.features.item(0).getGeometry().getCoordinates()[0]);
      updateSLDContent()
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
      layers: [
        basemaps[0].layer,
      //   origLayer,
        trimmedLayer,
        trimShapeLayer,
      ],
      view: new View({
      zoom: 16,
      })
    });
  
    // create interactions
    const draw = new Draw({
      source: trimShapeSource,
      type: 'Polygon',
      style: new Style({
        stroke: new Stroke({ color: '#fae200', width: 2, })
      }),
    });
    draw.setActive(true);
    map.addInteraction(draw)
  
    const modify = makeModifyInteraction(trimShapeLayer, trimShapeSource, targetElement)
    modify.setActive(true)
    map.addInteraction(modify)
  
    // create controls
    let mousePositionControl = new MousePosition({
      projection: 'EPSG:4326',
      coordinateFormat: createStringXY(6),
      undefinedHTML: '&nbsp;',
    });
    map.addControl(mousePositionControl);
  
    // expose properties as necessary
    this.map = map;
    this.element = targetElement;
    this.drawInteraction = draw;
  }

  onMount(() => {
    mapView = new MapViewer("map-viewer");
    resetInterface();
  });

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

  function updateSLDContent() { processMask("preview") }
  function submitMask() { processMask("submit") }

  function processMask(operation) {
  
    const data = JSON.stringify({
      "mask_coords": maskPolygonCoords,
      "operation": operation,
    });
    fetch(LAYER.urls.trim, {
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
        // this will trigger a refresh of the preview layer
        if (result['sld_content'] == null) {
          maskSLDContent = defaultSLD();
        } else {
          maskSLDContent = result['sld_content'];
        }
      }
      if (operation == "submit") {
        window.location.href = result['redirect_to'];
      }
    });
  }
  </script>
  
  <div class="svelte-component-main">
    <nav>
      <div id="interaction-options" class="tb-top-item">
      </div>
      <div class="tb-top-item"><em>{currentTxt}</em></div>
      <div class="tb-top-item">
      Preview:
      <select class="basemap-select" title="set preview mode" bind:value={previewMode} disabled={previewMode == "n/a"}>
        <option value="n/a" disabled>n/a</option>
        <option value="none">hide</option>
        <option value="transparent">transparent</option>
        <option value="full">opaque</option>
      </select>
      Basemap:
      <select class="basemap-select" title="select basemap" bind:value={currentBasemap}>
        {#each basemaps as basemap}
        <option value={basemap.id}>{basemap.label}</option>
        {/each}
      </select>
      </div>
      <div>
        <button title="remove mask" on:click={removeMask} disabled={!maskToRemove}><i class="fa fa-trash" /></button>
        <button title="reset" on:click={resetInterface} disabled={unchanged}><i class="fa fa-refresh" /></button>
        <button on:click={submitMask}>{submitBtnLabel}</button>
      </div>
    </nav>
    <div class="map-container">
      <div id="map-viewer" class="map-item rounded-bottom"></div>
    </div>
  </div>
  
<style>
</style>
