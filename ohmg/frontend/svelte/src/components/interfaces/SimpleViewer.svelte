<script>
    import {onMount} from 'svelte';

    import IconContext from 'phosphor-svelte/lib/IconContext';
    import CornersOut from "phosphor-svelte/lib/CornersOut";

    import 'ol/ol.css';
    
    import Map from 'ol/Map';
    import View from 'ol/View';
    import {ZoomToExtent, defaults as defaultControls} from 'ol/control.js';

    import {Projection, transformExtent} from 'ol/proj';

    import {XYZ} from 'ol/source';
    import {Tile as TileLayer} from 'ol/layer';
    
    import {ImageStatic} from 'ol/source';
    import {Image as ImageLayer} from 'ol/layer';

    import {
        iconProps,
        makeTitilerXYZUrl,
        makeBasemaps,
    } from '@lib/utils';
    import { DocMousePosition, LyrMousePosition } from '@lib/controls';

    import '@src/css/ol-overrides.css';
    
    export let CONTEXT;
    export let LAYER_URL;
    export let EXTENT;
    export let GEOSPATIAL = false;

    let currentZoom = '';

    class DocViewer {
        constructor(elementId) {

            let view;
            let mousePositionControl;
            const layers = [];

            if (GEOSPATIAL) {
                EXTENT = transformExtent(EXTENT, "EPSG:4326", "EPSG:3857");

                const basemaps = makeBasemaps(CONTEXT.mapbox_api_token);
                layers.push(basemaps[0].layer)
                
                const resLayer = new TileLayer({
                    source: new XYZ({
                        url: makeTitilerXYZUrl({
                            host: CONTEXT.titiler_host,
                            url: LAYER_URL,
                        }),
                    }),
                    extent: EXTENT
                });
                layers.push(resLayer)

                mousePositionControl = new LyrMousePosition('doc-coords')

            } else {
                const projection = new Projection({
                    units: 'pixels',
                    extent: EXTENT,
                });
                view = new View({
                    projection: projection,
                    zoom: 1,
                    maxZoom: 8,
                })
                mousePositionControl = new DocMousePosition('doc-coords', EXTENT, projection)

                layers.push(new ImageLayer({
                        source: new ImageStatic({
                            url: LAYER_URL,
                            projection: projection,
                            imageExtent: EXTENT,
                        }),
                    })
                )
            }

            const map = new Map({
                target: document.getElementById(elementId),
                layers: layers,
                controls: defaultControls().extend([
                    new ZoomToExtent({
                        extent: EXTENT,
                        label: document.getElementById('extent-icon-doc'),
                    }),
                    mousePositionControl,
                ]),
            });

            view && map.setView(view)
            map.getView().fit(EXTENT);

            function roundedZoom() {
                return Math.round(map.getView().getZoom() * 10) / 10
            }
            currentZoom = roundedZoom()

            map.getView().on('change:resolution', () => {
                currentZoom = roundedZoom()
            })

            this.map = map;
        }
    }

    let viewer;
    onMount(() => {
        viewer = new DocViewer('doc-viewer');
    })
</script>
<IconContext values={iconProps}>
<div style="height:100%;">
    <div id="doc-viewer">
        <i id='extent-icon-doc'><CornersOut size={'20px'} /></i>
    </div>
    <div id="info-row">
        <div id="info-box">
            <span>z: {currentZoom} |&nbsp;</span>
            <span id="doc-coords"></span>
        </div>
    </div>
</div>
</IconContext>
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
        background-color: rgba(255,255,255,.6);
        align-items: center;
        align-items: center;
        padding: 0 10px;
        font-size: .8em;
    }
</style>
