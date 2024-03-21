<script>
import {onMount} from 'svelte';

import IconContext from 'phosphor-svelte/lib/IconContext';
import { iconProps } from "@lib/utils"

import CrosshairSimple from "phosphor-svelte/lib/CrosshairSimple";
import MapTrifold from "phosphor-svelte/lib/MapTrifold";
import CornersOut from "phosphor-svelte/lib/CornersOut";
import DotsThreeOutline from "phosphor-svelte/lib/DotsThreeOutline";
import Stack from "phosphor-svelte/lib/Stack";
import X from "phosphor-svelte/lib/X";

import sync from 'ol-hashed';

import {createEmpty} from 'ol/extent';
import {extend} from 'ol/extent';
import {transformExtent} from 'ol/proj';
import {fromLonLat} from 'ol/proj';
import {createXYZ} from 'ol/tilegrid';

import 'ol/ol.css';
import '@src/css/ol-overrides.css';
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

import {MouseWheelZoom, defaults} from 'ol/interaction';

import {makeTitilerXYZUrl, makeLayerGroupFromVolume, makeBasemaps} from '@lib/utils';
import Modal, {getModal} from '@components/base/Modal.svelte'
import Link from '@components/base/Link.svelte';
import MapboxLogoLink from "./buttons/MapboxLogoLink.svelte"

export let CONTEXT;
export let PLACE;
export let VOLUMES;

let showPanel = true;

let volumeIds = [];
let volumeLookup = {};

const tileGrid = createXYZ({
	tileSize: 512,
});

let homeExtent;
if (VOLUMES.length > 0) {
	homeExtent = createEmpty();
} else {
	homeExtent = transformExtent([-100, 30, -80, 50], "EPSG:4326", "EPSG:3857")
}

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

	if (vol.extent) {
		extend(homeExtent, transformExtent(vol.extent, "EPSG:4326", "EPSG:3857"))
	}

	// zIndex guide (not all categories are implemented):
	// 0 = basemaps
	// 100 = graphic map of volumes
	// 200 = key map
	// 300 = congested district map (200' to 1")
	// 400 = main content

	let mainGroup;

	// look for mosaics of this item, and use the one that is indicated by the volume's
	// mosaic_preference field. If neither mosaics exist, load
	// each layer individually and apply the Crop mask
	let mosaicUrl;
	let mosaicType;
	if (vol.urls.mosaic_geotiff && vol.mosaic_preference === 'geotiff') {
		mosaicUrl = vol.urls.mosaic_geotiff;
		mosaicType = "gt";
	} else if (vol.urls.mosaic_json && vol.mosaic_preference === 'mosaicjson') {
		mosaicUrl = vol.urls.mosaic_json;
		mosaicType = "mj";
	}
	if (mosaicUrl) {
		mainGroup = new TileLayer({
			source: new XYZ({
				transition: 0,
				url: makeTitilerXYZUrl({
					host: CONTEXT.titiler_host,
					url: mosaicUrl,
				}),
			}),
			extent: transformExtent(vol.extent, "EPSG:4326", "EPSG:3857")
		});
	}
	// otherwise make a group layer out of all the main layers in the volume.
	else if (vol.sorted_layers.main.length > 0) {
		// mainGroup = getMainLayerGroupFromVolume(vol);
		mainGroup = makeLayerGroupFromVolume({
			volume: vol,
			titilerHost: CONTEXT.titiler_host,
			zIndex: 400+n,
			layerSet: "main",
		})
		mainGroup.setZIndex(400+n)
	}

	let opacity = 0;
	if (urlParams.has(vol.identifier)) {
		needToShowOneLayer = false;
		opacity = urlParams.get(vol.identifier)
	}
	if (opacity == 0) {
		urlParams.delete(vol.identifier)
	} else {
		urlParams.set(vol.identifier, opacity)
	}

	const volumeObj = {
		id: vol.identifier,
		summaryUrl: vol.urls.summary,
		displayName: vol.volume_no ? `${vol.year} vol. ${vol.volume_no}` : vol.year,
		progress: vol.progress,
		mainLayer: mainGroup,
		mainLayerO: opacity,
		mosaicType: mosaicType,
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
		if (volumeLookup[id].mainLayerO == 0) {
			urlParams.delete(id)
		} else {
			urlParams.set(id,  volumeLookup[id].mainLayerO);
		}
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

const basemaps = makeBasemaps(CONTEXT.mapbox_api_token)


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
		maxTilesLoading: 32,
		pixelRatio: 2,
		view: new View({
			zoom: 8,
			center: fromLonLat([-92.036, 31.16])
		}),
		interactions: defaults({mouseWheelZoom: false}).extend([
			new MouseWheelZoom({
				constrainResolution: true,
			}),
		]),
	});

	if (homeExtent) {
		// only if there are layers to show...
		// temporarily constrain to zoom 14 so the fit won't zoom too far out.
		if (VOLUMES.length > 0) {
			map.getView().setMinZoom(14)
		}
		map.getView().fit(homeExtent)
		// set initial zoom to integer to improve tile efficiency, esp. when
		// user zooms in and out with mouse wheel or clicks/taps
		map.getView().setZoom(Math.round(map.getView().getZoom()))
		map.getView().setMinZoom(0)
	}

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

	if (CONTEXT.on_mobile){
		map.on('singleclick', function() { showPanel = !showPanel })
	}

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

function getCompletedStr(id) {
	return `${volumeLookup[id].progress.georef_ct}/${volumeLookup[id].progress.unprep_ct+volumeLookup[id].progress.prep_ct+volumeLookup[id].progress.georef_ct}`
} 

</script>
<IconContext values={iconProps}>
<Modal id='modal-about'>
	<h1>Using this Viewer</h1>
	<ul>
		<li>Use
			<i class="transparency-toggle full-circle"/> /
			<i class="transparency-toggle half-circle"/> /
			<i class="transparency-toggle empty-circle"/>, or the slider,
			to change layer opacity</li>
		<li>Share the browser URL at any time to retain current location and layer settings</li>
	</ul>
	<h2>About the Maps</h2>
	<p>These historical fire insurance maps were originally created by the Sanborn Map Company, and provided here via the <Link href="https://loc.gov/collections/sanborn-maps/about-this-collection" title="LOC Sanborn Maps Collection">Library of Congress</Link> collection.</p>
	<p>In early 2022, participants in a <Link href="https://digitalcommons.lsu.edu/gradschool_theses/5641/" external={true}>crowdsourcing project</Link> georeferenced all of the Louisiana maps you see here, eventually creating these seamless mosaic overlays. These comprise 1,500 individual sheets from 270 different Sanborn atlases, covering of over <Link href="/browse">130 different locations</Link>.</p>
	<h2>Further Development</h2>
	<p>If you are interested in supporting this site <Link href="mailto:hello@oldinsuracemaps.net">get in touch</Link>. To get more Sanborn maps on here, please fill out <Link href="https://forms.gle/3gbZPYKWcPFb1NN5A">this form</Link>.</p>
	<p>To learn much more about the entire project, head to <Link href="https://ohmg.dev">ohmg.dev</Link>.</p>
</Modal>
<main>
	<div id="locate-button" class="ol-control ol-unselectable">
		<button title="Show my location" on:click={locateUser}>
			<CrosshairSimple />
		</button>
	</div>
	<div id="map">
		{#if currentBasemap == "satellite"}
		<MapboxLogoLink />
		{/if}
	</div>
	<div id="panel-btn">
		<button class="control-btn" on:click={() => {showPanel=!showPanel}}>
			{#if showPanel}
			<X />
			{:else}
			<Stack />
			{/if}
		</button>
	</div>
	{#if showPanel}
	<div id="layer-panel" style="display:{showPanel == true ? 'flex' : 'none'}">
		<div class="control-panel-buttons">
			<button class="control-btn" title="Change basemap" on:click={toggleBasemap}><MapTrifold /></button>
			<button class="control-btn" title="{watchId ? 'Disable' : 'Show'} my location" on:click={toggleGPSLocation} style="{watchId ? 'color:blue' : ''}"><CrosshairSimple /></button>
			<button class="control-btn" title="Reset to original extent and settings" on:click={resetExtent}><CornersOut /></button>
		</div>
		<div class="control-panel-title">
			<h1>{PLACE.display_name}</h1>
		</div>
		<div class="control-panel-content">
			{#if volumeIds.length > 0}
			{#each volumeIds as id }
			<div class="volume-item">
				<div class="volume-header">
					<div>
						<button class="toggle-button" disabled={!volumeLookup[id].mainLayer} on:click={() => toggleLayerTransparencyIcon(id)}>
							<i class="{volumeLookup[id].mainLayer != undefined ? 'transparency-toggle' : ''} {getClass(volumeLookup[id].mainLayerO)}" style="{volumeLookup[id].mainLayer != undefined ? '' : 'background:grey;border-color:grey;'}"  />
							<span>{volumeLookup[id].displayName}</span>
						</button>
						<input type=range disabled={volumeLookup[id].mainLayer ? "" : "disabled"} class="transparency-slider" bind:value={volumeLookup[id].mainLayerO} on:mouseup={syncUrlParams} min=0 max=100>
					</div>
					<div>
						<button style="" on:click={() => toggleDetails(id)}><DotsThreeOutline /></button>
					</div>
				</div>
				<div id="{id}" class="volume-detail">
					<div>
						<span title="{getCompletedStr(id)} georeferenced">
							{volumeLookup[id].progress.percent}&percnt; ({getCompletedStr(id)})
						</span>
						{#if volumeLookup[id].mosaicType}
						<span style="color:lightgrey;" title="Mosaic stored as {volumeLookup[id].mosaicType == 'gt' ? 'GeoTIFF' : 'MosaicJSON'}">
							{volumeLookup[id].mosaicType}
						</span>
						{/if}
					</div>
					<div>
						<Link href="{volumeLookup[id].summaryUrl}" title="The full summary includes content that has not yet been georeferenced." >
							Summary &rarr;
						</Link>
					</div>
				</div>
			</div>
			{/each}
			{:else}
			<div class="volume-item">
				<p>No volumes for this place. <Link href="/browse" title="Back to browse">Back to browse &rarr;</Link></p>
			</div>
			{/if}
		</div>
		<div class="control-panel-footer">
			<Link title="Find another city" href="/browse" classes={["white"]}>&larr; switch city</Link>
			<span>|</span>
			<Link title="Go to home page" href="/" classes={["white"]}>home</Link>
			<span>|</span>
			<button title="About this viewer" on:click={() => {getModal('modal-about').open()}}>info</button>
		</div>
	</div>
	{/if}
</main>
</IconContext>

<style>
main {
	display: flex;
}
h1, h2 {
	font-size: 1.4em;
	margin-top: 10px;
	margin-bottom: 10px;
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
	align-items: left;
}

#locate-button {
  top: 4em;
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
	height: 1.5em;
	text-align: center;
	z-index: 1000;
	
}

#panel-btn > button {
	border-color:black;
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
	padding: 5px;
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

.control-panel-buttons > button {
	margin-left: 10px;
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
	justify-content: space-between;
	align-items: center;
	height: 30px;
	width: 100%;
}
.volume-detail {
	padding: 0px 5px;
}
.volume-detail > div:first-child {
	margin-right: 10px;
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

@media only screen and (max-width: 480px) {
	#layer-panel {
		top: unset;
		right: 0;
		left: 0;
		bottom: 3em;
		margin-right: auto;
		margin-left: auto;
	}
}

</style>
