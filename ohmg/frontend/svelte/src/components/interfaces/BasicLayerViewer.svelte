<script>
  import { onMount } from 'svelte';

  import CornersOut from 'phosphor-svelte/lib/CornersOut';

  import 'ol/ol.css';

  import { transformExtent } from 'ol/proj';

  import { XYZ } from 'ol/source';
  import { Tile as TileLayer } from 'ol/layer';

  import { makeTitilerXYZUrl } from '../../lib/utils';
  import { LyrMousePosition } from '../../lib/controls';
  import { MapViewer } from '../../lib/viewers';

  import '../../css/ol-overrides.css';

  export let CONTEXT;
  export let LAYER_URL;
  export let EXTENT;

  let currentZoom;

  onMount(() => {
    const viewer = new MapViewer('map-viewer');

    const extent = transformExtent(EXTENT, 'EPSG:4326', 'EPSG:3857');
    viewer.addZoomToExtentControl(extent, 'extent-icon-doc');
    viewer.addControl(new LyrMousePosition('doc-coords', null));
    viewer.addBasemaps(CONTEXT.mapbox_api_token);
    viewer.addLayer(
      new TileLayer({
        source: new XYZ({
          url: makeTitilerXYZUrl({
            host: CONTEXT.titiler_host,
            url: LAYER_URL,
          }),
        }),
        extent: extent,
      }),
    );
    viewer.setExtent(extent);

    viewer.map.getView().on('change:resolution', () => {
      currentZoom = viewer.getZoom();
    });
    currentZoom = viewer.getZoom();
  });
</script>

<div style="height:100%;">
  <div id="map-viewer">
    <i id="extent-icon-doc"><CornersOut size={'20px'} /></i>
  </div>
  <div id="info-row">
    <div id="info-box">
      <span>z: {currentZoom} |&nbsp;</span>
      <span id="doc-coords"></span>
    </div>
  </div>
</div>

<style>
  #map-viewer {
    height: 100%;
    width: 100%;
  }
  #info-row {
    position: relative;
    display: flex;
    justify-content: start;
    max-width: 200px;
    margin-top: -25px;
    height: 25px;
  }
  #info-box {
    display: flex;
    justify-content: start;
    background-color: rgba(255, 255, 255, 0.6);
    align-items: center;
    align-items: center;
    padding: 0 10px;
    font-size: 0.8em;
  }
</style>
