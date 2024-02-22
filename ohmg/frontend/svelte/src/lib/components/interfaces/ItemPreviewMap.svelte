<script>
import {onMount} from 'svelte';

import IconContext from 'phosphor-svelte/lib/IconContext';

import OpenModalButton from "@components/base/OpenModalButton.svelte"
import BasemapToggleButton from "./buttons/BasemapToggleButton.svelte"
import ExpandElement from "./buttons/ExpandElement.svelte"
import FullExtentButton from "./buttons/FullExtentButton.svelte"

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

import '@src/css/map-panel.css';
import {
	iconProps,
	makeLayerGroupFromVolume,
	setMapExtent,
} from '@helpers/utils';

export let VOLUME;
export let MAPBOX_API_KEY;
export let TITILER_HOST;

let map;

const baseGroup = new LayerGroup();
let currentBasemap;

function getClass(n) {
	if (n == 100) {
		return "full-circle"
	} else if (n == 0) {
		return "empty-circle"
	} else {
		return "half-circle"
	}
}

function toggleBasemap() {
	baseGroup.getLayers().forEach( function(layer) {
		layer.setVisible(!layer.getVisible())
		if (layer.getVisible() == true) {
			currentBasemap = layer.get('name')
		}
	})
}

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

function initMap() {
	map = new Map({ 
		target: "map",
		maxTilesLoading: 50,
	});
	const osmLayer = new TileLayer({
		source: new OSM(),
		zIndex: 0,
	});
	osmLayer.setVisible(false)
	osmLayer.set('name', 'Open Street Map')
	
	const imageryLayer = new TileLayer({
		source: new XYZ({
			url: 'https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v10/tiles/{z}/{x}/{y}?access_token='+MAPBOX_API_KEY,
			tileSize: 512,
		})
	});
	imageryLayer.setVisible(true)
	imageryLayer.set('name', 'Mapbox Imagery')
	currentBasemap = imageryLayer.get('name')
	
	baseGroup.getLayers().push(osmLayer)
	baseGroup.getLayers().push(imageryLayer)
	map.addLayer(baseGroup);
	
	Object.entries(layerSets).forEach( function ([key, item]) {
		map.addLayer(item.layerGroup)
	})
	
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

onMount(() => {
	initMap();
	updateLayerSets();
	setMapExtent(map, VOLUME.extent)
});

</script>

<IconContext values={iconProps}>
<LegendModal id={"modal-legend"} legendUrl={"/static/img/key-nola-1940.png"} legendAlt={"Sanborn Map Key"} />
<div id="map-container" class="map-container"  style="display:flex; justify-content: center; height:550px">
	<div id="map-panel">
		<div id="map" style="height: 100%;"></div>
	</div>
	<div id="layer-panel" style="display: flex;">
		<div class="layer-section-header" style="border-top-width: 1px;">
			<FullExtentButton action={() => {setMapExtent(map, VOLUME.extent)}} />
			<OpenModalButton style="tool-ui" icon="article" modalId={"modal-legend"} />
			<ExpandElement elementId={'map-container'} maps={[map]} />
		</div>
		<div id="layer-list" style="flex:2;">
			<div class="layer-section-header">
				<span>Basemap</span>
				<BasemapToggleButton action={toggleBasemap} />
			</div>
			<div class="layer-section-subheader">
				{currentBasemap}
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
	</div>
</div>
</IconContext>
