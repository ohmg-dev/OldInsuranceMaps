<script>
import {onMount} from 'svelte';
import { slide } from 'svelte/transition';

import sync from 'ol-hashed';

import {createEmpty} from 'ol/extent';
import {extend} from 'ol/extent';
import {transformExtent} from 'ol/proj';
import {fromLonLat} from 'ol/proj';
import {createXYZ} from 'ol/tilegrid';

import 'ol/ol.css';
import './css/ol-overrides.css';
import Map from 'ol/Map';
import View from 'ol/View';

import Crop from 'ol-ext/filter/Crop';
import Control from 'ol/control/Control';

import GeoJSON from 'ol/format/GeoJSON';

import Feature from 'ol/Feature';
import Point from 'ol/geom/Point';
import {circular} from 'ol/geom/Polygon';

import XYZ from 'ol/source/XYZ';
import VectorSource from 'ol/source/Vector';
import TileWMS from 'ol/source/TileWMS';

import TileLayer from 'ol/layer/Tile';
import LayerGroup from 'ol/layer/Group';
import VectorLayer from 'ol/layer/Vector';

import Utils from './js/ol-utils';
const utils = new Utils();

export let PLACE;
export let MAPBOX_API_KEY;
export let VOLUMES;
export let TITILER_HOST;

let showPanel = true;
$: showHideBtnIcon = showPanel ? "✖" : "•••";

let volumeIds = [];
let volumeLookup = {};

const tileGrid = createXYZ({
	tileSize: 512,
});

let showAboutPanel = false;

let homeExtent;
const layerExtent = createEmpty();

// set variable to hold id for Geolocation.watchPosition()
let watchId;
let justEnabled = false;

// set some url variables that need to persist.
let originalUrl = window.location.href;
function paramsFromUrl (url) {
	let urlWithoutHash = url.split('#')[0];
	let paramString = urlWithoutHash.split('?')[1];
	return new URLSearchParams(paramString);
}
function hashFromUrl (url) {
	return url.split('#')[1];
}
function baseFromUrl(url) {
	let urlWithoutHash = url.split('#')[0];
	return urlWithoutHash.split('?')[0];
}
let currentHash = hashFromUrl(originalUrl);
let urlParams = paramsFromUrl(originalUrl);
let baseUrl = baseFromUrl(originalUrl);

let needToShowOneLayer = true;
VOLUMES.forEach( function (vol, n) {

	// zIndex guide (not all categories are implemented):
	// 0 = basemaps
	// 100 = graphic map of volumes
	// 200 = key map
	// 300 = congested district map (200' to 1")
	// 400 = main content

	let mainGroup;

	// if there is a mosaic JSON url for the volume, use that to make the layer
	if (vol.urls.mosaic) {
		mainGroup = new TileLayer({
			source: new XYZ({
				url: utils.makeTitilerXYZUrl(TITILER_HOST, vol.urls.mosaic),
			}),
			extent: transformExtent(vol.extent, "EPSG:4326", "EPSG:3857")
		});
		homeExtent = transformExtent(vol.extent, "EPSG:4326", "EPSG:3857");;
	} 
        // otherwise make a group layer out of all the main layers in the volume.
        else if (vol.sorted_layers.main.length > 0) {
		mainGroup = getMainLayerGroupFromVolume(vol);
		mainGroup.setZIndex(400+n)
	}

	let opacity = 0;
	if (urlParams.has(vol.identifier)) {
		needToShowOneLayer = false;
		opacity = urlParams.get(vol.identifier)
	}
	urlParams.set(vol.identifier, opacity)

	const volumeObj = {
		id: vol.identifier,
		summaryUrl: vol.urls.summary,
		displayName: vol.volume_no ? `${vol.year} vol. ${vol.volume_no}` : vol.year,
		mainLayer: mainGroup,
		mainLayerO: opacity,
	};
	volumeIds.push(vol.identifier);
	volumeLookup[vol.identifier] = volumeObj;

	
})

// if the params didn't have opacity settings for any layer, then set the latest
// layer to 100. In the case of New Orleans, set all layers to 100 (this is
// because all the current layers are really on edition, unlike every other
// city where each layer is a different year)
if (needToShowOneLayer) {
	volumeIds.forEach( function (id) {
		if (volumeLookup[id].mainLayer != undefined && needToShowOneLayer == true) {
			urlParams.set(id, 100);
			volumeLookup[id].mainLayerO = 100;
			needToShowOneLayer = false;
		} else if (originalUrl.indexOf("new-orleans-la") > 0) {
			urlParams.set(id, 100);
			volumeLookup[id].mainLayerO = 100;
		}
	});
}

// this takes care of situations in which only the bare viewer url is originally called,
// so the opacity params must be pushed to the url string
window.history.replaceState(null, "", baseUrl+"?"+urlParams.toString() + "#" + currentHash);
// now reset the originalUrl after all params have been pushed into it.
originalUrl = window.location.href;


function getClass(n) {
	if (n == 100) {
		return "full-circle"
	} else if (n == 0) {
		return "empty-circle"
	} else {
		return "half-circle"
	}
}
function toggleTransparencyIcon(inTrans) {
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
function toggleLayerTransparencyIcon(id) {
	if (volumeLookup[id].mainLayer) {
		volumeLookup[id].mainLayerO = toggleTransparencyIcon(volumeLookup[id].mainLayerO)
	}
	syncUrlParams()
}

function setVisibility(group, vis) {
	if (vis == 0) {
		group.setVisible(false)
	} else {
		group.setVisible(true)
		group.setOpacity(vis/100)
	}
}
// $: setVisibility(layerId, kGV)

function changes(volumeLookup) {
	volumeIds.forEach( function (id) {
		if (volumeLookup[id].mainLayer) {
			setVisibility(volumeLookup[id].mainLayer, volumeLookup[id].mainLayerO)
		}
	})
}
$: changes(volumeLookup)

function syncUrlParams () {
	currentHash = window.location.href.split("#")[1]
	volumeIds.forEach( function (id) {
		urlParams.set(id,  volumeLookup[id].mainLayerO);
		window.history.replaceState(null, "", baseUrl+"?"+urlParams.toString() + "#" + currentHash)
			// window.history.replaceState(null, "", window.location.href)
	});
}
function setOpacitiesFromParams() {
	urlParams = paramsFromUrl(window.location.href);
	volumeIds.forEach( function (id) {
		if (urlParams.has(id)) {
			volumeLookup[id].mainLayerO = urlParams.get(id)
		}
	});
}

// setup all the basemap stuff

const basemaps = utils.makeBasemaps(MAPBOX_API_KEY)


const baseGroup = new LayerGroup({
	zIndex: 0,
	layers: [
		basemaps[0].layer,
		basemaps[1].layer
	]
});

let currentBasemap = basemaps[1].id;
basemaps[0].layer.setVisible(false)
function toggleBasemap() {
	basemaps.forEach( function (layerItem) {
		layerItem.layer.setVisible(!layerItem.layer.getVisible())
		if (layerItem.layer.getVisible()) { currentBasemap = layerItem.id}
	});
}

// GENERATE THE MOSAIC LAYERS FOR EACH VOLUME

function getMainLayerGroupFromVolume(volumeJson) {
	// this is pulled from the Volume Summary construction, and should be
	// significantly refactored...

	const lyrGroup = new LayerGroup();

	volumeJson.sorted_layers.main.forEach( function(layerDef) {

		const extent3857 = transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857");
		extend(layerExtent, extent3857)
		homeExtent = layerExtent;

		// create the actual ol layers and add to group.
		const newLayer = new TileLayer({
			source: new XYZ({
				url: utils.makeTitilerXYZUrl(TITILER_HOST, layerDef.urls.cog),
			}),
			extent: transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857")
		});
		lyrGroup.getLayers().push(newLayer)

		if (volumeJson.multimask) {
			Object.entries(volumeJson.multimask).forEach(kV => {
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
	return lyrGroup
}

// GEOLOCATION MANAGEMENT
const gpsSource = new VectorSource();
const gpsLayer = new VectorLayer({
	source: gpsSource,
	zIndex: 500,
});

function toggleGPSLocation() {
	if (watchId) {
		disableGPSLocation();
	} else {
		enableGPSLocation();
	}
}
function enableGPSLocation() {
	justEnabled = true;
	watchId = navigator.geolocation.watchPosition(
		function (pos) {
			const coords = [pos.coords.longitude, pos.coords.latitude];
			const accuracy = circular(coords, pos.coords.accuracy);
			gpsSource.clear(true);
			gpsSource.addFeatures([
				new Feature(
					accuracy.transform('EPSG:4326', mapView.map.getView().getProjection())
				),
				new Feature(new Point(fromLonLat(coords))),
			]);
			if (justEnabled) { locateUser(); justEnabled = false;}
		},
		function (error) {
			alert(`ERROR: ${error.message}`);
		},
		{
			enableHighAccuracy: true,
		}
	);
}

function disableGPSLocation() {
	navigator.geolocation.clearWatch(watchId);
	gpsSource.clear(true);
	watchId = undefined;
}

function locateUser() {
	if (!watchId) {
		enableGPSLocation();
	} else if (!gpsSource.isEmpty() && mapView.map) {
		mapView.map.getView().fit(gpsSource.getExtent(), {
		maxZoom: 18,
		duration: 500,
		});
	}
}

function resetExtent() {
	mapView.map.getView().fit(homeExtent);
	window.history.replaceState(null, "", originalUrl);
	setOpacitiesFromParams();
}

let mapView;
function MapViewer (elementId) {

	const targetElement = document.getElementById(elementId);

	// create map
	const map = new Map({
		target: targetElement,
		layers: [baseGroup],
		maxTilesLoading: 50,
                pixelRatio: 2,
		view: new View({
			zoom: 8,
			minZoom: 14,
			center: fromLonLat([-92.036, 31.16])
		})
	});

	if (homeExtent) {map.getView().fit(homeExtent)}

	volumeIds.forEach(function (vol) {
		if (volumeLookup[vol].mainLayer) {
			map.addLayer(volumeLookup[vol].mainLayer)
		}
	})

	map.addLayer(gpsLayer);

	map.addControl(
		new Control({
			element: document.getElementById("locate-button"),
		})
	);

	sync(map);
	this.map = map;
}

onMount(() => {
  mapView = new MapViewer("map");
});

function toggleDetails(id) {
	const el = document.getElementById(id);
	el.style.display = el.style.display ? "" : "flex";
}


</script>
{#if showAboutPanel}
<div class="about-modal-bg">
	<div class="about-modal-content">
		<h1>About</h1>
		<p>These historical fire insurance maps were originally created by the <a href="">Sanborn Map Company</a>, and the maps used here come from the Library of Congress <a title="LOC Sanborn Maps Collection" href="https://loc.gov/collections/sanborn-maps/about-this-collection">digital collection</a>.</p>
		<p>In early 2022, participants in a crowdsourcing pilot project georeferenced all of the Louisiana maps you see here, eventually creating these seamless mosaic overlays. Over four months, 1,500 individual sheets from 270 different Sanborn atlases were processed, covering of over 130 different locations. You can find other cities in the <a href="/browse">main search page</a>.</p>
		<p>If you or your organization are interested in getting Sanborn maps of your home on this site so they can be georeferenced, please fill out <a href="https://forms.gle/3gbZPYKWcPFb1NN5A">this form</a>, or just <a href="mailto:hello@oldinsuracemaps.net">get in touch</a>.</p>
		<p>To learn more more about the entire project, head to <a href="https://about.oldinsurancemaps.net">about.oldinsurancemaps.net</a>.</p>
		<button on:click={() => {showAboutPanel=false}}>close</button>
	</div>
</div>
{/if}
<main>
	<div id="locate-button" class="ol-control ol-unselectable">
		<button title="Show my location" on:click={locateUser}><i class="fa fa-crosshairs"></i></button>
	</div>
	<div id="map">
		{#if currentBasemap == "satellite"}
		<a href="http://mapbox.com/about/maps" class='mapbox-logo' target="_blank">Mapbox</a>
		{/if}
	</div>
	<div id="panel-btn">
		<button on:click={() => {showPanel=!showPanel}} style="{showPanel ? 'border-color:#333; color:#333;' : ''};">
			<span>{showHideBtnIcon}</span>
		</button>
	</div>
	{#if showPanel}
	<div id="layer-panel" style="display:{showPanel == true ? 'flex' : 'none'}">
		<div class="control-panel-buttons">
			<button title="Change basemap" on:click={toggleBasemap}><i class="fa fa-exchange" /></button>
			<button title="{watchId ? 'Disable' : 'Show'} my location" on:click={toggleGPSLocation} style="color:{watchId ? 'blue' : 'black'}"><i class="fa fa-crosshairs" /></button>
			<button title="Reset to original extent and settings" on:click={resetExtent}><i class="fa fa-refresh" /></button>
		</div>
		<div class="control-panel-title">
			<h1>{PLACE.display_name}</h1>
		</div>
		<div class="control-panel-content">
			{#if volumeIds.length > 0}
			{#each volumeIds as id }
			<div class="volume-item">
				<div class="volume-header">
					<button class="toggle-button" disabled={!volumeLookup[id].mainLayer} on:click={() => toggleLayerTransparencyIcon(id)}>
						<i class="{volumeLookup[id].mainLayer != undefined ? 'transparency-toggle' : ''} {getClass(volumeLookup[id].mainLayerO)}" style="{volumeLookup[id].mainLayer != undefined ? '' : 'background:grey;border-color:grey;'}"  />
						<span>{volumeLookup[id].displayName}</span>
					</button>
					<button style="" on:click={() => toggleDetails(id)}>•••</button>
					<input type=range disabled={volumeLookup[id].mainLayer ? "" : "disabled"} class="transparency-slider" bind:value={volumeLookup[id].mainLayerO} on:mouseup={syncUrlParams} min=0 max=100>
				</div>
				<div id="{id}" class="volume-detail">
					<a href="{volumeLookup[id].summaryUrl}">Go to full summary &rarr;</a>
				</div>
			</div>
			{/each}
			{:else}
			<div class="volume-item">
				<p>No volumes for this place. <a title="Back to browse" href="/browse">Back to browse &rarr;</a></p>
			</div>
			{/if}
		</div>
		<div class="control-panel-footer">
			<a title="Find another city" href="/browse">&larr; back to browse</a>
			<span>|</span>
			<a title="Go to home page" href="/">home</a>
			<span>|</span>
			<button title="About this viewer" on:click={() => {showAboutPanel = !showAboutPanel}}>about</button>
		</div>
	</div>
	{/if}
</main>
<style>
main {
	display: flex;
}
h1 {
	font-size: 1.5em;
}

.about-modal-bg {
	position: absolute;
	background: rgba(255, 255, 255, .6);
	z-index: 999999;
	height: 100vh;
	width: 100%;
}
.about-modal-content {
	position: absolute;
	background: white;
	border-radius: 4px;
	top: 3em;
	right: 0;
	left: 0;
	margin: auto;
	width: 400px;
	max-width: 80%;
	padding: 10px;
	display: flex;
	flex-direction: column;
	align-items: center;
}

#locate-button {
  top: 6em;
  left: .5em;
}

#map {
	height: 100vh;
	width: 100%;
	position: absolute;
}

#panel-btn {
	position: absolute;
	top: .5em;
	right: .5em;
	width: 50px;
	height: 1.5em;
	text-align: center;
	z-index: 1000;
	
}

#panel-btn button {
	display: inline-flex;
  	align-items: center;
	justify-content: center;
	color: #666666;
	background: lightgrey;
	border-radius: 4px;
	border: 1px solid #333333;
	cursor: pointer;
	width: 50px;
	font-size: 1.2em;
}

#panel-btn button:hover {
	color: #333333;
}

#layer-panel {
	display: flex;
	flex-direction: column;
	align-items: center;
	color: #333333;
	position: absolute;
	top: .5em;
	right: .5em;
	max-width: 100%;
	min-width: 250px;
	background: #F7F1E1;
	border-radius: 4px;
	border: 1px solid #333333;
	z-index: 999;
}

.toggle-button {
	display: inline-flex;
	align-items: center;
	align-content: center;
}

.btn-spacer {
	width: 41px;
}

.control-panel-title {
	padding: 10px;
}
.control-panel-title h1 {
	margin: 0;
}
.control-panel-buttons {
	display: flex;
	justify-content: start;
	padding-right: 50px;
	width: 100%;
}

.control-panel-content {
	display: flex;
	flex-direction: column;
	max-height: 500px;
	overflow-y: auto;
	width: 100%;
}
.control-panel-footer {
	text-align: center;
	height: 30px;
	width: 100%;
	padding: 5px;
	background-color: #123b4f;
	color: white;
}
.control-panel-footer a {
	color: white;
}
.control-panel-footer button {
	color: white;
	border: none;
	background: none;
	padding: 0;
}
.control-panel-footer button:hover {
	text-decoration: underline;
}

.volume-item {
	display: flex;
	flex-direction: column;
	border-top: 1px dashed grey;
	padding: 3px 10px;
}

.volume-header, .volume-detail {
	display: flex;
	flex-direction: row;
	justify-content: space-around;
	align-items: center;
	height: 30px;
	width: 100%;
}

.volume-header button {
	background: none;
	border: none;
	color: #1b4060;
	font-weight: 600;
	padding-top: 2px;
}

.volume-header button:hover {
	text-decoration: underline;
	color: #1b4060;
}
.volume-header button:disabled {
	text-decoration: none;
	color: grey;
}
.volume-header button i {
	margin-right: 4px;
}

.volume-detail {
	margin-top: 5px;
	display: none;
}

.transparency-slider {
	display: inline;
	width: 150px;
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

.mapbox-logo {
  position: absolute;
  display: block;
  height: 20px;
  width: 65px;
  left: 10px;
  bottom: 10px;
  text-indent: -9999px;
  z-index: 99999;
  overflow: hidden;

  /* `background-image` contains the Mapbox logo */
  background-image: url(data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz48c3ZnIHZlcnNpb249IjEuMSIgaWQ9IkxheWVyXzEiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgeG1sbnM6eGxpbms9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkveGxpbmsiIHg9IjBweCIgeT0iMHB4IiB2aWV3Qm94PSIwIDAgODAuNDcgMjAuMDIiIHN0eWxlPSJlbmFibGUtYmFja2dyb3VuZDpuZXcgMCAwIDgwLjQ3IDIwLjAyOyIgeG1sOnNwYWNlPSJwcmVzZXJ2ZSI+PHN0eWxlIHR5cGU9InRleHQvY3NzIj4uc3Qwe29wYWNpdHk6MC42O2ZpbGw6I0ZGRkZGRjtlbmFibGUtYmFja2dyb3VuZDpuZXcgICAgO30uc3Qxe29wYWNpdHk6MC42O2VuYWJsZS1iYWNrZ3JvdW5kOm5ldyAgICA7fTwvc3R5bGU+PGc+PHBhdGggY2xhc3M9InN0MCIgZD0iTTc5LjI5LDEzLjYxYzAsMC4xMS0wLjA5LDAuMi0wLjIsMC4yaC0xLjUzYy0wLjEyLDAtMC4yMy0wLjA2LTAuMjktMC4xNmwtMS4zNy0yLjI4bC0xLjM3LDIuMjhjLTAuMDYsMC4xLTAuMTcsMC4xNi0wLjI5LDAuMTZoLTEuNTNjLTAuMDQsMC0wLjA4LTAuMDEtMC4xMS0wLjAzYy0wLjA5LTAuMDYtMC4xMi0wLjE4LTAuMDYtMC4yN2MwLDAsMCwwLDAsMGwyLjMxLTMuNWwtMi4yOC0zLjQ3Yy0wLjAyLTAuMDMtMC4wMy0wLjA3LTAuMDMtMC4xMWMwLTAuMTEsMC4wOS0wLjIsMC4yLTAuMmgxLjUzYzAuMTIsMCwwLjIzLDAuMDYsMC4yOSwwLjE2bDEuMzQsMi4yNWwxLjMzLTIuMjRjMC4wNi0wLjEsMC4xNy0wLjE2LDAuMjktMC4xNmgxLjUzYzAuMDQsMCwwLjA4LDAuMDEsMC4xMSwwLjAzYzAuMDksMC4wNiwwLjEyLDAuMTgsMC4wNiwwLjI3YzAsMCwwLDAsMCwwTDc2Ljk2LDEwbDIuMzEsMy41Qzc5LjI4LDEzLjUzLDc5LjI5LDEzLjU3LDc5LjI5LDEzLjYxeiIvPjxwYXRoIGNsYXNzPSJzdDAiIGQ9Ik02My4wOSw5LjE2Yy0wLjM3LTEuNzktMS44Ny0zLjEyLTMuNjYtMy4xMmMtMC45OCwwLTEuOTMsMC40LTIuNiwxLjEyVjMuMzdjMC0wLjEyLTAuMS0wLjIyLTAuMjItMC4yMmgtMS4zM2MtMC4xMiwwLTAuMjIsMC4xLTAuMjIsMC4yMnYxMC4yMWMwLDAuMTIsMC4xLDAuMjIsMC4yMiwwLjIyaDEuMzNjMC4xMiwwLDAuMjItMC4xLDAuMjItMC4yMnYtMC43YzAuNjgsMC43MSwxLjYyLDEuMTIsMi42LDEuMTJjMS43OSwwLDMuMjktMS4zNCwzLjY2LTMuMTNDNjMuMjEsMTAuMyw2My4yMSw5LjcyLDYzLjA5LDkuMTZMNjMuMDksOS4xNnogTTU5LjEyLDEyLjQxYy0xLjI2LDAtMi4yOC0xLjA2LTIuMy0yLjM2VjkuOTljMC4wMi0xLjMxLDEuMDQtMi4zNiwyLjMtMi4zNnMyLjMsMS4wNywyLjMsMi4zOVM2MC4zOSwxMi40MSw1OS4xMiwxMi40MXoiLz48cGF0aCBjbGFzcz0ic3QwIiBkPSJNNjguMjYsNi4wNGMtMS44OS0wLjAxLTMuNTQsMS4yOS0zLjk2LDMuMTNjLTAuMTIsMC41Ni0wLjEyLDEuMTMsMCwxLjY5YzAuNDIsMS44NSwyLjA3LDMuMTYsMy45NywzLjE0YzIuMjQsMCw0LjA2LTEuNzgsNC4wNi0zLjk5UzcwLjUxLDYuMDQsNjguMjYsNi4wNHogTTY4LjI0LDEyLjQyYy0xLjI3LDAtMi4zLTEuMDctMi4zLTIuMzlzMS4wMy0yLjQsMi4zLTIuNHMyLjMsMS4wNywyLjMsMi4zOVM2OS41MSwxMi40MSw2OC4yNCwxMi40Mkw2OC4yNCwxMi40MnoiLz48cGF0aCBjbGFzcz0ic3QxIiBkPSJNNTkuMTIsNy42M2MtMS4yNiwwLTIuMjgsMS4wNi0yLjMsMi4zNnYwLjA2YzAuMDIsMS4zMSwxLjA0LDIuMzYsMi4zLDIuMzZzMi4zLTEuMDcsMi4zLTIuMzlTNjAuMzksNy42Myw1OS4xMiw3LjYzeiBNNTkuMTIsMTEuMjNjLTAuNiwwLTEuMDktMC41My0xLjExLTEuMTlWMTBjMC4wMS0wLjY2LDAuNTEtMS4xOSwxLjExLTEuMTlzMS4xMSwwLjU0LDEuMTEsMS4yMVM1OS43NCwxMS4yMyw1OS4xMiwxMS4yM3oiLz48cGF0aCBjbGFzcz0ic3QxIiBkPSJNNjguMjQsNy42M2MtMS4yNywwLTIuMywxLjA3LTIuMywyLjM5czEuMDMsMi4zOSwyLjMsMi4zOXMyLjMtMS4wNywyLjMtMi4zOVM2OS41MSw3LjYzLDY4LjI0LDcuNjN6IE02OC4yNCwxMS4yM2MtMC42MSwwLTEuMTEtMC41NC0xLjExLTEuMjFzMC41LTEuMiwxLjExLTEuMnMxLjExLDAuNTQsMS4xMSwxLjIxUzY4Ljg1LDExLjIzLDY4LjI0LDExLjIzeiIvPjxwYXRoIGNsYXNzPSJzdDAiIGQ9Ik00My41Niw2LjI0aC0xLjMzYy0wLjEyLDAtMC4yMiwwLjEtMC4yMiwwLjIydjAuN2MtMC42OC0wLjcxLTEuNjItMS4xMi0yLjYtMS4xMmMtMi4wNywwLTMuNzUsMS43OC0zLjc1LDMuOTlzMS42OSwzLjk5LDMuNzUsMy45OWMwLjk5LDAsMS45My0wLjQxLDIuNi0xLjEzdjAuN2MwLDAuMTIsMC4xLDAuMjIsMC4yMiwwLjIyaDEuMzNjMC4xMiwwLDAuMjItMC4xLDAuMjItMC4yMlY2LjQ0YzAtMC4xMS0wLjA5LTAuMjEtMC4yMS0wLjIxQzQzLjU3LDYuMjQsNDMuNTcsNi4yNCw0My41Niw2LjI0eiBNNDIuMDIsMTAuMDVjLTAuMDEsMS4zMS0xLjA0LDIuMzYtMi4zLDIuMzZzLTIuMy0xLjA3LTIuMy0yLjM5czEuMDMtMi40LDIuMjktMi40YzEuMjcsMCwyLjI4LDEuMDYsMi4zLDIuMzZMNDIuMDIsMTAuMDV6Ii8+PHBhdGggY2xhc3M9InN0MSIgZD0iTTM5LjcyLDcuNjNjLTEuMjcsMC0yLjMsMS4wNy0yLjMsMi4zOXMxLjAzLDIuMzksMi4zLDIuMzlzMi4yOC0xLjA2LDIuMy0yLjM2VjkuOTlDNDIsOC42OCw0MC45OCw3LjYzLDM5LjcyLDcuNjN6IE0zOC42MiwxMC4wMmMwLTAuNjcsMC41LTEuMjEsMS4xMS0xLjIxYzAuNjEsMCwxLjA5LDAuNTMsMS4xMSwxLjE5djAuMDRjLTAuMDEsMC42NS0wLjUsMS4xOC0xLjExLDEuMThTMzguNjIsMTAuNjgsMzguNjIsMTAuMDJ6Ii8+PHBhdGggY2xhc3M9InN0MCIgZD0iTTQ5LjkxLDYuMDRjLTAuOTgsMC0xLjkzLDAuNC0yLjYsMS4xMlY2LjQ1YzAtMC4xMi0wLjEtMC4yMi0wLjIyLTAuMjJoLTEuMzNjLTAuMTIsMC0wLjIyLDAuMS0wLjIyLDAuMjJ2MTAuMjFjMCwwLjEyLDAuMSwwLjIyLDAuMjIsMC4yMmgxLjMzYzAuMTIsMCwwLjIyLTAuMSwwLjIyLTAuMjJ2LTMuNzhjMC42OCwwLjcxLDEuNjIsMS4xMiwyLjYxLDEuMTJjMi4wNywwLDMuNzUtMS43OCwzLjc1LTMuOTlTNTEuOTgsNi4wNCw0OS45MSw2LjA0eiBNNDkuNiwxMi40MmMtMS4yNiwwLTIuMjgtMS4wNi0yLjMtMi4zNlY5Ljk5YzAuMDItMS4zMSwxLjA0LTIuMzcsMi4yOS0yLjM3YzEuMjYsMCwyLjMsMS4wNywyLjMsMi4zOVM1MC44NiwxMi40MSw0OS42LDEyLjQyTDQ5LjYsMTIuNDJ6Ii8+PHBhdGggY2xhc3M9InN0MSIgZD0iTTQ5LjYsNy42M2MtMS4yNiwwLTIuMjgsMS4wNi0yLjMsMi4zNnYwLjA2YzAuMDIsMS4zMSwxLjA0LDIuMzYsMi4zLDIuMzZzMi4zLTEuMDcsMi4zLTIuMzlTNTAuODYsNy42Myw0OS42LDcuNjN6IE00OS42LDExLjIzYy0wLjYsMC0xLjA5LTAuNTMtMS4xMS0xLjE5VjEwQzQ4LjUsOS4zNCw0OSw4LjgxLDQ5LjYsOC44MWMwLjYsMCwxLjExLDAuNTUsMS4xMSwxLjIxUzUwLjIxLDExLjIzLDQ5LjYsMTEuMjN6Ii8+PHBhdGggY2xhc3M9InN0MCIgZD0iTTM0LjM2LDEzLjU5YzAsMC4xMi0wLjEsMC4yMi0wLjIyLDAuMjJoLTEuMzRjLTAuMTIsMC0wLjIyLTAuMS0wLjIyLTAuMjJWOS4yNGMwLTAuOTMtMC43LTEuNjMtMS41NC0xLjYzYy0wLjc2LDAtMS4zOSwwLjY3LTEuNTEsMS41NGwwLjAxLDQuNDRjMCwwLjEyLTAuMSwwLjIyLTAuMjIsMC4yMmgtMS4zNGMtMC4xMiwwLTAuMjItMC4xLTAuMjItMC4yMlY5LjI0YzAtMC45My0wLjctMS42My0xLjU0LTEuNjNjLTAuODEsMC0xLjQ3LDAuNzUtMS41MiwxLjcxdjQuMjdjMCwwLjEyLTAuMSwwLjIyLTAuMjIsMC4yMmgtMS4zM2MtMC4xMiwwLTAuMjItMC4xLTAuMjItMC4yMlY2LjQ0YzAuMDEtMC4xMiwwLjEtMC4yMSwwLjIyLTAuMjFoMS4zM2MwLjEyLDAsMC4yMSwwLjEsMC4yMiwwLjIxdjAuNjNjMC40OC0wLjY1LDEuMjQtMS4wNCwyLjA2LTEuMDVoMC4wM2MxLjA0LDAsMS45OSwwLjU3LDIuNDgsMS40OGMwLjQzLTAuOSwxLjMzLTEuNDgsMi4zMi0xLjQ5YzEuNTQsMCwyLjc5LDEuMTksMi43NiwyLjY1TDM0LjM2LDEzLjU5eiIvPjxwYXRoIGNsYXNzPSJzdDEiIGQ9Ik04MC4zMiwxMi45N2wtMC4wNy0wLjEyTDc4LjM4LDEwbDEuODUtMi44MWMwLjQyLTAuNjQsMC4yNS0xLjQ5LTAuMzktMS45MmMtMC4wMS0wLjAxLTAuMDItMC4wMS0wLjAzLTAuMDJjLTAuMjItMC4xNC0wLjQ4LTAuMjEtMC43NC0wLjIxaC0xLjUzYy0wLjUzLDAtMS4wMywwLjI4LTEuMywwLjc0bC0wLjMyLDAuNTNsLTAuMzItMC41M2MtMC4yOC0wLjQ2LTAuNzctMC43NC0xLjMxLTAuNzRoLTEuNTNjLTAuNTcsMC0xLjA4LDAuMzUtMS4yOSwwLjg4Yy0yLjA5LTEuNTgtNS4wMy0xLjQtNi45MSwwLjQzYy0wLjMzLDAuMzItMC42MiwwLjY5LTAuODUsMS4wOWMtMC44NS0xLjU1LTIuNDUtMi42LTQuMjgtMi42Yy0wLjQ4LDAtMC45NiwwLjA3LTEuNDEsMC4yMlYzLjM3YzAtMC43OC0wLjYzLTEuNDEtMS40LTEuNDFoLTEuMzNjLTAuNzcsMC0xLjQsMC42My0xLjQsMS40djMuNTdjLTAuOS0xLjMtMi4zOC0yLjA4LTMuOTctMi4wOWMtMC43LDAtMS4zOSwwLjE1LTIuMDIsMC40NWMtMC4yMy0wLjE2LTAuNTEtMC4yNS0wLjgtMC4yNWgtMS4zM2MtMC40MywwLTAuODMsMC4yLTEuMSwwLjUzYy0wLjAyLTAuMDMtMC4wNC0wLjA1LTAuMDctMC4wOGMtMC4yNy0wLjI5LTAuNjUtMC40NS0xLjA0LTAuNDVoLTEuMzJjLTAuMjksMC0wLjU3LDAuMDktMC44LDAuMjVDNDAuOCw1LDQwLjEyLDQuODUsMzkuNDIsNC44NWMtMS43NCwwLTMuMjcsMC45NS00LjE2LDIuMzhjLTAuMTktMC40NC0wLjQ2LTAuODUtMC43OS0xLjE5Yy0wLjc2LTAuNzctMS44LTEuMTktMi44OC0xLjE5aC0wLjAxYy0wLjg1LDAuMDEtMS42NywwLjMxLTIuMzQsMC44NGMtMC43LTAuNTQtMS41Ni0wLjg0LTIuNDUtMC44NGgtMC4wM2MtMC4yOCwwLTAuNTUsMC4wMy0wLjgyLDAuMWMtMC4yNywwLjA2LTAuNTMsMC4xNS0wLjc4LDAuMjdjLTAuMi0wLjExLTAuNDMtMC4xNy0wLjY3LTAuMTdoLTEuMzNjLTAuNzgsMC0xLjQsMC42My0xLjQsMS40djcuMTRjMCwwLjc4LDAuNjMsMS40LDEuNCwxLjRoMS4zM2MwLjc4LDAsMS40MS0wLjYzLDEuNDEtMS40MWMwLDAsMCwwLDAsMFY5LjM1YzAuMDMtMC4zNCwwLjIyLTAuNTYsMC4zNC0wLjU2YzAuMTcsMCwwLjM2LDAuMTcsMC4zNiwwLjQ1djQuMzVjMCwwLjc4LDAuNjMsMS40LDEuNCwxLjRoMS4zNGMwLjc4LDAsMS40LTAuNjMsMS40LTEuNGwtMC4wMS00LjM1YzAuMDYtMC4zLDAuMjQtMC40NSwwLjMzLTAuNDVjMC4xNywwLDAuMzYsMC4xNywwLjM2LDAuNDV2NC4zNWMwLDAuNzgsMC42MywxLjQsMS40LDEuNGgxLjM0YzAuNzgsMCwxLjQtMC42MywxLjQtMS40di0wLjM2YzAuOTEsMS4yMywyLjM0LDEuOTYsMy44NywxLjk2YzAuNywwLDEuMzktMC4xNSwyLjAyLTAuNDVjMC4yMywwLjE2LDAuNTEsMC4yNSwwLjgsMC4yNWgxLjMyYzAuMjksMCwwLjU3LTAuMDksMC44LTAuMjV2MS45MWMwLDAuNzgsMC42MywxLjQsMS40LDEuNGgxLjMzYzAuNzgsMCwxLjQtMC42MywxLjQtMS40di0xLjY5YzAuNDYsMC4xNCwwLjk0LDAuMjIsMS40MiwwLjIxYzEuNjIsMCwzLjA3LTAuODMsMy45Ny0yLjF2MC41YzAsMC43OCwwLjYzLDEuNCwxLjQsMS40aDEuMzNjMC4yOSwwLDAuNTctMC4wOSwwLjgtMC4yNWMwLjYzLDAuMywxLjMyLDAuNDUsMi4wMiwwLjQ1YzEuODMsMCwzLjQzLTEuMDUsNC4yOC0yLjZjMS40NywyLjUyLDQuNzEsMy4zNiw3LjIyLDEuODljMC4xNy0wLjEsMC4zNC0wLjIxLDAuNS0wLjM0YzAuMjEsMC41MiwwLjcyLDAuODcsMS4yOSwwLjg2aDEuNTNjMC41MywwLDEuMDMtMC4yOCwxLjMtMC43NGwwLjM1LTAuNThsMC4zNSwwLjU4YzAuMjgsMC40NiwwLjc3LDAuNzQsMS4zMSwwLjc0aDEuNTJjMC43NywwLDEuMzktMC42MywxLjM4LTEuMzlDODAuNDcsMTMuMzgsODAuNDIsMTMuMTcsODAuMzIsMTIuOTdMODAuMzIsMTIuOTd6IE0zNC4xNSwxMy44MWgtMS4zNGMtMC4xMiwwLTAuMjItMC4xLTAuMjItMC4yMlY5LjI0YzAtMC45My0wLjctMS42My0xLjU0LTEuNjNjLTAuNzYsMC0xLjM5LDAuNjctMS41MSwxLjU0bDAuMDEsNC40NGMwLDAuMTItMC4xLDAuMjItMC4yMiwwLjIyaC0xLjM0Yy0wLjEyLDAtMC4yMi0wLjEtMC4yMi0wLjIyVjkuMjRjMC0wLjkzLTAuNy0xLjYzLTEuNTQtMS42M2MtMC44MSwwLTEuNDcsMC43NS0xLjUyLDEuNzF2NC4yN2MwLDAuMTItMC4xLDAuMjItMC4yMiwwLjIyaC0xLjMzYy0wLjEyLDAtMC4yMi0wLjEtMC4yMi0wLjIyVjYuNDRjMC4wMS0wLjEyLDAuMS0wLjIxLDAuMjItMC4yMWgxLjMzYzAuMTIsMCwwLjIxLDAuMSwwLjIyLDAuMjF2MC42M2MwLjQ4LTAuNjUsMS4yNC0xLjA0LDIuMDYtMS4wNWgwLjAzYzEuMDQsMCwxLjk5LDAuNTcsMi40OCwxLjQ4YzAuNDMtMC45LDEuMzMtMS40OCwyLjMyLTEuNDljMS41NCwwLDIuNzksMS4xOSwyLjc2LDIuNjVsMC4wMSw0LjkxQzM0LjM3LDEzLjcsMzQuMjcsMTMuOCwzNC4xNSwxMy44MUMzNC4xNSwxMy44MSwzNC4xNSwxMy44MSwzNC4xNSwxMy44MXogTTQzLjc4LDEzLjU5YzAsMC4xMi0wLjEsMC4yMi0wLjIyLDAuMjJoLTEuMzNjLTAuMTIsMC0wLjIyLTAuMS0wLjIyLTAuMjJ2LTAuNzFDNDEuMzQsMTMuNiw0MC40LDE0LDM5LjQyLDE0Yy0yLjA3LDAtMy43NS0xLjc4LTMuNzUtMy45OXMxLjY5LTMuOTksMy43NS0zLjk5YzAuOTgsMCwxLjkyLDAuNDEsMi42LDEuMTJ2LTAuN2MwLTAuMTIsMC4xLTAuMjIsMC4yMi0wLjIyaDEuMzNjMC4xMS0wLjAxLDAuMjEsMC4wOCwwLjIyLDAuMmMwLDAuMDEsMCwwLjAxLDAsMC4wMlYxMy41OXogTTQ5LjkxLDE0Yy0wLjk4LDAtMS45Mi0wLjQxLTIuNi0xLjEydjMuNzhjMCwwLjEyLTAuMSwwLjIyLTAuMjIsMC4yMmgtMS4zM2MtMC4xMiwwLTAuMjItMC4xLTAuMjItMC4yMlY2LjQ1YzAtMC4xMiwwLjEtMC4yMSwwLjIyLTAuMjFoMS4zM2MwLjEyLDAsMC4yMiwwLjEsMC4yMiwwLjIydjAuN2MwLjY4LTAuNzIsMS42Mi0xLjEyLDIuNi0xLjEyYzIuMDcsMCwzLjc1LDEuNzcsMy43NSwzLjk4UzUxLjk4LDE0LDQ5LjkxLDE0eiBNNjMuMDksMTAuODdDNjIuNzIsMTIuNjUsNjEuMjIsMTQsNTkuNDMsMTRjLTAuOTgsMC0xLjkyLTAuNDEtMi42LTEuMTJ2MC43YzAsMC4xMi0wLjEsMC4yMi0wLjIyLDAuMjJoLTEuMzNjLTAuMTIsMC0wLjIyLTAuMS0wLjIyLTAuMjJWMy4zN2MwLTAuMTIsMC4xLTAuMjIsMC4yMi0wLjIyaDEuMzNjMC4xMiwwLDAuMjIsMC4xLDAuMjIsMC4yMnYzLjc4YzAuNjgtMC43MSwxLjYyLTEuMTIsMi42LTEuMTFjMS43OSwwLDMuMjksMS4zMywzLjY2LDMuMTJDNjMuMjEsOS43Myw2My4yMSwxMC4zMSw2My4wOSwxMC44N0w2My4wOSwxMC44N0w2My4wOSwxMC44N3ogTTY4LjI2LDE0LjAxYy0xLjksMC4wMS0zLjU1LTEuMjktMy45Ny0zLjE0Yy0wLjEyLTAuNTYtMC4xMi0xLjEzLDAtMS42OWMwLjQyLTEuODUsMi4wNy0zLjE1LDMuOTctMy4xNGMyLjI1LDAsNC4wNiwxLjc4LDQuMDYsMy45OVM3MC41LDE0LjAxLDY4LjI2LDE0LjAxTDY4LjI2LDE0LjAxeiBNNzkuMDksMTMuODFoLTEuNTNjLTAuMTIsMC0wLjIzLTAuMDYtMC4yOS0wLjE2bC0xLjM3LTIuMjhsLTEuMzcsMi4yOGMtMC4wNiwwLjEtMC4xNywwLjE2LTAuMjksMC4xNmgtMS41M2MtMC4wNCwwLTAuMDgtMC4wMS0wLjExLTAuMDNjLTAuMDktMC4wNi0wLjEyLTAuMTgtMC4wNi0wLjI3YzAsMCwwLDAsMCwwbDIuMzEtMy41bC0yLjI4LTMuNDdjLTAuMDItMC4wMy0wLjAzLTAuMDctMC4wMy0wLjExYzAtMC4xMSwwLjA5LTAuMiwwLjItMC4yaDEuNTNjMC4xMiwwLDAuMjMsMC4wNiwwLjI5LDAuMTZsMS4zNCwyLjI1bDEuMzQtMi4yNWMwLjA2LTAuMSwwLjE3LTAuMTYsMC4yOS0wLjE2aDEuNTNjMC4wNCwwLDAuMDgsMC4wMSwwLjExLDAuMDNjMC4wOSwwLjA2LDAuMTIsMC4xOCwwLjA2LDAuMjdjMCwwLDAsMCwwLDBMNzYuOTYsMTBsMi4zMSwzLjVjMC4wMiwwLjAzLDAuMDMsMC4wNywwLjAzLDAuMTFDNzkuMjksMTMuNzIsNzkuMiwxMy44MSw3OS4wOSwxMy44MUM3OS4wOSwxMy44MSw3OS4wOSwxMy44MSw3OS4wOSwxMy44MUw3OS4wOSwxMy44MXoiLz48cGF0aCBjbGFzcz0ic3QwIiBkPSJNMTAsMS4yMWMtNC44NywwLTguODEsMy45NS04LjgxLDguODFzMy45NSw4LjgxLDguODEsOC44MXM4LjgxLTMuOTUsOC44MS04LjgxQzE4LjgxLDUuMTUsMTQuODcsMS4yMSwxMCwxLjIxeiBNMTQuMTgsMTIuMTljLTEuODQsMS44NC00LjU1LDIuMi02LjM4LDIuMmMtMC42NywwLTEuMzQtMC4wNS0yLTAuMTVjMCwwLTAuOTctNS4zNywyLjA0LTguMzljMC43OS0wLjc5LDEuODYtMS4yMiwyLjk4LTEuMjJjMS4yMSwwLDIuMzcsMC40OSwzLjIzLDEuMzVDMTUuOCw3LjczLDE1Ljg1LDEwLjUsMTQuMTgsMTIuMTl6Ii8+PHBhdGggY2xhc3M9InN0MSIgZD0iTTEwLDAuMDJjLTUuNTIsMC0xMCw0LjQ4LTEwLDEwczQuNDgsMTAsMTAsMTBzMTAtNC40OCwxMC0xMEMxOS45OSw0LjUsMTUuNTIsMC4wMiwxMCwwLjAyeiBNMTAsMTguODNjLTQuODcsMC04LjgxLTMuOTUtOC44MS04LjgxUzUuMTMsMS4yLDEwLDEuMnM4LjgxLDMuOTUsOC44MSw4LjgxQzE4LjgxLDE0Ljg5LDE0Ljg3LDE4LjgzLDEwLDE4LjgzeiIvPjxwYXRoIGNsYXNzPSJzdDEiIGQ9Ik0xNC4wNCw1Ljk4Yy0xLjc1LTEuNzUtNC41My0xLjgxLTYuMi0wLjE0QzQuODMsOC44Niw1LjgsMTQuMjMsNS44LDE0LjIzczUuMzcsMC45Nyw4LjM5LTIuMDRDMTUuODUsMTAuNSwxNS44LDcuNzMsMTQuMDQsNS45OHogTTExLjg4LDkuODdsLTAuODcsMS43OGwtMC44Ni0xLjc4TDguMzgsOS4wMWwxLjc3LTAuODZsMC44Ni0xLjc4bDAuODcsMS43OGwxLjc3LDAuODZMMTEuODgsOS44N3oiLz48cG9seWdvbiBjbGFzcz0ic3QwIiBwb2ludHM9IjEzLjY1LDkuMDEgMTEuODgsOS44NyAxMS4wMSwxMS42NSAxMC4xNSw5Ljg3IDguMzgsOS4wMSAxMC4xNSw4LjE1IDExLjAxLDYuMzcgMTEuODgsOC4xNSAiLz48L2c+PC9zdmc+);
  background-repeat: no-repeat;
  background-position: 0 0;
  background-size: 65px 20px;
}

@media only screen and (max-width: 480px) {
	#layer-panel {
		top: unset;
		right: 0;
		left: 0;
		bottom: 3em;
		margin-right: auto;
		margin-left: auto;
	}
	#panel-btn {
		top: unset;
		right: 0;
		left: 0;
		bottom: 1em;
		margin-right: auto;
		margin-left: auto;
	}
}

</style>
