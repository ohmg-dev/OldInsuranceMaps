<script>
import {onMount} from 'svelte';
import { slide } from 'svelte/transition';

import 'ol/ol.css';
import Map from 'ol/Map';
import {transformExtent} from 'ol/proj';
import {OSM, XYZ} from 'ol/source';
import GeoJSON from 'ol/format/GeoJSON';
import {
	Tile as TileLayer,
	Group as LayerGroup,
} from 'ol/layer';

import Crop from 'ol-ext/filter/Crop';

import Utils from '../js/ol-utils';
const utils = new Utils();

export let VOLUME;
export let MAPBOX_API_KEY;
export let TITILER_HOST;

let previewMapTip = false;

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

let mapIndexLayerIds = []; 

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

	// empty the light layers lists used for interactivity, need to be repopulated
	mapIndexLayerIds = [];

	mainGroup.getLayers().clear();
	keyGroup.getLayers().clear();

	VOLUME.sorted_layers.main.forEach( function(layerDef, n) {
		// push to the lightweight list used for the draggable layer list
		const pName = layerDef.title.slice(layerDef.title.lastIndexOf('|')+6, layerDef.title.length)

		// create the actual ol layers and add to group.
		let newLayer = new TileLayer({
			source: new XYZ({
				url: utils.makeTitilerXYZUrl(TITILER_HOST, layerDef.urls.cog),
			}),
			extent: transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857")
		});

		mainGroup.getLayers().push(newLayer)

		if (VOLUME.multimask) {		
			Object.entries(VOLUME.multimask).forEach(kV => {
				if (kV[0] == layerDef.slug) {
					const feature = new GeoJSON().readFeature(kV[1])
				feature.getGeometry().transform("EPSG:4326", "EPSG:3857")
					const crop = new Crop({ 
						feature: feature, 
						wrapX: true,
						inner: false
					});
				newLayer.addFilter(crop);
				}
			});
		}
	});

	VOLUME.sorted_layers.key_map.forEach( function(layerDef, n) {
		const pName = layerDef.title.slice(layerDef.title.lastIndexOf('|')+6, layerDef.title.length)
		mapIndexLayerIds.push(layerDef.slug)

		// create the actual ol layers and add to group.
		let newLayer = new TileLayer({
			source: new XYZ({
				url: utils.makeTitilerXYZUrl(TITILER_HOST, layerDef.urls.cog),
			}),
			extent: transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857")
		});

		keyGroup.getLayers().push(newLayer)
	});

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

function showImgModal(imgUrl, caption) {
	const modalImg = document.getElementById("modalImg")
	modalImg.src = imgUrl;
	modalImg.alt = caption;
	document.getElementById("imgCaption").firstChild.innerHTML = caption;
	document.getElementById("vModal").style.display = "block";
}
function closeModal() {
	document.getElementById("vModal").style.display = "none";
	document.getElementById("modalImg").src = "";
}

function toggleFullscreen () {
	// https://www.w3schools.com/howto/howto_js_fullscreen.asp
	const elem = document.getElementsByClassName('map-container')[0]
	if (document.fullscreenElement == null) {
		if (elem.requestFullscreen) {
			elem.requestFullscreen();
		} else if (elem.webkitRequestFullscreen) { /* Safari */
			elem.webkitRequestFullscreen();
		} else if (elem.msRequestFullscreen) { /* IE11 */
			elem.msRequestFullscreen();
		}
	} else {
		document.exitFullscreen();
	}
}

let fullscreenBtnIcon = 'fa-arrows-alt';
let fullscreenBtnTitle = "Enter fullscreen"
document.addEventListener("fullscreenchange", function(){
	if (document.fullscreenElement == null) {
		fullscreenBtnIcon = 'fa-arrows-alt';
		fullscreenBtnTitle = "Enter fullscreen";
	} else {
		fullscreenBtnIcon = 'fa-close';
		fullscreenBtnTitle = "Exit fullscreen";
	}
}, false);

</script>

<h4>
	Preview Map ({VOLUME.items.layers.length} layers)
	<i class="fa fa-info-circle help-icon" on:click={() => previewMapTip = !previewMapTip}></i>
</h4>
{#if previewMapTip}
<div transition:slide>
	<p>The preview map shows progress toward a full mosaic of this volume's content. For a more immersive experience, view this volume in the <a href="{VOLUME.urls.viewer}">main viewer</a> where you can also compare it against other years.</p>
</div>
{/if}
<div class="map-container"  style="display:flex; justify-content: center; height:550px">
	<div id="map-panel">
		<div id="map" style="height: 100%;"></div>
	</div>
	<div id="layer-panel" style="display: flex;">
		<div class="layer-section-header" style="border-top-width: 1px;">
			<button class="control-btn" title="Reset extent" on:click={setMapExtent}>
				<i class="fa fa-home" />
			</button>
			<button id="show-key-img" on:click={() => {showImgModal(keyImgUrl, keyImgCaption)}} class="control-btn">
				<i class="fa fa-key" />
			</button>
			<button class="control-btn" title={fullscreenBtnTitle} on:click={toggleFullscreen}>
				<i class="fa {fullscreenBtnIcon}" />
			</button>
		</div>
		<div id="layer-list" style="flex:2;">
			
			<div class="layer-section-header">
				<span>Basemap</span>
				<i class="transparency-toggle fa fa-exchange" on:click={toggleBasemap}></i>
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
				<span>Layers</span>
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

<style>

i.help-icon {
	cursor: pointer;
	color: #2c689c;
}
i.help-icon:hover {
	color: #1b4060;
}

#map-panel {
	display: flex;
	flex-direction: column;
	width: 100%;
	border: 1px solid gray;
}

#layer-panel {
	display: flex;
	flex-direction: column;
	justify-content: space-between;
	width: 20%;
	min-width: 115px;
	background: rgb(235, 235, 235);
	border-top: 1px solid gray;
	border-right: 1px solid gray;
	border-bottom: 1px solid gray;
}

#layer-list {
	overflow-y: auto;
}

.control-btn {
	height: 30px;
	width: 30px;
	border-radius: 4px;
	font-size: 19.2px;
}

.layer-section-header {
	display: flex;
	justify-content: space-between;
	flex-wrap: wrap;
	align-items: center;
	font-size: 1.2em;
	border-top: 2px solid grey;
	padding: 5px;
	width: 100%;
	background: lightgray;
}

.layer-section-subheader {
	padding: 5px;
	text-align: center;
	min-height: 35px;
}

.layer-section-content {
	padding: 5px;
	text-align: center;
}

.sheets-status-bar {
	width: 100%;
	display: inline-block;
	vertical-align: middle;
	font-size: .9em;
}

.transparency-toggle {
	display: inline-block;
	cursor: pointer;
	color: #2c689c;
}
.transparency-toggle:hover {
	color: #1b4060;
}

.full-circle {
  background: #2c689c;
  height: 15px;
  width: 15px;
  border: solid #2c689c 3px;
  border-radius: 15px;
}
.full-circle:hover {
	background: #1b4060;
	border-color: #1b4060;
}
.half-circle {
  background: linear-gradient(
    to right, 
    #2c689c 0%, 
    #2c689c 50%, 
    white 50%,
    white 100%
  );
  height: 15px;
  width: 15px;
  border: solid #2c689c 3px;
  border-radius: 15px;
}
.half-circle:hover {
	background: linear-gradient(
		to right, 
		#1b4060 0%, 
		#1b4060 50%, 
		white 50%,
		white 100%
	);
	border-color: #1b4060;
}
.empty-circle {
  background: white;
  height: 15px;
  width: 15px;
  border: solid #2c689c 3px;
  border-radius: 15px;
}
.empty-circle {
	border-color: #1b4060;
}

.title-section {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-top: 20px;
}

/* input[type="range"] {
 -webkit-appearance: none;
}

input[type="range"]:focus {
 outline: none;
} */


/* input[type="range"]::-webkit-slider-runnable-track {
 background: #123B4F;
 height: 5px;
}

input[type="range"]::-moz-range-track {
 background: #123B4F;
 height: 5px;
} */


/* input[type="range"]::-webkit-slider-thumb {
 -webkit-appearance: none;
 height: 15px;
 width: 15px;
 background: #123B4F;
 margin-top: -5px;
 border-radius: 50%;
}

input[type="range"]::-moz-range-thumb {
 height: 15px;
 width: 15px;
 background: #123B4F;
 margin-top: -5px;
 border-radius: 50%;
} */

</style>
