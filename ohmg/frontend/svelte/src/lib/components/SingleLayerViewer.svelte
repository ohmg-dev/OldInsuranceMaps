<script>
    import {onMount} from 'svelte';

    import IconContext from 'phosphor-svelte/lib/IconContext';
    import { iconProps } from "../../js/utils"
    import CornersOut from "phosphor-svelte/lib/CornersOut";

    import 'ol/ol.css';
    import '../../css/ol-overrides.css';

    import Map from 'ol/Map';
    import {ZoomToExtent, defaults as defaultControls} from 'ol/control.js';

    import {transformExtent} from 'ol/proj';

    import {XYZ} from 'ol/source';
    import {Tile as TileLayer} from 'ol/layer';

    import {
        makeTitilerXYZUrl,
        makeBasemaps,
    } from '../../js/utils';

    export let EXTENT;
    export let MAPBOX_API_KEY;
    export let TITILER_HOST;
    export let LAYER_URL;

    function LayerViewer () {

        const targetElement = document.getElementById('lyr-viewer');

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

        const extentIconEl = document.getElementById('lyr-extent-icon')

        const map = new Map({
            target: targetElement,
            layers: [basemaps[0].layer, resLayer],
            controls: defaultControls().extend([
                new ZoomToExtent({
                    extent: extent,
                    label: extentIconEl,
                }),
            ]),
        });

        map.getView().fit(extent);

        this.map = map;
    }

    let viewer;
    onMount(() => {
        viewer = new LayerViewer();
    })
</script>
<IconContext values={iconProps}>
    <i id='lyr-extent-icon'><CornersOut size={'20px'} /></i>
    <div id="lyr-viewer" style="height:100%; width:100%;"></div>
</IconContext>
