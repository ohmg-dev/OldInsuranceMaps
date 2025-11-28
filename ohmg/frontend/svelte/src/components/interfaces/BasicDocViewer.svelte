<script>
  import { onMount } from 'svelte';

  import CornersOut from 'phosphor-svelte/lib/CornersOut';

  import View from 'ol/View';

  import { Projection } from 'ol/proj';

  import { ImageStatic } from 'ol/source';
  import { Image as ImageLayer } from 'ol/layer';

  import { DocMousePosition } from '../../lib/controls';
  import { MapViewer } from '../../lib/viewers';

  export let LAYER_URL;
  export let EXTENT;

  let currentZoom;

  onMount(() => {
    const viewer = new MapViewer('doc-viewer');

    viewer.addZoomToExtentControl(EXTENT, 'extent-icon-doc');
    viewer.addControl(new DocMousePosition(EXTENT, 'doc-coords', null));
    const projection = new Projection({
      units: 'pixels',
      extent: EXTENT,
    });
    const view = new View({
      projection: projection,
      zoom: 1,
      maxZoom: 8,
    });
    viewer.setView(view);

    viewer.addLayer(
      new ImageLayer({
        source: new ImageStatic({
          url: LAYER_URL,
          projection: projection,
          imageExtent: EXTENT,
        }),
      }),
    );
    viewer.setExtent(EXTENT);

    viewer.map.getView().on('change:resolution', () => {
      currentZoom = viewer.getZoom();
    });
    currentZoom = viewer.getZoom();
  });
</script>

<div style="height:100%;">
  <div id="doc-viewer">
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
  #doc-viewer {
    background: url('../../static/img/sandpaper-bg-vlite.jpg');
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
