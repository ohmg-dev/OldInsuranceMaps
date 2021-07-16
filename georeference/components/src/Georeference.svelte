<script>

  import {onMount} from 'svelte';

  import 'ol/ol.css';
  import Map from 'ol/Map';
  import View from 'ol/View';
  import Feature from 'ol/Feature';
  import Collection from 'ol/Collection';

  import Point from 'ol/geom/Point';

  import IIIF from 'ol/source/IIIF';
  import ImageStatic from 'ol/source/ImageStatic';
  import VectorSource from 'ol/source/Vector';
  import OSM from 'ol/source/OSM';
  import TileWMS from 'ol/source/TileWMS';
  import GeoJSON from 'ol/format/GeoJSON';

  import IIIFInfo from 'ol/format/IIIFInfo';

  import TileLayer from 'ol/layer/Tile';

  import ImageLayer from 'ol/layer/Image';
  import VectorLayer from 'ol/layer/Vector';

  import Projection from 'ol/proj/Projection';
  import {get as getProjection} from 'ol/proj';

  import Zoom from 'ol/control/Zoom';
  import MousePosition from 'ol/control/MousePosition';
  import {createStringXY} from 'ol/coordinate';

  import Style from 'ol/style/Style';
  import Circle from 'ol/style/Circle';
  import Stroke from 'ol/style/Stroke';
  import Fill from 'ol/style/Fill';
  import Text from 'ol/style/Text';
  import RegularShape from 'ol/style/RegularShape';

  import Draw from 'ol/interaction/Draw';
  import Select from 'ol/interaction/Select';
  import Modify from 'ol/interaction/Modify';
  import Snap from 'ol/interaction/Snap';

  export let IMG_HEIGHT;
  export let IMG_WIDTH;
  export let DOC_URL;
	export let DOC_ID;
  export let CSRFTOKEN;
  export let USERNAME;
  export let SUBMIT_URL;
  export let MAP_CENTER;
  export let INCOMING_GCPS;
  export let MAPSERVER_ENDPOINT;
	export let MAPSERVER_LAYERNAME;

  if (!MAP_CENTER) { MAP_CENTER = [0,0] };

  let previewOpacity = .6;

  let activeGCP = 1;
  let inProgress = false;

  let docView;
  let mapView;
  let gcpList = [];

  let noteInputEl;

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
      fill: new Fill({color: 'red'}),
      stroke: new Stroke({
        color: 'red', width: 2
      })
    })
  });

  let currentInteraction = 'add';
  const mapInteractions = [
    {id: 'add', name: 'Add', faClass: 'plus'},
    {id: 'edit', name: 'Edit', faClass: 'edit'},
    // {id: 'remove', name: 'Remove', faClass: 'minus'},
  ];
  let currentTransformation = "poly";
  const transformations = [
    {id: 'poly', name: 'Polynomial'},
    {id: 'tps', name: 'Thin Plate Spline'},
    // {id: 'remove', name: 'Remove', faClass: 'minus'},
  ];

  const docGCPSource = new VectorSource();
  const mapGCPSource = new VectorSource();

  docGCPSource.on('addfeature', function (event) {
		activeGCP = gcpList.length + 1;
    if (!event.feature.getProperties().listId) {
			event.feature.setProperties({'listId': activeGCP})
		}
		event.feature.setStyle(gcpHighlight);
    inProgress = true;
  })

  mapGCPSource.on(['addfeature'], function (event) {

    // if this is an incoming gcp, the listID (and all other properties)
    // will already be set. Otherwise, it must be set here.
		if (!event.feature.getProperties().listId) {
	    event.feature.setProperties({
        'id': null,
        'listId': activeGCP,
	      'username': USERNAME,
	      'note': '',
	    });
    }
    event.feature.setStyle(gcpHighlight);
    syncGCPList();
    inProgress = false;
  })

  const previewSource = new TileWMS({
    url: MAPSERVER_ENDPOINT,
    params: {
        // set this as env variable in apache conf file
        // 'MAP': '/opt/mapserver/data/config/geonode.map',
        'LAYERS': MAPSERVER_LAYERNAME,
        'TILED': true,
    },
    serverType: 'mapserver',
  });

	// this modify interaction is created individually for each map panel
  function makeModifyInteraction(hitDetection, source, targetElement) {
    const modify = new Modify({
      hitDetection: hitDetection,
      source: source,
			style: new Style({
		    image: new Circle({
					radius: 3,
		      fill: new Fill({
						color: 'white'
					}),
		    })
		  }),
    });

    modify.on(['modifystart', 'modifyend'], function (evt) {
      targetElement.style.cursor = evt.type === 'modifystart' ? 'grabbing' : 'grab';
			if (evt.type == "modifyend") {
				activeGCP = evt.features.item(0).getProperties().listId;
				syncGCPList();
			}
    });

    let overlaySource = modify.getOverlay().getSource();
    overlaySource.on(['addfeature', 'removefeature'], function (evt) {
      targetElement.style.cursor = evt.type === 'addfeature' ? 'grab' : '';
    });

    return modify
  }

	// this draw interaction is created individually for each map panel
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
    map.addInteraction(draw)

    const modify = makeModifyInteraction(gcpLayer, docGCPSource, targetElement)
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

    // expose properties as necessary
    this.map = map;
    this.element = targetElement;
    this.drawInteraction = draw;
    this.modifyInteraction = modify;

  }

  function MapViewer (elementId) {

      const targetElement = document.getElementById(elementId);

      // create layers
      const osmLayer = new TileLayer({
        source: new OSM(),
      })

      const previewLayer = new TileLayer({
        source: previewSource,
				opacity: .5,
      });

      const gcpLayer = new VectorLayer({
        source: mapGCPSource,
        style: gcpDefault,
      });

      // create map
      const map = new Map({
        target: targetElement,
				layers: [osmLayer, previewLayer, gcpLayer],
        view: new View({
          center: MAP_CENTER,
          zoom: 16,
          // not yet sure how to change the projection
          // projection: getProjection('EPSG:42304'),
        })
      });

      // create interactions
      const draw = makeDrawInteraction(mapGCPSource);
      map.addInteraction(draw)

      const modify = makeModifyInteraction(gcpLayer, mapGCPSource, targetElement)
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
			this.previewLayer = previewLayer;
      this.element = targetElement;
      this.drawInteraction = draw;
      this.modifyInteraction = modify;
  }

  onMount(() => {
    docView = new DocumentViewer('doc-viewer');
    mapView = new MapViewer('map-viewer');
    noteInputEl = document.getElementById("note-input");

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
			})
		}
		syncGCPList();
		activeGCP = gcpList.length + 1;
		inProgress = false;
	}

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

  function gcpGeoJSON() {

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
  };

  function previewGCPs() { processGCPs(true) }
  function submitGCPs() { processGCPs(false) }

  function processGCPs(previewOnly){
    if (gcpList.length < 3) {return};
    const data = JSON.stringify({
      "gcp_geojson": gcpGeoJSON(),
      "docid": DOC_ID,
      "transformation": currentTransformation,
      "preview_only": previewOnly,
      // "gs_layer_name": GEOSERVER_LAYER_NAME,
    });
    console.log(SUBMIT_URL)
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
        console.log(result)
        let sourceUrl = previewSource.getUrls()[0];
        previewSource.setUrl(sourceUrl.replace(/\/[^\/]*$/, '/'+Math.random()));
        previewSource.refresh()
      });
  }

  function updateNote() {
    mapGCPSource.getFeatures().forEach( function (feature) {
      if (feature.getProperties().listId == activeGCP) {
        feature.setProperties({"note": noteInputEl.value});
      }
    })
  }

  $: if (docView && mapView) {
    if (currentInteraction == 'add') {
      docView.drawInteraction.setActive(!inProgress);
      mapView.drawInteraction.setActive(inProgress);
      docView.element.style.cursor = ( inProgress ? 'default' : 'crosshair' );
      mapView.element.style.cursor = ( inProgress ? 'crosshair' : 'default' );
    } else {
      docView.drawInteraction.setActive(false);
      mapView.drawInteraction.setActive(false);
    }

    docView.modifyInteraction.setActive(currentInteraction == "edit");
    mapView.modifyInteraction.setActive(currentInteraction == "edit");

		// not yet implemented
    // docView.deleteInteraction.setActive(currentInteraction == "remove");
    // mapView.deleteInteraction.setActive(currentInteraction == "remove");
  }

  $: if (mapView) {
    if (inProgress) {
      noteInputEl.value = "";
    } else {
      mapGCPSource.getFeatures().forEach( function (feat) {
        let props = feat.getProperties();
        if (props.listId == activeGCP) { noteInputEl.value = props.note }
      })
    }
  }

	$: if (mapView) {
		mapView.previewLayer.setOpacity(previewOpacity);
	}

  $: {
    docGCPSource.getFeatures().forEach( function (feat) {
      feat.setStyle(gcpDefault);
      if (feat.getProperties().listId == activeGCP) { feat.setStyle(gcpHighlight) }
    })
    mapGCPSource.getFeatures().forEach( function (feat) {
      feat.setStyle(gcpDefault)
      if (feat.getProperties().listId == activeGCP) { feat.setStyle(gcpHighlight) }
    })
  }

  let key;
  function handleKeydown(event) {
    // only allow these shortcuts if the maps have focus
    if (document.activeElement != noteInputEl) {
      switch(event.key) {
        case "Escape":
          if (document.fullscreen) {  document.exitFullscreen(); }
          // if (iface) { iface.drawInteraction.abortDrawing()}
          break;
        case "a": case "A":
          currentInteraction = 'add';
          break;
        case "e": case "E":
          currentInteraction = 'edit';
          break;
        case "r": case "R":
          currentInteraction = 'remove';
          break;
        case "w": case "W":
					previewOpacity = (previewOpacity < 1 ? previewOpacity + .6 : 0);
          break;
      }
    }
  }

  function toggleFullscreen () {
    if (!document.fullscreen) {
      let promise = document.getElementById('interface').requestFullscreen();
      document.getElementById("fs-icon").classList.remove("fa-arrows-alt");
      document.getElementById("fs-icon").classList.add("fa-times");
    } else {
      document.exitFullscreen();
      document.getElementById("fs-icon").classList.remove("fa-times");
      document.getElementById("fs-icon").classList.add("fa-arrows-alt");
    }
  }

  function cleanupOnLeave (e) {
    // e.preventDefault();
    // alert("hello!")
    console.log("pausing")
    // e.returnValue = '';
  }

</script>

<svelte:window on:keydown={handleKeydown} on:beforeunload={cleanupOnLeave}/>

<div id="interface" class="main">
  <div class="tb tb-top">
    <div id="interaction-options" class="tb-top-item">
    <button title="enter fullscreen mode" on:click={toggleFullscreen}><i id="fs-icon" class="fa fa-arrows-alt" /></button>
    <button title="reset interface" on:click={loadIncomingGCPs}><i id="fs-icon" class="fa fa-refresh" /></button>
    {#each mapInteractions as option}
        <label>
          <input type=radio bind:group={currentInteraction} value={option.id}>
            {option.name}<i class="fa fa-{option.faClass}" />
        </label>
    {/each}
    </div>
    <div id="summary-panel" class="toolbar-item">
      {#if gcpList.length == 0}
      <em>no control points added yet</em>
      {:else}
      <select class="gcp-select" bind:value={activeGCP}>
        {#each gcpList as gcp}
          <option value={gcp.listId}>
            {gcp.listId} | ({gcp.pixelX}, {gcp.pixelY}) ({gcp.coordX}, {gcp.coordY}) | {gcp.username}
          </option>
        {/each}
      </select>
      {/if}
    </div>
    <div class="tb-top-item">
      <!-- svelte-ignore a11y-no-onchange -->
      <select class="trans-select" title="select transformation type" bind:value={currentTransformation} on:change={previewGCPs}>
        {#each transformations as trans}
          <!-- disable thin plate spline for now, but it does work properly -->
          <!-- <option value={trans.id} disabled={trans.id == "tps"}>{trans.name}</option> -->
          <option value={trans.id}>{trans.name}</option>
        {/each}
      </select>
       <button on:click={submitGCPs}>Submit</button>
    </div>
  </div>
  <div class="map-container">
    <div id="doc-viewer" class="map-item"></div>
    <div id="map-viewer" class="map-item"></div>
  </div>
  <div class="tb tb-bottom">
    <div class="tb-bottom-item">
      <label>
        Note [{activeGCP}]
        <input type="text" id="note-input" style="width:400px" on:change={updateNote}>
      </label>
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

  .tb-top {
    justify-content: space-between;
  }

  .tb-top-item {}

  .tb-bottom {
    justify-content: center;
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

</style>
