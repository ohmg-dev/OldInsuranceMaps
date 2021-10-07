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

  import Projection from 'ol/proj/Projection';

  import MousePosition from 'ol/control/MousePosition';
  import {createStringXY} from 'ol/coordinate';

  import Style from 'ol/style/Style';
  import Stroke from 'ol/style/Stroke';
  import Fill from 'ol/style/Fill';
  import RegularShape from 'ol/style/RegularShape';

  import Draw from 'ol/interaction/Draw';
  import Modify from 'ol/interaction/Modify';
  import Snap from 'ol/interaction/Snap';

  export let IMG_HEIGHT;
  export let IMG_WIDTH;
  export let DOC_URL;
  export let CSRFTOKEN;
  export let USERNAME;
  export let SUBMIT_URL;
  export let MAP_CENTER;
  export let INCOMING_GCPS;
  export let INCOMING_TRANSFORMATION;
  export let MAPSERVER_ENDPOINT;
	export let MAPSERVER_LAYERNAME;
  export let MAPBOX_API_KEY;

  if (!MAP_CENTER) { MAP_CENTER = [0,0] };

  let previewMode = "n/a";

  let activeGCP = 1;
  let inProgress = false;

  let panelFocus = "equal";
  let syncPanelWidth = false;

  let docView;
  let mapView;
  let gcpList = [];
  
  const beginTxt = "Click a recognizable location on the map document (left panel)"
  const completeTxt = "Now find and click on the corresponding location in the web map (right panel)"

  let currentTxt = beginTxt;

  const noteInputElId = "note-input";

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

  let currentTransformation = "poly1";
  const transformations = [
    {id: 'poly1', name: 'Polynomial'},
    {id: 'tps', name: 'Thin Plate Spline'},
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

  const osmLayer = new TileLayer({
    source: new OSM(),
  })

  // const imageryLayer = new TileLayer({
  //   preload: 12,
  //   source: new TileArcGISRest({
  //     layer: "163",
  //     url: "https://atlas1.ga.lsu.edu/arcgis/rest/services/imagery/la_gohsep2010_mosaic_LSU_2016/MapServer",
  //   })
  // });
  // const imageryLabels = new TileLayer({
  //   source: new XYZ({
  //     url: 'https://api.mapbox.com/styles/v1/legiongis/ckr9kiwkk3naq17qlarzn5q9s/tiles/256/{z}/{x}/{y}?access_token='+MAPBOX_API_KEY,
  //   })
  // });
  // const imageryGroup = new LayerGroup({
  //   layers: [
  //     imageryLayer,
  //     imageryLabels,
  //   ]
  // })

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

  const docGCPSource = new VectorSource();
  docGCPSource.on('addfeature', function (e) {
		activeGCP = gcpList.length + 1;
    if (!e.feature.getProperties().listId) {
			e.feature.setProperties({'listId': activeGCP})
		}
		e.feature.setStyle(gcpHighlight);
    inProgress = true;
  })

  const mapGCPSource = new VectorSource();
  mapGCPSource.on(['addfeature'], function (e) {

    // if this is an incoming gcp, the listID (and all other properties)
    // will already be set. Otherwise, it must be set here.
		if (!e.feature.getProperties().listId) {
	    e.feature.setProperties({
        'id': uuid(),
        'listId': activeGCP,
	      'username': USERNAME,
	      'note': '',
	    });
    }
    e.feature.setStyle(gcpHighlight);
    syncGCPList();
    inProgress = false;
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
				activeGCP = e.features.item(0).getProperties().listId;
				syncGCPList();
			}
    });

    let overlaySource = modify.getOverlay().getSource();
    overlaySource.on(['addfeature', 'removefeature'], function (e) {
      targetElement.style.cursor = e.type === 'addfeature' ? 'pointer' : '';
    });
    return modify
  }

	// this Draw interaction is created individually for each map panel
  function makeDrawInteraction(source) {
    return new Draw({
      source: source,
      type: 'Point',
      style: new Style(),
    });
  }

  function DocumentViewer (elementId) {

    const targetElement = document.getElementById(elementId);

    // items needed by layers and map
    // set the extent and projection with 0, 0 at the top left of the image
    const docExtent = [0, -IMG_HEIGHT, IMG_WIDTH, 0];
    const docProjection = new Projection({
      units: 'pixels',
      extent: docExtent,
    });

    // create layers
    const docLayer = new ImageLayer({
      source: new ImageStatic({
        url: DOC_URL,
        projection: docProjection,
        imageExtent: docExtent,
      }),
      // zIndex: 999,
    })

    const gcpLayer = new VectorLayer({
      source: docGCPSource,
      style: gcpDefault,
    });

    // create map
    const map = new Map({
      target: targetElement,
      layers: [docLayer, gcpLayer],
      view: new View({
        projection: docProjection,
        center: [IMG_WIDTH/2, -IMG_HEIGHT/2],
        zoom: 1,
        maxZoom: 8,
      })
    });

    // create interactions
    const draw = makeDrawInteraction(docGCPSource);
    draw.setActive(true);
    targetElement.style.cursor = 'crosshair';
    map.addInteraction(draw)

    const modify = makeModifyInteraction(gcpLayer, docGCPSource, targetElement)
    modify.setActive(true);
    map.addInteraction(modify)

    // create controls
    const mousePositionControl = new MousePosition({
      coordinateFormat: function(coordinate) {
        const x = Math.round(coordinate[0]);
        const y = -Math.round(coordinate[1]);
        let formatted = `${x}, ${y}`;
        // set empty if the mouse is outside of the image itself
        if (x < 0 || x > IMG_WIDTH || y < 0 || y > IMG_HEIGHT) {formatted = ""}
        return formatted
      },
      projection: docProjection,
      undefinedHTML: '&nbsp;',
    });
    map.addControl(mousePositionControl);

    // add some click actions to the map
    map.on("click", setActiveGCPOnClick);

    // add transition actions to the map element
    function updateMapEl() {map.updateSize()}
    targetElement.style.transition = "width .5s";
    targetElement.addEventListener("transitionend", updateMapEl)

    // expose properties as necessary
    this.map = map;
    this.element = targetElement;
    this.drawInteraction = draw;

  }

  function MapViewer (elementId) {

      const targetElement = document.getElementById(elementId);

      const gcpLayer = new VectorLayer({
        source: mapGCPSource,
        style: gcpDefault,
      });

      // create map
      const map = new Map({
        target: targetElement,
				layers: [basemaps[0].layer, gcpLayer],
        view: new View({
          center: MAP_CENTER,
          zoom: 16,
          // not yet sure how to change the projection
          // projection: getProjection('EPSG:42304'),
        })
      });

      // create interactions
      const draw = makeDrawInteraction(mapGCPSource);
      draw.setActive(false);
      map.addInteraction(draw)

      const modify = makeModifyInteraction(gcpLayer, mapGCPSource, targetElement)
      modify.setActive(true)
      map.addInteraction(modify)

      // create controls
      let mousePositionControl = new MousePosition({
        projection: 'EPSG:4326',
        coordinateFormat: createStringXY(6),
        undefinedHTML: '&nbsp;',
      });
      map.addControl(mousePositionControl);

      // add some click actions to the map
      map.on("click", setActiveGCPOnClick)

      // add transition actions to the map element
      function updateMapEl() {map.updateSize()}
      targetElement.style.transition = "width .5s";
      targetElement.addEventListener("transitionend", updateMapEl)

      // expose properties as necessary
      this.map = map;
      this.element = targetElement;
      this.drawInteraction = draw;
  }

  onMount(() => {
    docView = new DocumentViewer('doc-viewer');
    mapView = new MapViewer('map-viewer');
		loadIncomingGCPs();
  });

  function loadIncomingGCPs() {
		docGCPSource.refresh();
		mapGCPSource.refresh();
		if (INCOMING_GCPS) {
			let listId = 1;
			let inGCPs = new GeoJSON().readFeatures(INCOMING_GCPS, {
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
    currentTransformation = (INCOMING_TRANSFORMATION ? INCOMING_TRANSFORMATION : "poly1")
		syncGCPList();
		activeGCP = gcpList.length + 1;
		inProgress = false;
	}

  function setActiveGCPOnClick(e) {
    e.map.forEachFeatureAtPixel(e.pixel, function(feature) {
      activeGCP = feature.getProperties().listId;
    });
  }

  function removeActiveGCP() {
    if (activeGCP) { removeGCP(activeGCP) }
  }

  function confirmGCPRemoval(gcpId) {
    return window.confirm(`Remove GCP #${gcpId}?`);
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
      activeGCP = (gcpList.length == 0 ? 1 : activeGCP - 1);
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
    previewGCPs();
  }

  function updateNote() {
    const el = document.getElementById(noteInputElId);
    mapGCPSource.getFeatures().forEach( function (feature) {
      if (feature.getProperties().listId == activeGCP) {
        feature.setProperties({"note": el.value});
      }
    })
  }

  // Triggered by the inProgress boolean
  function updateInterface(gcpInProgress) {

    if (syncPanelWidth) {
      panelFocus = ( gcpInProgress ? "right" : "left" )
      setPanelWidths(panelFocus)
    }
    if (docView && mapView) {
      docView.drawInteraction.setActive(!gcpInProgress);
      mapView.drawInteraction.setActive(gcpInProgress);
      docView.element.style.cursor = ( gcpInProgress ? 'default' : 'crosshair' );
      mapView.element.style.cursor = ( gcpInProgress ? 'crosshair' : 'default' );
      currentTxt = ( gcpInProgress ? completeTxt : beginTxt );
    }
  }
  $: updateInterface(inProgress)

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
      // first set the opacity of the layer
      const newOpacity = ( mode == "full" ? 1 : .6 );
      previewLayer.setOpacity(newOpacity);
      // now add the layer if necessary
      if (mapView.map.getLayers().getArray().length == 2){
        mapView.map.getLayers().insertAt(1, previewLayer)
      }
    } else if (mode == "none" || mode == "n/a") {
      // remove the layer
      mapView.map.removeLayer(previewLayer);
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
    if (inProgress) {
      el.value = "";
    } else {
      mapGCPSource.getFeatures().forEach( function (feat) {
        let props = feat.getProperties();
        if (props.listId == activeId) { el.value = props.note }
      })
    }

    // highlight features for active GCP
    docGCPSource.getFeatures().forEach( function (feat) {
      feat.setStyle(gcpDefault);
      if (feat.getProperties().listId == activeId) { feat.setStyle(gcpHighlight) }
    })
    mapGCPSource.getFeatures().forEach( function (feat) {
      feat.setStyle(gcpDefault)
      if (feat.getProperties().listId == activeId) { feat.setStyle(gcpHighlight) }
    })
  }
  $: displayActiveGCP(activeGCP)

  // Triggered by a (manual) change in which panel should have focus
  function setPanelWidths (focusOn) {
    if (docView && mapView) {
      switch(focusOn) {
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
  $: setPanelWidths(panelFocus);

  function toggleFullscreen () {
    if (document.fullscreenElement == null) {
      let promise = document.getElementById('interface').requestFullscreen();
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
      featureCollection.features.push(
        {
          "type": "Feature",
          "properties": feature.getProperties(),
          "geometry": {
            "type": "Point",
            "coordinates": wgs84_geom.flatCoordinates
          }
        }
      )
    });
    return featureCollection
  }

  // wrappers for the backend view to process GCPs
  function previewGCPs() { processGCPs("preview") }
  function submitGCPs() { processGCPs("submit") }
  function cleanupPreview() { processGCPs("cleanup") }

  function processGCPs(operation){
    if (gcpList.length < 3) {
      previewMode = "n/a";
      return
    };

    const data = JSON.stringify({
      "gcp_geojson": asGeoJSON(),
      "transformation": currentTransformation,
      "operation": operation,
    });
    fetch(SUBMIT_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json;charset=utf-8',
          'X-CSRFToken': CSRFTOKEN,
        },
        body: data,
      })
      .then(response => response.json())
      .then(result => {
        if (previewMode == "n/a") { previewMode = "transparent"};
        if (operation == "preview") {
          let sourceUrl = previewSource.getUrls()[0];
          previewSource.setUrl(sourceUrl.replace(/\/[^\/]*$/, '/'+Math.random()));
          previewSource.refresh()
        } else if (operation == "submit") {
          processGCPs("cleanup");
        } else if (operation == "cleanup") {
          window.location.href = result['redirect_to'];
        }
      });

  }

  // A couple of functions that are attached to the window itself

  // wrapper function to call view for db cleanup as needed
  function cleanupOnLeave (e) {
    // e.preventDefault();
    // alert("hello!")
    console.log("pausing")
    // e.returnValue = '';
    cleanupPreview()
  }

  function handleKeydown(e) {
    // only allow these shortcuts if the maps have focus
    // so they aren't activated while typing a note.
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
  }

</script>

<svelte:window on:keydown={handleKeydown} on:beforeunload={cleanupOnLeave}/>

<div id="interface" class="main">
  <div class="tb tb-top">
    <div id="interaction-options" class="tb-top-item">
      <button title="enter fullscreen mode" on:click={toggleFullscreen}><i id="fs-icon" class="fa fa-arrows-alt" /></button>
      Panels:
      <select class="basemap-select" title="set panel size" bind:value={panelFocus} disabled={syncPanelWidth}>
        <option value="equal">equal</option>
        <option value="left">more left</option>
        <option value="right">more right</option>
      </select>
      <!-- <label><input type=radio bind:group={panelFocus} disabled={syncPanelWidth} value="equal">equal</label>
      <label><input type=radio bind:group={panelFocus} disabled={syncPanelWidth} value="left">left</label>
      <label><input type=radio bind:group={panelFocus} disabled={syncPanelWidth} value="right">right</label> -->
      <label><input type=checkbox bind:checked={syncPanelWidth}>auto</label>

    </div>
    <div class="tb-top-item"><em>{currentTxt}</em></div>
    <div class="tb-top-item">
      {startloads}/{endloads} | {inProgress} | {activeGCP} | 
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
  </div>
  <div class="map-container">
    <div id="doc-viewer" class="map-item"></div>
    <div id="map-viewer" class="map-item"></div>
    <div class={previewLoading ? 'lds-ellipsis': ''}><div></div><div></div><div></div><div></div></div>
  </div>
  <div class="tb tb-bottom">
    {#if gcpList.length == 0}
    <div class="tb-bottom-item">
      <em>no control points added yet</em>
    </div>
    {:else}
    <div id="summary-panel" class="tb-bottom-item">
      <select class="gcp-select" bind:value={activeGCP}>
        {#each gcpList as gcp}
          <option value={gcp.listId}>
            {gcp.listId} | ({gcp.pixelX}, {gcp.pixelY}) ({gcp.coordX}, {gcp.coordY}) | {gcp.username}
          </option>
        {/each}
      </select>
      <label>
        Note:
        <input type="text" id="{noteInputElId}" style="width:400px" disabled={gcpList.length == 0} on:change={updateNote}>
      </label>
    <button title="remove" on:click={removeActiveGCP}><i id="fs-icon" class="fa fa-trash" style="color:red"/></button>
    <button title="clear all GCPs" on:click={loadIncomingGCPs}><i id="fs-icon" class="fa fa-refresh" /></button>
    </div>
    {/if}
    <div class="tb-bottom-item">
      <!-- svelte-ignore a11y-no-onchange -->
      <select class="trans-select" title="select transformation type" bind:value={currentTransformation} on:change={previewGCPs}>
        {#each transformations as trans}
          <!-- disable thin plate spline for now, but it does work properly -->
          <!-- <option value={trans.id} disabled={trans.id == "tps"}>{trans.name}</option> -->
          <option value={trans.id}>{trans.name}</option>
        {/each}
      </select>
      <button on:click={submitGCPs} disabled={gcpList.length < 3}>Done</button>
    </div>
  </div>
</div>

<style>

  .gcp-select {
    width: 400px;
  }

  .main {
    height: 700px;
    padding: 0;
  }

  .tb {
    display: flex;
    flex-direction: row;
    align-items: center;
    background: white;
    height: 2em;
  }

  .tb button {
    padding: 0;
    height: 2em;
  }

  .tb button:disabled {
    color: grey;
  }

  .tb-top {
    justify-content: space-between;
  }

  .tb-top-item {}

  .tb-bottom {
    justify-content: space-between;
  }

  .tb-bottom-item {}

  .map-container {
    display: flex;
    height: calc(100% - 4em);
    justify-content: space-between;
  }

  .map-item {
    width: 50%;
    height: 100%;
  }

  #doc-viewer {
    background: url('../static/img/sandpaper-bg-vlite.jpg');
  }

  @media (max-width: 640px) {
		/* .map-container {
	    display: flex;
	    height: calc(100% - 4em);
	    justify-content: space-between;
			flex-direction: column;
	  }
		.map-item {
	    width: 100%;
	    height: 50%;
	  } */
  }

  /* pure css loading bar */
	/* from https://loading.io/css/ */
	.lds-ellipsis {
		display: inline-block;
		position: absolute;
    right: 25px;
		width: 80px;
		height: 80px;
	}
	.lds-ellipsis div {
		position: absolute;
		top: 33px;
		width: 13px;
		height: 13px;
		border-radius: 50%;
		background: #000;
		animation-timing-function: cubic-bezier(0, 1, 1, 0);
	}
	.lds-ellipsis div:nth-child(1) {
		left: 8px;
		animation: lds-ellipsis1 0.6s infinite;
	}
	.lds-ellipsis div:nth-child(2) {
		left: 8px;
		animation: lds-ellipsis2 0.6s infinite;
	}
	.lds-ellipsis div:nth-child(3) {
		left: 32px;
		animation: lds-ellipsis2 0.6s infinite;
	}
	.lds-ellipsis div:nth-child(4) {
		left: 56px;
		animation: lds-ellipsis3 0.6s infinite;
	}
	@keyframes lds-ellipsis1 {
		0% {
			transform: scale(0);
		}
		100% {
			transform: scale(1);
		}
	}
	@keyframes lds-ellipsis3 {
		0% {
			transform: scale(1);
		}
		100% {
			transform: scale(0);
		}
		}
		@keyframes lds-ellipsis2 {
		0% {
			transform: translate(0, 0);
		}
		100% {
			transform: translate(24px, 0);
		}
	}

</style>
