<script>
    import {onMount} from 'svelte';

    import IconContext from 'phosphor-svelte/lib/IconContext';
    import { iconProps } from "@helpers/utils"
    import CornersOut from "phosphor-svelte/lib/CornersOut";

    import 'ol/ol.css';
    
    import Map from 'ol/Map';
    import View from 'ol/View';
    import {ZoomToExtent, defaults as defaultControls} from 'ol/control.js';
    
    import {Projection} from 'ol/proj';
    
    import {ImageStatic} from 'ol/source';
    import {Image as ImageLayer} from 'ol/layer';

    import '@src/css/ol-overrides.css';
    
    export let IMAGE_SIZE;
    export let LAYER_URL;

    function DocViewer () {

        const targetElement = document.getElementById('doc-viewer');

        // items needed by layers and map
        // set the extent and projection with 0, 0 at the **top left** of the image
        const docExtent = [0, -IMAGE_SIZE[1], IMAGE_SIZE[0], 0];
        const projection = new Projection({
            units: 'pixels',
            extent: docExtent,
        });

        // create layers
        const resLayer = new ImageLayer({
            source: new ImageStatic({
                url: LAYER_URL,
                projection: projection,
                imageExtent: docExtent,
            }),
        })

        const extentIconEl = document.getElementById('doc-extent-icon')

        const map = new Map({
            target: targetElement,
            layers: [resLayer],
            view: new View({
                projection: projection,
                zoom: 1,
                maxZoom: 8,
            }),
            controls: defaultControls().extend([
                new ZoomToExtent({
                    extent: docExtent,
                    label: extentIconEl,
                }),
            ]),
        });

        map.getView().fit(docExtent);

        this.map = map;
    }

    let viewer;
    onMount(() => {
        viewer = new DocViewer();
    })
</script>
<IconContext values={iconProps}>
    <i id='doc-extent-icon'><CornersOut size={'20px'} /></i>
    <div id="doc-viewer"></div>
</IconContext>
<style>
    #doc-viewer {
        background: url('../../static/img/sandpaper-bg-vlite.jpg');
        height: 100%;
        width: 100%;
    }
</style>