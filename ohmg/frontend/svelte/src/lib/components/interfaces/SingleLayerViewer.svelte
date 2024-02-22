<script>
    import {onMount} from 'svelte';

    import IconContext from 'phosphor-svelte/lib/IconContext';
    import CornersOut from "phosphor-svelte/lib/CornersOut";

    import 'ol/ol.css';
    
    import Map from 'ol/Map';
    import {ZoomToExtent, defaults as defaultControls} from 'ol/control.js';
    
    import {transformExtent} from 'ol/proj';

    import MousePosition from 'ol/control/MousePosition';
    import {createStringXY} from 'ol/coordinate';

    import {XYZ} from 'ol/source';
    import {Tile as TileLayer} from 'ol/layer';
    
    import '@src/css/ol-overrides.css';
    import {
        iconProps,
        makeTitilerXYZUrl,
        makeBasemaps,
    } from '@helpers/utils';

    import { LyrMousePosition } from '@helpers/controls';

    export let EXTENT;
    export let MAPBOX_API_KEY;
    export let TITILER_HOST;
    export let LAYER_URL;

    let currentZoom = '';

    class Viewer {
        constructor(elementId) {

            const targetElement = document.getElementById(elementId);

            const basemaps = makeBasemaps(MAPBOX_API_KEY);
            const extent = transformExtent(EXTENT, "EPSG:4326", "EPSG:3857");

            const resLayer = new TileLayer({
                source: new XYZ({
                    url: makeTitilerXYZUrl({
                        host: TITILER_HOST,
                        url: LAYER_URL,
                    }),
                }),
                extent: extent
            });

            const map = new Map({
                target: targetElement,
                layers: [basemaps[0].layer, resLayer],
                controls: defaultControls().extend([
                    new ZoomToExtent({
                        extent: extent,
                        label: document.getElementById('extent-icon-lyr'),
                    }),
                    new LyrMousePosition('pointer-coords-lyr'),
                ]),
            });

            function roundedZoom() {
                return Math.round(map.getView().getZoom() * 10) / 10
            }
            currentZoom = roundedZoom()

            map.getView().on('change:resolution', () => {
                currentZoom = roundedZoom()
            })

            map.getView().fit(extent);

            this.map = map;
        }
    }

    let viewer;
    onMount(() => {
        viewer = new Viewer('lyr-viewer');
    })
</script>
<IconContext values={iconProps}>
<div style="height:100%;">
    <div id="lyr-viewer">
        <i id='extent-icon-lyr'><CornersOut size={'20px'} /></i>
    </div>
    <div id="info-row">
        <div id="info-box">
            <span>z: {currentZoom} |&nbsp;</span>
            <span id="pointer-coords-lyr"></span>
        </div>
    </div>
</div>
</IconContext>

<style>
    #lyr-viewer {
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
        background-color: rgba(255,255,255,.6);
        align-items: center;
        align-items: center;
        padding: 0 10px;
        font-size: .8em;
    }
</style>
