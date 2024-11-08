<script>
import {onMount} from 'svelte';

import CornersOut from 'phosphor-svelte/lib/CornersOut';
import Article from 'phosphor-svelte/lib/Article';
import MapTrifold from "phosphor-svelte/lib/MapTrifold";

import ToolUIButton from "@components/base/ToolUIButton.svelte";
import {getModal} from "@components/base/Modal.svelte";

import ExpandElement from "./buttons/ExpandElement.svelte"
import MapboxLogoLink from "./buttons/MapboxLogoLink.svelte"

import LegendModal from "./modals/LegendModal.svelte"

import 'ol/ol.css';
import Map from 'ol/Map';
import {createEmpty, extend} from 'ol/extent';
import {transformExtent} from 'ol/proj';
import MousePosition from 'ol/control/MousePosition';
    import {createStringXY} from 'ol/coordinate';

import {ZoomToExtent, defaults as defaultControls} from 'ol/control.js';

import '@src/css/map-panel.css';
import {
	makeLayerGroupFromLayerSet,
	makeBasemaps,
} from '@lib/utils';

export let CONTEXT;
export let LAYERSETS;

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

const basemaps = makeBasemaps(CONTEXT.mapbox_api_token);
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

const zIndexLookup = {
	"graphic-map-of-volumes": 10,
	"key-map": 15,
	"congested-district-map": 20,
	"main-content": 25,
}
LAYERSETS.sort((a, b) => zIndexLookup[a.id] - zIndexLookup[b.id]);

let currentZoom = '';
class MapPreviewViewer {
	constructor(elementId) {
		map = new Map({
			target: document.getElementById(elementId),
			maxTilesLoading: 50,
			controls: defaultControls().extend([
				new ZoomToExtent({
					extent: fullExtent,
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

		// Object.entries(layerSets).forEach( function ([key, item]) {
		// 	map.addLayer(item.layerGroup)
		// })

		map.getView().on('change:resolution', () => {
			const z = map.getView().getZoom()
			currentZoom = Math.round(z*10)/10
		})

		this.map = map;
	}
};

const layerSets = {};
let layerSetList = [];

$: {
	Object.entries(layerSets).forEach( function ([key, ls]) {
		setVisibility(ls.layerGroup, ls.opacity)
	})
}

const fullExtent = createEmpty();

function createLayerGroups() {

	LAYERSETS.forEach( function( ls ){
		if (ls.layers.length > 0) {
			const layerGroup = makeLayerGroupFromLayerSet({
				layerSet: ls,
				zIndex: zIndexLookup[ls.id],
				titilerHost: CONTEXT.titiler_host,
				applyMultiMask: true,
			})
			let extent3857;
			if (ls.extent) {
				extent3857 = transformExtent(ls.extent, "EPSG:4326", "EPSG:3857")
				extend(fullExtent, extent3857)
			}
			const setDef = {
				id: ls.id,
				name: ls.name,
				layerGroup: layerGroup,
				sortOrder: zIndexLookup[ls.id],
				opacity: 100,
				layerCt: ls.layers.length,
				extent: extent3857
			}
			layerSets[ls.id] = setDef
			layerSetList.push(ls.id)
			map.addLayer(setDef.layerGroup)
		}
	})
}

let viewer;
onMount(() => {
	viewer = new MapPreviewViewer('map');
	createLayerGroups();
	map.getView().fit(fullExtent)
});

</script>

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
			<ToolUIButton action={() => {getModal('modal-legend').open()}}>
				<Article />
			</ToolUIButton>
			<ExpandElement elementId={'map-container'} maps={[map]} />
		</div>
		<div id="layer-list" style="flex:2;">
			<div class="layer-section-header">
				<span>Basemap</span>
				<ToolUIButton action={toggleBasemap} title="change basemap">
					<MapTrifold />
				</ToolUIButton>
			</div>
			<div class="layer-section-subheader">
				{currentBasemap == 'satellite' ? 'Mapbox Imagery' : 'Open Street Map'}
			</div>
			{#each layerSetList as id}
				{#if layerSets[id].layerCt > 0}
				<div class="layer-section-header">
					<button class="layer-entry" on:click={() => map.getView().fit(layerSets[id].extent)} on:focus={null}>
						<span>{layerSets[id].name}</span>
					</button>
					<span style="color:grey">({layerSets[id].layerCt})</span>
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
