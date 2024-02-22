<script>
import {onMount} from 'svelte';

import IconContext from 'phosphor-svelte/lib/IconContext';
import CornersOut from 'phosphor-svelte/lib/CornersOut';
import MapboxLogoLink from "./buttons/MapboxLogoLink.svelte"

import OpenModalButton from "@components/base/OpenModalButton.svelte"
import BasemapToggleButton from "./buttons/BasemapToggleButton.svelte"
import ExpandElement from "./buttons/ExpandElement.svelte"

import LegendModal from "./modals/LegendModal.svelte"

import 'ol/ol.css';
import Map from 'ol/Map';
import {transformExtent} from 'ol/proj';
import MousePosition from 'ol/control/MousePosition';
    import {createStringXY} from 'ol/coordinate';
import {OSM, XYZ} from 'ol/source';

import {
	Tile as TileLayer,
	Group as LayerGroup,
} from 'ol/layer';

import {ZoomToExtent, defaults as defaultControls} from 'ol/control.js';

import '@src/css/map-panel.css';
import {
	iconProps,
	makeLayerGroupFromVolume,
	setMapExtent,
	makeBasemaps,
} from '@helpers/utils';

export let VOLUME;
export let MAPBOX_API_KEY;
export let TITILER_HOST;

let map;

function getClass(n) {
	if (n == 100) {
		return "full-circle"
	} else if (n == 0) {
		return "empty-circle"
	} else {
		return "half-circle"
	}
}

const basemaps = makeBasemaps(MAPBOX_API_KEY);
let currentBasemap = 'satellite';

function toggleBasemap() {
  if (currentBasemap === "osm") {
    currentBasemap = "satellite"
  } else {
    currentBasemap = "osm"
  }
}

// triggered by a change in the basemap id
function setBasemap(basemapId) {
  if (viewer) {
    viewer.map.getLayers().removeAt(0);
    basemaps.forEach( function(item) {
      if (item.id == basemapId) {
        viewer.map.getLayers().insertAt(0, item.layer);
      }
    });
  }
}
$: setBasemap(currentBasemap);

function toggleTransparency(inTrans) {
	let outTrans;
	if (inTrans == 100) {
		outTrans = 0
	} else if (inTrans == 0) {
		outTrans = 50
	} else {
		outTrans = 100
	}
	return outTrans
}

function setVisibility(group, vis) {
	if (vis == 0) {
		group.setVisible(false)
	} else {
		group.setVisible(true)
		group.setOpacity(vis/100)
	}
}

let layerSets = {
	"key-map": {
		name: "Key Map",
		layerGroup: new LayerGroup(),
		opacity: 100,
		layerCt: 0,
	},
	"main": {
		name: "Main Content",
		layerGroup: new LayerGroup(),
		opacity: 100,
		layerCt: 0,
	},
}


$: {
	Object.entries(layerSets).forEach( function ([key, item]) {
		setVisibility(item.layerGroup, item.opacity)
	})
}

let currentZoom = '';
class MapPreviewViewer {
	constructor(elementId) {
		map = new Map({
			target: document.getElementById(elementId),
			maxTilesLoading: 50,
			controls: defaultControls().extend([
				new ZoomToExtent({
					extent:  transformExtent(VOLUME.extent, "EPSG:4326", "EPSG:3857"),
					label: document.getElementById('extent-icon-preview'),
				}),
			]),
			layers: [
				basemaps[1].layer,
			]
		});

		let mousePositionControl = new MousePosition({
			projection: 'EPSG:4326',
			coordinateFormat: createStringXY(6),
			placeholder: 'n/a',
			target: document.getElementById('pointer-coords-preview'),
			className: null,
		});
		map.addControl(mousePositionControl);

		Object.entries(layerSets).forEach( function ([key, item]) {
			map.addLayer(item.layerGroup)
		})

		map.getView().on('change:resolution', () => {
			const z = map.getView().getZoom()
			currentZoom = Math.round(z*10)/10
		})

		this.map = map;
	}
};

let layerSetList = [];

function updateLayerSets() {
	layerSetList = []
	Object.entries(layerSets).forEach( function ([key, item]) {
		item.layerGroup.getLayers().clear();
		makeLayerGroupFromVolume({
			volume: VOLUME,
			layerSet: key,
			titilerHost: TITILER_HOST,
		}).getLayers().forEach( function(lyr) {
			item.layerGroup.getLayers().push(lyr)
		})
		item.layerCt = item.layerGroup.getLayers().getArray().length;
		layerSetList.push(key)
	});
}

let viewer;
onMount(() => {
	viewer = new MapPreviewViewer('map');
	updateLayerSets();
	setMapExtent(map, VOLUME.extent)
});

</script>

<IconContext values={iconProps}>
<LegendModal id={"modal-legend"} legendUrl={"/static/img/key-nola-1940.png"} legendAlt={"Sanborn Map Key"} />
<div id="map-container" class="map-container"  style="display:flex; justify-content: center; height:550px">
	<div id="map-panel">
		<div id="map" style="height: 100%;">
		</div>
		<i id='extent-icon-preview'><CornersOut size={'20px'} /></i>
		{#if currentBasemap == "satellite"}
			<MapboxLogoLink />
		{/if}
	</div>
	<div id="layer-panel" style="display: flex;">
		<div class="layer-section-header" style="border-top-width: 1px;">
			<OpenModalButton style="tool-ui" icon="article" modalId={"modal-legend"} />
			<ExpandElement elementId={'map-container'} maps={[map]} />
		</div>
		<div id="layer-list" style="flex:2;">
			<div class="layer-section-header">
				<span>Basemap</span>
				<BasemapToggleButton action={toggleBasemap} />
			</div>
			<div class="layer-section-subheader">
				{currentBasemap == 'satellite' ? 'Mapbox Imagery' : 'Open Street Map'}
			</div>
			{#each layerSetList as id}
				{#if layerSets[id].layerCt > 0}
				<div class="layer-section-header">
					<span>{layerSets[id].name}</span>
				</div>
				<div class="layer-section-subheader">
					<div style="display:flex; align-items:center;">
						<input class="slider" type=range bind:value={layerSets[id].opacity} min=0 max=100>
						<button class="transparency-toggle" on:click={() => {layerSets[id].opacity = toggleTransparency(layerSets[id].opacity)}}>
							<i class="{getClass(layerSets[id].opacity)}" />
						</button>
					</div>
				</div>
				{/if}
			{/each}
		</div>
		<div id="info-box">
			<span>z: {currentZoom}</span>
			<span id="pointer-coords-preview"></span>
		</div>
	</div>
</div>
</IconContext>
<style>
	#info-box {
		position: relative;
		display: flex;
		flex-direction: column;
		background-color: rgba(255,255,255,.6);
		align-items: end;
		padding: 0 10px;
		font-size: .8em;
	}
</style>