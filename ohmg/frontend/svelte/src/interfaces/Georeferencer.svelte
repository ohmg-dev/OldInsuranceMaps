<script>

  import X from "phosphor-svelte/lib/X";
  import Check from "phosphor-svelte/lib/Check";
  import ArrowsClockwise from "phosphor-svelte/lib/ArrowsClockwise";
  import Trash from "phosphor-svelte/lib/Trash";
  import Stack from "phosphor-svelte/lib/Stack";
  import GearSix from "phosphor-svelte/lib/GearSix";

  import {onMount} from 'svelte';

  import 'ol/ol.css';
  import View from 'ol/View';
  import Feature from 'ol/Feature';

  import Point from 'ol/geom/Point';

  import VectorSource from 'ol/source/Vector';
  import XYZ from 'ol/source/XYZ';

  import GeoJSON from 'ol/format/GeoJSON';

  import TileLayer from 'ol/layer/Tile';
  import VectorLayer from 'ol/layer/Vector';

  import {transformExtent} from 'ol/proj';
  import { containsXY } from 'ol/extent';
  import { inflateCoordinatesArray } from "ol/geom/flat/inflate"

  import Draw from 'ol/interaction/Draw';
  import Modify from 'ol/interaction/Modify';
  import Snap from 'ol/interaction/Snap';

  import Styles from '@lib/ol-styles';
  import {
    makeLayerGroupFromLayerSet,
    makeTitilerXYZUrl,
    makeRotateCenterLayer,
    showRotateCenter,
    removeRotateCenter,
    uuid,
    extentFromImageSize,
    projectionFromImageExtent,
    usaExtent,
  } from '@lib/utils';
  import { submitPostRequest } from '@lib/requests';
  import { makeImageLayer, makePmTilesLayer } from '@lib/layers';
  import { DocMousePosition, LyrMousePosition, MapScaleLine } from '@lib/controls';

  import Modal, {getModal} from '@/base/Modal.svelte';
  import LoadingEllipsis from '@/base/LoadingEllipsis.svelte';
  import Link from '@/base/Link.svelte';
  import ToolUIButton from '../base/ToolUIButton.svelte';

  import ExpandElement from "./buttons/ExpandElement.svelte";
  import ExtendSessionModal from "./modals/ExtendSessionModal.svelte";

  import { MapViewer } from "@lib/viewers";

  import {parcelLookup} from "@lib/parcelLookup";

  export let CONTEXT;
  export let REGION;
  export let MAP;
  export let MAIN_LAYERSET;
  export let KEYMAP_LAYERSET;

  const styles = new Styles();

  let previewMode = "n/a";
  let previewUrl = '';

  let inProgress = false;
  let loadingInitial = false;

  let panelFocus = "equal";
  let syncPanelWidth = false;

  let docViewer;
  let mapViewer;

  let gcpList = [];

  let activeGCP = null;
  $: nextGCP = gcpList.length + 1;

  let unchanged = true;

  let showLayerPanel = true;
  let showNotePanel = false;
  let showSettingsPanel = false;

  let docRotate;
  let mapRotate;

  let showLoading;

  let currentBasemap;
  let currentZoom;

  let enableSnapLayer = false;

  let currentPreviewId;

  let defaultExtent;
  if (REGION.gcps_geojson) {
    defaultExtent = new VectorSource({
      features: new GeoJSON().readFeatures(REGION.gcps_geojson, {
        dataProjection: "EPSG:4326",
        featureProjection: "EPSG:3857",
      })
    }).getExtent();
  } else if (MAP.extent) {
    defaultExtent = transformExtent(MAP.extent, "EPSG:4326", "EPSG:3857");
  } else {
    defaultExtent = usaExtent;
  }

  const sessionId = REGION.lock ? REGION.lock.session_id : null;

  let disableInterface = REGION.lock && (REGION.lock.user.username != CONTEXT.user.username);
  let disableReason;
  let leaveOkay = true;
  let enableButtons = false;
  if (REGION.lock && (REGION.lock.user.username == CONTEXT.user.username)) {
    leaveOkay = false;
    enableButtons = true;
  }
  $: enableSave = gcpList.length >= 3 && enableButtons;

  // show the extend session prompt 10 seconds before the session expires
  setTimeout(promptRefresh, (CONTEXT.session_length*1000) - 10000)

  let autoRedirect;
  function promptRefresh() {
    if (!leaveOkay) {
      getModal('modal-extend-session').open()
      leaveOkay = true;
      autoRedirect = setTimeout(cancelSession, 10000);
    }
  }

  const noteInputElId = "note-input";

  let currentTransformation = "poly1";
  const transformations = [
    {id: 'poly1', name: 'Polynomial'},
    {id: 'tps', name: 'Thin Plate Spline'},
  ];

  let currentTargetProjection = "EPSG:3857"
  const availableProjections = [
    {id: 'EPSG:3857', name: 'Pseudo Mercator'},
    {id: 'ESRI:102009', name: 'Lambert North America'},
  ];

  // CREATE GCP LAYERS
  const docGCPSource = new VectorSource();
  docGCPSource.on('addfeature', function (e) {
    if (!e.feature.getProperties().listId) {
      e.feature.setProperties({'listId': nextGCP})
    }
    activeGCP = e.feature.getProperties().listId;
    inProgress = true;
    unchanged = false;
  })
  const docGCPLayer = new VectorLayer({
    source: docGCPSource,
    style: styles.gcpDefault,
  });

  const mapGCPSource = new VectorSource();
  mapGCPSource.on(['addfeature'], function (e) {
    // if this is an incoming gcp, the listID (and all other properties)
    // will already be set. Otherwise, it must be set here.
    if (!e.feature.getProperties().listId) {
      e.feature.setProperties({
        'id': uuid(),
        'listId': nextGCP,
        'username': CONTEXT.user.username,
        'note': '',
      });
    }
    e.feature.setStyle(styles.gcpHighlight);
    // check the loadingInitial flag to save unnecessary calls to backend
    if (!loadingInitial) {syncGCPList()}
    inProgress = false;
    activeGCP = e.feature.getProperties().listId;
  })
  const mapGCPLayer = new VectorLayer({
    source: mapGCPSource,
    style: styles.gcpDefault,
    zIndex: 30,
  });

  // CREATE DISPLAY LAYERS

  // items needed by layers and map
  const docExtent = extentFromImageSize(REGION.image_size)
  const docProjection = projectionFromImageExtent(docExtent)
  const documentLayer = makeImageLayer(REGION.urls.image, docProjection, docExtent)

  let previewLayer = new TileLayer({
    source: new XYZ(),
    zIndex: 20,
  });

  // REFERENCE LAYER STUFF
  let kmLayerGroup;
  let kmLayerGroup50;
  if (KEYMAP_LAYERSET) {
    kmLayerGroup = makeLayerGroupFromLayerSet({
      layerSet: KEYMAP_LAYERSET,
      zIndex: 10,
      titilerHost: CONTEXT.titiler_host,
      applyMultiMask: true,
    })
    kmLayerGroup50 = makeLayerGroupFromLayerSet({
      layerSet: KEYMAP_LAYERSET,
      zIndex: 11,
      titilerHost: CONTEXT.titiler_host,
      applyMultiMask: true,
    })
    kmLayerGroup50.setOpacity(.5)
  }

  const mainLayerGroup = makeLayerGroupFromLayerSet({
    layerSet: MAIN_LAYERSET,
    zIndex: 12,
    titilerHost: CONTEXT.titiler_host,
    applyMultiMask: true,
    excludeLayerId: REGION.layer ? REGION.layer.slug : '',
  })
  const mainLayerGroup50 = makeLayerGroupFromLayerSet({
    layerSet: MAIN_LAYERSET,
    zIndex: 13,
    titilerHost: CONTEXT.titiler_host,
    applyMultiMask: true,
    excludeLayerId: REGION.layer ? REGION.layer.slug : '',
  })
  mainLayerGroup50.setOpacity(.5)

  const refLayers = [
    {
      id: "none",
      label: "None",
      layer: false,
      disabled: null,
    },
    {
      id: "keyMap50",
      label: "Key Map 1/2",
      layer: kmLayerGroup50,
      disabled: kmLayerGroup50 ? false : true,
    },
    {
      id: "keyMap",
      label: "Key Map",
      layer: kmLayerGroup,
      disabled: kmLayerGroup ? false : true,
    },
    {
      id: "mainLayers50",
      label: "Main Layers 1/2",
      layer: mainLayerGroup50,
      disabled: mainLayerGroup50.getLayers().getArray().length == 0 ? true : null,
    },
    {
      id: "mainLayers",
      label: "Main Layers",
      layer: mainLayerGroup,
      disabled: mainLayerGroup.getLayers().getArray().length == 0 ? true : null,
    }
  ]

  let currentRefLayer = 'none';
  if (kmLayerGroup) { currentRefLayer = "keyMap50"}

  $: {
    refLayers.forEach( function(layerDef) {
      if (layerDef.layer) {
        if (currentRefLayer === layerDef.id) {
          layerDef.layer.setVisible(true)
        } else {
          layerDef.layer.setVisible(false)
        }
      }
    })
  }

  // SNAP LAYER STUFF
  const parcelEntry = parcelLookup[MAP.locale.slug]
  const pmLayer = parcelEntry ? makePmTilesLayer(
    parcelEntry.pmtilesUrl,
    `<a target="_blank" href="${parcelEntry.attributionUrl}">${parcelEntry.attributionText}</a>`,
    styles.redOutline
  ) : null
  const snapSource = new VectorSource({
    overlaps: false,
  })
  const snapLayer = new VectorLayer({
    source: snapSource,
    style: styles.empty,
  })

  // MAKING INTERACTIONS

  // this Modify interaction is created individually for each map panel
  function makeModifyInteraction(source, targetElement) {
    const modify = new Modify({
      source: source,
      style: styles.gcpHover,
    });

    modify.on(['modifystart', 'modifyend'], function (e) {
      targetElement.style.cursor = e.type === 'modifystart' ? 'grabbing' : 'pointer';
      if (e.type == "modifyend") {
        activeGCP = e.features.item(0).getProperties().listId;
        unchanged = false;
        syncGCPList();
      }
    });

    let overlaySource = modify.getOverlay().getSource();
    overlaySource.on(['addfeature', 'removefeature'], function (e) {
      const fallback = targetElement.id == 'doc-viewer' ? docCursorStyle : mapCursorStyle;
      targetElement.style.cursor = e.type === 'addfeature' ? 'pointer' : fallback;
    });
    return modify
  }

  // this Draw interaction is created individually for each map panel
  function makeDrawInteraction(source, condition, style) {
    const draw = new Draw({
      source: source,
      type: 'Point',
      style: style,
      condition: condition,
    });
    return draw
  }

  function selectGCPOnClick (e) {
    let found = false;
    e.map.forEachFeatureAtPixel(e.pixel, function(feature) {
      if (feature.getProperties().listId) {
        activeGCP = feature.getProperties().listId;
        found = true;
      }
    });
    if (!found && !inProgress) {activeGCP = null}
  }

  onMount(() => {

    // CREATE THE LEFT-SIDE DOCUMENT INTERFACE
    docViewer = new MapViewer('doc-viewer')
    docViewer.setDefaultExtent(docExtent)
    docViewer.setView(new View({
      projection: docProjection,
      zoom: 1,
      maxZoom: 8,
    }))
    docViewer.addLayer(documentLayer)
    docViewer.addLayer(docGCPLayer)

    // add control
    docViewer.addControl(new DocMousePosition(docExtent, null, 'ol-mouse-position'));

    // create interactions
    function drawWithinDocCondition (mapBrowserEvent) {
      return containsXY(docExtent, mapBrowserEvent.coordinate[0], mapBrowserEvent.coordinate[1])
    }

    docViewer.addInteraction('draw', makeDrawInteraction(docGCPSource, drawWithinDocCondition, styles.empty))
    docViewer.addInteraction('modify', makeModifyInteraction(docGCPSource, docViewer.element))

    docRotate = makeRotateCenterLayer();
    docViewer.addLayer(docRotate.layer);

    // add some click actions to the map
    docViewer.map.on("click", selectGCPOnClick);


    // CREATE THE RIGHT-SIDE MAP INTERFACE
    mapViewer = new MapViewer('map-viewer')
    mapViewer.setDefaultExtent(defaultExtent)

    mapViewer.addBasemaps(CONTEXT.mapbox_api_token)
    currentBasemap = mapViewer.currentBasemap.id;
    mapViewer.addLayer(previewLayer)
    mapViewer.addLayer(mapGCPLayer)

    // create controls
    mapViewer.addControl(new LyrMousePosition(null, 'ol-mouse-position'))
    mapViewer.addControl(new MapScaleLine())

    // create interactions
    const mapDrawGCPStyle = pmLayer ? styles.smallCross : styles.empty
    mapViewer.addInteraction('draw', makeDrawInteraction(mapGCPSource, null, mapDrawGCPStyle))
    mapViewer.addInteraction('modify', makeModifyInteraction(mapGCPSource, mapViewer.element))

    // add some event listening to the map
    mapViewer.map.on("click", selectGCPOnClick);
    mapViewer.map.on("rendercomplete", () => {showLoading = false})

    mapRotate = makeRotateCenterLayer()
    mapViewer.addLayer(mapRotate.layer)

    kmLayerGroup &&  mapViewer.addLayer(kmLayerGroup)
    kmLayerGroup50 &&  mapViewer.addLayer(kmLayerGroup50)
    mapViewer.addLayer(mainLayerGroup)
    mapViewer.addLayer(mainLayerGroup50)

    // snap to parcels --- work-in-progress!
    const snap = new Snap({
      source: snapSource,
      edge: false,
    });
    mapViewer.addInteraction('parcelSnap', snap)
    mapViewer.interactions.parcelSnap.setActive(false)
    // tried map.on('rendercomplete') here but sometimes it would fire constantly,
    // so using these more specific event listeners
    mapViewer.map.getView().on('change:resolution', refreshSnapSource)
    mapViewer.map.on('moveend', refreshSnapSource)

    currentZoom = mapViewer.getZoom()
    mapViewer.map.getView().on('change:resolution', () => {
      currentZoom = mapViewer.getZoom()
    })

    // OTHER STUFF
    setPreviewVisibility(previewMode)
    loadIncomingGCPs();
    if (!CONTEXT.user.is_authenticated) { getModal('modal-anonymous').open() }
  });

  function loadIncomingGCPs() {
    loadingInitial = true;
    docGCPSource.clear();
    mapGCPSource.clear();
    if (REGION.gcps_geojson) {
      const incomingFeats = new GeoJSON().readFeatures(REGION.gcps_geojson, {
        dataProjection: "EPSG:4326",
        featureProjection: "EPSG:3857",
      })
      let listId = 1;

      incomingFeats.forEach( function(inGCP) {

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
    currentTransformation = (REGION.transformation ? REGION.transformation : "poly1")
    syncGCPList();
    docViewer.resetExtent()
    mapViewer.resetExtent()
    loadingInitial = false;
    inProgress = false;
    unchanged = true;
    activeGCP = null;
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
      activeGCP = null;
      inProgress = false;
    }
  }

  function resetListIds() {
    // iterates the features in map and doc and resets all list ids.
    // necessary if any GCP has been deleted that is not the last in the list.
    let newListId = 1;
    const newIdLookup = {}
    // first create a lookup to translate old ids to new ids
    mapGCPSource.forEachFeature( function (mapFeat) {
      newIdLookup[mapFeat.getProperties().listId] = newListId;
      newListId += 1;
    })
    // now update all listIds on both layers using the lookup
    mapGCPSource.forEachFeature( function (mapFeat) {
      mapFeat.setProperties({'listId': newIdLookup[mapFeat.getProperties().listId]});
    })
    docGCPSource.forEachFeature( function (docFeat) {
      docFeat.setProperties({'listId': newIdLookup[docFeat.getProperties().listId]});
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
    getPreview();
  }

  function updateNote() {
    const el = document.getElementById(noteInputElId);
    mapGCPSource.getFeatures().forEach( function (feature) {
      if (feature.getProperties().listId == activeGCP) {
        feature.setProperties({"note": el.value});
      }
    })
  }

  $: {
    if (syncPanelWidth) {
      panelFocus = inProgress ? "right" : "left";
    } else {
      panelFocus = "equal";
    }
  }

  $: {
    if (docViewer && mapViewer) {
      docViewer.interactions.draw.setActive(!inProgress);
      mapViewer.interactions.draw.setActive(inProgress);
    }
  }

  $: {
    if (mapViewer) {mapViewer.setBasemap(currentBasemap)}
  }

  $: docCursorStyle = inProgress ? 'default' : 'crosshair';
  $: mapCursorStyle = inProgress ? 'crosshair' : 'default';

  $: {
    if (docViewer && mapViewer) {
      docViewer.element.style.cursor = docCursorStyle;
      mapViewer.element.style.cursor = mapCursorStyle;
    }
  }

  $: {
    if (currentZoom < 17) {enableSnapLayer = false}
  }

  function refreshSnapSource() {
    if (!enableSnapLayer) {return}
    snapSource.clear()
    const features = pmLayer.getFeaturesInExtent(mapViewer.map.getView().calculateExtent());
    features.forEach(function (feature) {
      const lineCoords = inflateCoordinatesArray(
        feature.getFlatCoordinates(), // flat coordinates
        0, // offset
        feature.getEnds(), // geometry end indices
        2, // stride
      )
      const geoJsonGeom = {coordinates: lineCoords, type: "Polygon"};
      const f = new GeoJSON().readFeature(geoJsonGeom, {
        dataProjection: "EPSG:3857",
      })
      if (!snapSource.hasFeature(f)) {snapSource.addFeature(f)}
    })
  }
  function toggleSnap(enabled) {
    if (!mapViewer || !pmLayer) {return}
    if (enabled) {
      mapViewer.addLayer(snapLayer)
      mapViewer.addLayer(pmLayer)
      mapViewer.interactions.parcelSnap.setActive(true)
      mapViewer.map.once('rendercomplete', refreshSnapSource)
    } else {
      snapSource.clear()
      mapViewer.map.removeLayer(snapLayer)
      mapViewer.map.removeLayer(pmLayer)
      mapViewer.interactions.parcelSnap.setActive(false)
    }
  }
  $: toggleSnap(enableSnapLayer)

  function setPreviewVisibility(mode) {
    if (!mapViewer) { return }
    if (mode == "full" || mode == "transparent") {
      previewLayer.setVisible(true)
      previewLayer.setOpacity(mode == "full" ? 1 : .6);
    } else if (mode == "none" || mode == "n/a") {
      previewLayer.setVisible(false)
    }
  }
  $: setPreviewVisibility(previewMode);

  // Triggered by change of activeGCP
  function displayActiveGCP(activeId) {

    // set note display content
    const el = document.getElementById(noteInputElId);
    if (el) {
      if (inProgress) {
        el.value = "";
      } else {
        mapGCPSource.getFeatures().forEach( function (feat) {
          let props = feat.getProperties();
          if (props.listId == activeId) { el.value = props.note }
        })
      }
    }

    // highlight features for active GCP
    docGCPSource.getFeatures().forEach( function (feat) {
      feat.setStyle(styles.gcpDefault);
      if (feat.getProperties().listId == activeId) { feat.setStyle(styles.gcpHighlight) }
    })
    mapGCPSource.getFeatures().forEach( function (feat) {
      feat.setStyle(styles.gcpDefault)
      if (feat.getProperties().listId == activeId) { feat.setStyle(styles.gcpHighlight) }
    })
  }
  $: displayActiveGCP(activeGCP)

  $: {
    if (docViewer && mapViewer) {
      switch(panelFocus) {
        case "equal":
          docViewer.element.style.width = "50%";
          mapViewer.element.style.width = "50%";
          break;
        case "left":
          docViewer.element.style.width = "75%";
          mapViewer.element.style.width = "25%";
          break;
        case "right":
          docViewer.element.style.width = "25%";
          mapViewer.element.style.width = "75%";
          break
      }
    }
  }

  function updatePreviewSource (previewUrl) {
    if (previewUrl) {
      showLoading = true;
      mapViewer.map.removeLayer(previewLayer)
      previewLayer = new TileLayer({
          source: new XYZ({
          url: makeTitilerXYZUrl({
            host: CONTEXT.titiler_host,
            url: previewUrl,
          }),
        }),
        zIndex: 20,
      })
      setPreviewVisibility(previewMode)
      mapViewer.addLayer(previewLayer)
    }
  }
  $: updatePreviewSource(previewUrl)

  // convert the map features to GeoJSON for sending to georeferencing operation
  $: asGeoJSON = () => {
    let featureCollection = { "type": "FeatureCollection", "features": [] };
    mapGCPSource.forEachFeature( function(feature) {
      const wgs84_geom = feature.getGeometry().clone().transform('EPSG:3857', 'EPSG:4326')
      let props = feature.getProperties();
      delete props['geometry'];
      featureCollection.features.push(
        {
          "type": "Feature",
          "properties": props,
          "geometry": {
            "type": "Point",
            "coordinates": wgs84_geom.flatCoordinates
          }
        }
      )
    });
    return featureCollection
  }

  function getPreview() {
    if (gcpList.length < 3) {
      previewMode = "n/a";
      return
    };
    submitPostRequest(
      `/georeference/${REGION.id}/`,
      CONTEXT.ohmg_post_headers,
      "preview",
      {
        "gcp_geojson": asGeoJSON(),
        "transformation": currentTransformation,
        "projection": currentTargetProjection,
        "sesh_id": sessionId,
        "last_preview_id": currentPreviewId,
      },
      (result) => {
        previewMode = previewMode == "n/a" ? "transparent" : previewMode;
        // updating this variable will trigger the preview layer to be
        // updated with the new source url
        previewUrl = result.payload.preview_url;
        currentPreviewId = result.payload.preview_id;
      },
    )
  }

  function submitSession() {
    if (gcpList.length < 3) {
      previewMode = "n/a";
      return
    };
    leaveOkay = true;
    disableInterface = true;
    disableReason = "submit";
    submitPostRequest(
      `/georeference/${REGION.id}/`,
      CONTEXT.ohmg_post_headers,
      "submit",
      {
        "gcp_geojson": asGeoJSON(),
        "transformation": currentTransformation,
        "projection": currentTargetProjection,
        "sesh_id": sessionId,
        "last_preview_id": currentPreviewId,
      },
      () => {window.location.href = `/map/${REGION.map}`},
    )
  }

  function cancelSession() {
    leaveOkay = true;
    disableInterface = true;
    disableReason = "cancel"
    submitPostRequest(
      `/georeference/${REGION.id}/`,
      CONTEXT.ohmg_post_headers,
      "cancel",
      {
        "sesh_id": sessionId,
        "last_preview_id": currentPreviewId,
      },
      () => {window.location.href = `/map/${REGION.map}`;},
    )
  }

  let keyPressed = {};
  function handleKeydown(e) {
    // only allow these shortcuts if the maps have focus,
    // so shortcuts aren't activated while typing a note.
    if (document.activeElement.id == "") {
      switch(e.key) {
        case "d": case "D":
          removeActiveGCP();
          break;
        case "w": case "W": case "p": case "P":
          // cyle through the three preview level options
          if (previewMode == "none") {
            previewMode = "transparent"
          } else if (previewMode == "transparent") {
            previewMode = "full"
          } else if (previewMode == "full") {
            previewMode = "none"
          }
          break;
        case "b": case "B":
          currentBasemap = currentBasemap === "osm" ? "satellite" : "osm";
          break;
        case "r": case "R":
          let currentIndex;
          refLayers.forEach( function (layerDef, n) {
            if (layerDef.id == currentRefLayer) {
              currentIndex = n
            }
          })
          if (currentIndex == refLayers.length - 1) {
            currentRefLayer = refLayers[0].id
          } else {
            currentRefLayer = refLayers[currentIndex+1].id
          }
          break;
      }
    }
    // // toggle the center icon to help with rotation
    // if (e.shiftKey || e.key == "Shift") {keyPressed['shift'] = true}
    // if (e.altKey || e.key == "Alt") {keyPressed['alt'] = true}
    // if (keyPressed.shift && keyPressed.alt) {
    //   if (mapView && docView) {
    //     showRotateCenter(docView.map, docRotate.layer, docRotate.feature)
    //     showRotateCenter(mapView.map, mapRotate.layer, mapRotate.feature)
    //   }
    // }
  }

  function handleKeyup(e) {
    // remove the center point if rotation is to be disabled
    // if (e.shiftKey || e.key == "Shift") {keyPressed['shift'] = false}
    // if (e.altKey || e.key == "Alt") {keyPressed['alt'] = false}
    // if (!keyPressed.shift && !keyPressed.alt) {
    // 	if (mapView && docView) {
    //     removeRotateCenter(docRotate.layer)
    //     removeRotateCenter(mapRotate.layer)
    //   }
    // }
  };

  function confirmLeave () {
    event.preventDefault();
    event.returnValue = "";
    return "...";
  }

  function handleExtendSession(response) {
    leaveOkay = false;
    clearTimeout(autoRedirect)
    setTimeout(promptRefresh, (CONTEXT.session_length*1000) - 10000)
  }

</script>

<ExtendSessionModal {CONTEXT} {sessionId} callback={handleExtendSession} />

<svelte:window on:keydown={handleKeydown} on:keyup={handleKeyup} on:beforeunload={() => {if (!leaveOkay) {confirmLeave()}}} on:unload={cancelSession}/>
<div style="height:25px;">
  Create 3 or more ground control points to georeference this document. <Link href="https://about.oldinsurancemaps.net/guides/georeferencing/" external={true}>Learn more</Link>
</div>

<Modal id="modal-anonymous">
  <p>Feel free to experiment with the interface, but to submit your work you must 
    <Link href="/account/login">sign in</Link> or
    <Link href="/account/signup">sign up</Link>.
  </p>
</Modal>
<Modal id="modal-cancel">
	<p>Are you sure you want to cancel this session?</p>
  <button class="button is-success" on:click={() => {
    cancelSession();
    getModal('modal-cancel').close()
    }}>Yes - return to overview</button>
  <button class="button is-danger" on:click={() => {
    getModal('modal-cancel').close()}
    }>No - keep working</button>
</Modal>

<div id="map-container" style="height:calc(100vh - 205px)" class="svelte-component-main">
  {#if disableInterface}
  <div class="interface-mask">
    <div class="signin-reminder">
      {#if disableReason == "unauthenticated"}
      <p><em>
        <Link href="/account/login">Sign in</Link> or
        <Link href="/account/signup">sign up</Link> to proceed.
      </em></p>
      {:else if disableReason == "input" || disableReason == "processing"}
      <!-- svelte-ignore a11y-invalid-attribute -->
      <p>Someone is already georeferencing this document (<Link href="javascript:window.location.reload(true)">refresh</Link>).</p>
      {:else if disableReason == "submit"}
      <p>Saving control points and georeferencing document... redirecting to document detail page.</p>
      <LoadingEllipsis />
      {:else if disableReason == "cancel"}
      <p>Cancelling georeferencing.</p>
      <LoadingEllipsis />
      {/if}
    </div>
  </div>
  {/if}
  <nav>
    <div>
      <select title="Set panel size" bind:value={panelFocus} disabled={syncPanelWidth}>
        <option value="equal">equal panels</option>
        <option value="left">more left</option>
        <option value="right">more right</option>
      </select>
      <label><input type=checkbox bind:checked={syncPanelWidth}> autosize</label>
    </div>
    <div class="control-btn-group">
        <ToolUIButton action={submitSession} title="Save control points" disabled={!enableSave}><Check /></ToolUIButton>
        <ToolUIButton action={() => { getModal('modal-cancel').open() }} title="Cancel georeferencing" disabled={!enableButtons}><X /></ToolUIButton>
        <ToolUIButton action={loadIncomingGCPs} title="Reset/reload original GCPs" disabled={unchanged}><ArrowsClockwise /></ToolUIButton>
        <ExpandElement elementId={'map-container'} />
    </div>
  </nav>
  <div class="map-container">
    <div id="doc-viewer" class="map-item"></div>
    <div id="map-viewer" class="map-item"></div>
    {#if showLoading && (previewMode == "transparent" || previewMode == "full")}
    <div style="top:65px; right:25px; width:80px; height:80px; position:absolute;">
      <LoadingEllipsis />
    </div>
    {/if}
  </div>
  {#if showLayerPanel}
  <nav style="justify-content: end;">
    <label title="Change preview opacity">
      Preview (p)
      <select title="Set preview (w)" bind:value={previewMode} disabled={previewMode == "n/a"}>
        {#if previewMode == "n/a"}<option value="n/a" disabled>n/a</option>{/if}
        <option value="none">none</option>
        <option value="transparent">1/2</option>
        <option value="full">full</option>
      </select>
    </label>
    <label title="Change reference layer">
      Reference (r)
      <select  style="width:151px;" bind:value={currentRefLayer}>
        {#each refLayers as refLayer}
        <option value={refLayer.id} disabled={refLayer.disabled}>{refLayer.label}</option>
        {/each}
      </select>
    </label>
    {#if pmLayer}
    <label class="checkbox">
      Snap to Parcels
      <input type="checkbox" bind:checked={enableSnapLayer} disabled={currentZoom<=17} />
    </label>
    {/if}
    <label title="Change basemap">
      Basemap (b)
      <select  style="width:151px;" bind:value={currentBasemap}>
        <option value="osm">Streets</option>
        <option value="satellite">Streets+Satellite</option>
      </select>
    </label>
  </nav>
  {/if}
  {#if showSettingsPanel}
  <nav style="justify-content: end;">
    <label title="Set georeferencing transformation">
      Transformation:
      <select class="trans-select" style="width:151px;" bind:value={currentTransformation} on:change={getPreview}>
        {#each transformations as trans}
        <option value={trans.id}>{trans.name}</option>
        {/each}
      </select>
    </label>
  </nav>
  {/if}
  {#if showNotePanel}
  <nav style="justify-content: start;">
    <label title="Add note about control point {activeGCP}">
      <span class="">Note:</span>
      <input type="text" id="{noteInputElId}" style="height:30px; width:250px;" disabled={gcpList.length == 0} on:change={updateNote}>
    </label>
  </nav>
  {/if}
  <nav>
    <div style="display:flex; flex-direction:column;">
      {#if gcpList.length == 0}
      <div>
        <em>no control points added yet...</em>
      </div>
      {:else}
      <div id="summary-panel" style="display:flex; flex-direction:row">
        <select class="gcp-select" bind:value={activeGCP}>
          {#each gcpList as gcp}
            <option value={gcp.listId}>
              {gcp.listId} | ({gcp.pixelX}, {gcp.pixelY}) ({gcp.coordX}, {gcp.coordY}) | {gcp.username}
            </option>
          {/each}
        </select>
        <ToolUIButton action={removeActiveGCP} title="Remove control point {activeGCP} (d)"><Trash /></ToolUIButton>
        <ToolUIButton action={() => {showNotePanel=!showNotePanel}} onlyIcon={false} title="">Show/edit note for this GCP...</ToolUIButton>
      </div>
      {/if}
    </div>
    <div style="display:flex; flex-direction:row; text-align:right;">
      <div class="control-btn-group">
        <ToolUIButton action={() => {showSettingsPanel=!showSettingsPanel}} title="Show/hide advanced settings..."><GearSix /></ToolUIButton>
        <ToolUIButton action={() => {showLayerPanel=!showLayerPanel}} title="Show/hide layer panel..."><Stack /></ToolUIButton>
      </div>
      <!--
      <div>
        <label style="margin-top:5px;" title="Set georeferencing transformation">
          Projection:
          <select class="trans-select" style="width:151px;" bind:value={currentTargetProjection} on:change={getPreview}>
            {#each availableProjections as proj}
              <option value={proj.id}>{proj.name}</option>
            {/each}
          </select>
        </label>
      </div>-->
    </div>
  </nav>
</div>

<style>

label {
  margin: 0px;
}

.map-item {
  width: 50%;
}

.gcp-select {
    max-width: 400px;
  }

@media screen and (max-width: 768px){
  .gcp-select {
    max-width: 300px;
  }
}

</style>
