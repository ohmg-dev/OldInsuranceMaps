<script>
import {onMount} from 'svelte';

import Icon from 'svelte-icons-pack/Icon.svelte';
import FiMaximize from 'svelte-icons-pack/fi/FiMaximize';
import FiMaximize2 from 'svelte-icons-pack/fi/FiMaximize2';
import FiMinimize2 from 'svelte-icons-pack/fi/FiMinimize2';
import FiHome from 'svelte-icons-pack/fi/FiHome';
import FiKey from 'svelte-icons-pack/fi/FiKey';
import FiCode from 'svelte-icons-pack/fi/FiCode';
import FiInfo from 'svelte-icons-pack/fi/FiInfo';

import 'ol/ol.css';
import Map from 'ol/Map';
import {transformExtent} from 'ol/proj';
import {OSM, XYZ} from 'ol/source';

import {
	Tile as TileLayer,
	Group as LayerGroup,
} from 'ol/layer';

import '../css/map-panel.css';
import {toggleFullscreen, makeLayerGroupFromVolume} from '../js/utils';

import Modal, {getModal} from './Modal.svelte';

export let VOLUME;
export let MAPBOX_API_KEY;
export let TITILER_HOST;

let map;
let layersPresent = VOLUME.items.layers.length > 0;
let showMap = layersPresent

let kGV = 100;
let mGV = 100;

const baseGroup = new LayerGroup({
	// zIndex: 0
});
let currentBasemap;
const keyGroup = new LayerGroup({
	// zIndex: 100
});
const mainGroup = new LayerGroup({
	// zIndex: 200
});

const keyImgUrl = "/static/img/key-nola-1940.png"
const keyImgCaption = "Sanborn Map Key"

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
$: setVisibility(keyGroup, kGV)
$: setVisibility(mainGroup, mGV)

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
	map.addLayer(keyGroup);
	map.addLayer(mainGroup);
	setLayersFromVolume(true);
};

function setLayersFromVolume(setExtent) {
	
	// only run this function if a new layer has been added, i.e. the map needs to
	// be redrawn.
	if (
		VOLUME.sorted_layers.key_map.length == keyGroup.getLayers().length ||
		VOLUME.sorted_layers.main.length == mainGroup.getLayers().length
	) { return }

	mainGroup.getLayers().clear();
	keyGroup.getLayers().clear();

	// use this function to get a LayerGroup, but don't use it, just iterate
	// its layers and add them to the existing groups.
	makeLayerGroupFromVolume({
		volume: VOLUME,
		layerSet: "main",
		titilerHost: TITILER_HOST,
	}).getLayers().forEach( function(lyr) {
		mainGroup.getLayers().push(lyr)
	})
	makeLayerGroupFromVolume({
		volume: VOLUME,
		layerSet: "key-map",
		titilerHost: TITILER_HOST,
	}).getLayers().forEach( function(lyr) {
		keyGroup.getLayers().push(lyr)
	})

	if (setExtent) { setMapExtent() };
}

function setMapExtent() {
	if (map) {
		const extent3857 = transformExtent(VOLUME.extent, "EPSG:4326", "EPSG:3857");
		map.getView().fit(extent3857);
	}
}

onMount(() => {
	initMap();
});

let inFullscreen = false;

</script>
<Modal id="modal-map-key">
	<img src={keyImgUrl} alt={keyImgCaption}>
</Modal>
<div id="map-container" class="map-container"  style="display:flex; justify-content: center; height:550px">
	<div id="map-panel">
		<div id="map" style="height: 100%;"></div>
	</div>
	<div id="layer-panel" style="display: flex;">
		<div class="layer-section-header" style="border-top-width: 1px;">
			<button class="control-btn" title="Go to full extent" on:click={setMapExtent}>
				<Icon src={FiMaximize} />
			</button>
			<button class="control-btn" on:click={() => {getModal('modal-map-key').open()}}>
				<Icon src={FiKey} />
			</button>
			<button class="control-btn" title={inFullscreen ? "Exit fullscreen" : "Enter fullscreen"} on:click={() => {inFullscreen = toggleFullscreen('map-container')}}>
				{#if inFullscreen}
				<Icon src={FiMinimize2} />
				{:else}
				<Icon src={FiMaximize2} />
				{/if}
			</button>
		</div>
		<div id="layer-list" style="flex:2;">
			
			<div class="layer-section-header">
				<span>Basemap</span>
				<button class="control-btn" title="Toggle basemap" on:click={toggleBasemap}>
					<Icon src={FiCode} />
				</button>
			</div>
			<div class="layer-section-subheader">
				{currentBasemap}
			</div>
			
			<div class="layer-section-header">
				<span>Key Map</span>
				<i class="transparency-toggle {getClass(kGV)}" on:click={() => {kGV = toggleTransparency(kGV)}}></i>
			</div>
			<div class="layer-section-subheader">
				{#if VOLUME.sorted_layers.key_map.length == 0}
				<em>no key map set</em>
				{:else}
				<input type=range bind:value={kGV} min=0 max=100>
				{/if}
			</div>
			<div class="layer-section-header">
				<span>Main Layers</span>
				<i class="transparency-toggle {getClass(mGV)}" on:click={() => {mGV = toggleTransparency(mGV)}}></i>
			</div>
			<div class="layer-section-subheader">
				{#if VOLUME.sorted_layers.main.length == 0}
				<em>no layers</em>
				{:else}
				<input type=range bind:value={mGV} min=0 max=100>
				{/if}
			</div>
		</div>
	</div>
</div>
