<script>
  import { onMount } from 'svelte';

  import Overlay from 'ol/Overlay';

  import 'ol/ol.css';
  import View from 'ol/View';

  import GeoJSON from 'ol/format/GeoJSON';

  import VectorSource from 'ol/source/Vector';
  import VectorLayer from 'ol/layer/Vector';

  import Styles from '../../lib/ol-styles';
  import { MapViewer } from '../../lib/viewers';

  const styles = new Styles();

  export let CONTEXT;
  export let MAP_HEIGHT = '600';
  export let EMBEDDED = false;

  let container;
  let content;
  let overlay;

  let viewer;
  onMount(async function () {
    viewer = new MapViewer('map-viewer');
    viewer.addBasemaps();

    container = document.getElementById('popup');
    content = document.getElementById('popup-content');
    overlay = new Overlay({
      element: container,
      autoPan: {
        animation: {
          duration: 250,
        },
      },
    });

    viewer.addOverlay(overlay);

    viewer.setView(
      new View({
        zoom: 5,
        // center: fromLonLat([-92.036, 31.16]),
        center: [-10728204.02342, 4738596.138147663],
        maxZoom: 15,
      }),
    );

    const response = await fetch('/api/beta2/places/geojson', {
      headers: CONTEXT.ohmg_api_headers,
    });
    const mapGeoJSON = await response.json();

    const placeLayer = new VectorLayer({
      source: new VectorSource({
        features: new GeoJSON().readFeatures(mapGeoJSON, {
          dataProjection: 'EPSG:4326',
          featureProjection: 'EPSG:3857',
        }),
      }),
      style: styles.browseMapStyle,
      zIndex: 500,
    });
    viewer.addLayer(placeLayer);
    viewer.map.getView().fit(placeLayer.getSource().getExtent(), {
      padding: [25, 25, 25, 25],
      duration: 500,
    });

    viewer.map.on('pointermove', function (event) {
      let hit = false;
      viewer.map.forEachFeatureAtPixel(
        event.pixel,
        function (feature) {
          if (hit) return; // only hover on one point at a time
          hit = true;
        },
        {
          hitTolerance: 2,
        },
      );
      viewer.element.style.cursor = hit ? 'pointer' : 'default';
    });

    viewer.map.on('singleclick', function (event) {
      let hit = false;
      viewer.map.forEachFeatureAtPixel(
        event.pixel,
        function (feature) {
          if (hit) return; // only hover on one point at a time
          const props = feature.getProperties();
          const volList = [];
          props.volumes.forEach(function (vol) {
            volList.push(`<a title="Go to item summary: ${vol.title}" href="${vol.url}">${vol.year}</a>`);
          });
          const volListStr = volList.join(' • ');
          const popupContent = `
					<h4 style="margin-bottom:0px;">${props.place.display_name}</h4>
					<p><a title="Go to viewer" href="${props.place.url}">Go to viewer &rarr;</a></p>
					<div style="margin-bottom:15px;">
						<div style="border-bottom:1px dashed #000; height:12px; margin-bottom:10px;">
							<span style="background:#fff; padding-right:5px;">Content</span>
						</div>
					</div>
					<p>${volListStr}</p>
				`;
          content.innerHTML = popupContent;
          overlay.setPosition(feature.getGeometry().getCoordinates());
          hit = true;
        },
        {
          hitTolerance: 2,
        },
      );
      if (!hit) {
        overlay.setPosition(undefined);
      }
    });
    viewer.element.classList.remove('spinner');
  });

  function closePopup() {
    overlay.setPosition(undefined);
    return false;
  }
</script>

{#if EMBEDDED}
  <!-- svelte-ignore a11y-no-noninteractive-tabindex -->
  <div
    id="map-viewer"
    tabindex="0"
    class="spinner"
    style="height:{MAP_HEIGHT}px; width:100%; cursor:{EMBEDDED ? 'pointer' : 'default'};"
  ></div>
{:else}
  <div id="map-viewer" class="spinner" style="height:{MAP_HEIGHT}px; width:100%"></div>
{/if}
<div id="popup" class="ol-popup" style="">
  <button class="close-popup" on:click={closePopup} title="close">x</button>
  <div id="popup-content"></div>
</div>

<style>
  @keyframes spinner {
    to {
      transform: rotate(360deg);
    }
  }

  #map-viewer {
    position: relative;
  }

  #map-viewer:focus {
    outline: #4a74a8 solid 0.15em;
  }

  .spinner:after {
    content: '';
    box-sizing: border-box;
    position: absolute;
    top: 50%;
    left: 50%;
    width: 40px;
    height: 40px;
    margin-top: -20px;
    margin-left: -20px;
    border-radius: 50%;
    border: 5px solid rgba(180, 180, 180, 0.6);
    border-top-color: rgb(18, 59, 79);
    animation: spinner 0.8s linear infinite;
  }

  .ol-popup {
    position: absolute;
    background-color: white;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #cccccc;
    bottom: 12px;
    left: -50px;
    min-width: 280px;
    z-index: 1000000000;
  }
  .ol-popup:after,
  .ol-popup:before {
    top: 100%;
    border: solid transparent;
    content: ' ';
    height: 0;
    width: 0;
    position: absolute;
    pointer-events: none;
  }
  .ol-popup:after {
    border-top-color: white;
    border-width: 10px;
    left: 48px;
    margin-left: -10px;
  }
  .ol-popup:before {
    border-top-color: #cccccc;
    border-width: 11px;
    left: 48px;
    margin-left: -11px;
  }
  button.close-popup {
    float: right;
    background: none;
    border: none;
  }
</style>
