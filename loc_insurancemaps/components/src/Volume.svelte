<script>
import {onMount} from 'svelte';
import { slide } from 'svelte/transition';

import DragDrop from 'svelte-dragdroplist';

import 'ol/ol.css';
import Map from 'ol/Map';
import ZoomToExtent from 'ol/control/ZoomToExtent';
import {FullScreen, defaults as defaultControls} from 'ol/control';

import LayerGroup from 'ol/layer/Group';

import {createEmpty} from 'ol/extent';
import {extend} from 'ol/extent';
import {transformExtent} from 'ol/proj';

import OSM from 'ol/source/OSM';
import XYZ from 'ol/source/XYZ';
import TileWMS from 'ol/source/TileWMS';

import TileLayer from 'ol/layer/Tile';

export let VOLUME;
export let CSRFTOKEN;
export let USER_TYPE;
export let GEOSERVER_WMS;
export let MAPBOX_API_KEY;

$: sheetsLoading = VOLUME.status == "initializing...";
let loadTip = false;

let map;
let layersPresent = VOLUME.ordered_layers.layers.length != 0 || VOLUME.ordered_layers.index_layers.length != 0;
let showMap = layersPresent
let showUnprepared = false;
let showPrepared = false;
let showGeoreferenced = false;

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

let layerRegistry = {}

let showLayerConfig = false;
let showLayerList = true;

let orderableLayers = [];
let orderableIndexLayers = [];
let mapIndexLayerIds = [];

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
		// controls:  defaultControls().extend([new FullScreen(), new ZoomToExtent()]),
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
}

$: {
	if (showMap && map == undefined) {
		setTimeout(function() {
			initMap();
			setLayersFromVolume(true);
		}, 100);
	} else {
		cancelLayerConfig();
	}
}

function setMapExtent() {
	if (map) {
		if (layersPresent) {
			const fullExtent = createEmpty();
			VOLUME.ordered_layers.layers.forEach( function(layerDef) {
				const extent3857 = transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857");
				extend(fullExtent, extent3857)
			});
			VOLUME.ordered_layers.index_layers.forEach( function(layerDef) {
				const extent3857 = transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857");
				extend(fullExtent, extent3857)
			});
			map.getView().fit(fullExtent);
		} else {
			map.getView().setCenter([0,0]);
			map.getView().setZoom(1)
		}
	}
}

function setLayersFromVolume(setExtent) {
	// empty the light layers lists used for interactivity, need to be repopulated
	orderableLayers = [];
	orderableIndexLayers = [];
	mapIndexLayerIds = [];

	mainGroup.getLayers().clear();
	keyGroup.getLayers().clear();

	VOLUME.ordered_layers.layers.forEach( function(layerDef, n) {
		// push to the lightweight list used for the draggable layer list
		const pName = layerDef.title.slice(layerDef.title.lastIndexOf('|')+6, layerDef.title.length)
		orderableLayers.push({
			id: layerDef.alternate,
			html: "<span style='color:black;'>"+pName + "</span>"
		})

		// create the actual ol layers and add to group.
		const newLayer = new TileLayer({
			source: new TileWMS({
				url: GEOSERVER_WMS,
				params: {
					'LAYERS': layerDef.geoserver_id,
					'TILED': true,
				},
			})
		});
		layerRegistry[layerDef.geoserver_id] = newLayer;
		mainGroup.getLayers().push(newLayer)
	});

	VOLUME.ordered_layers.index_layers.forEach( function(layerDef, n) {
		const pName = layerDef.title.slice(layerDef.title.lastIndexOf('|')+6, layerDef.title.length)
		mapIndexLayerIds.push(layerDef.alternate)
		orderableIndexLayers.push({
			id: layerDef.alternate,
			html: "<span style='color:black;'>"+pName + "</span>"
		})

		// create the actual ol layers and add to group.
		const newLayer = new TileLayer({
			source: new TileWMS({
				url: GEOSERVER_WMS,
				params: {
					'LAYERS': layerDef.geoserver_id,
					'TILED': true,
				},
			}),
		});
		layerRegistry[layerDef.geoserver_id] = newLayer;
		keyGroup.getLayers().push(newLayer)
	});

	if (setExtent) { setMapExtent() };
}

function setLayerOrder(newOrder, topZ) {
	if (!map) {return}
	newOrder.forEach( function(layerLt, n) {
		const newZ = topZ-n
		layerRegistry[layerLt.id].setZIndex(newZ);
	})
}
$: setLayerOrder(orderableLayers, 500)
$: setLayerOrder(orderableIndexLayers, 50)


function postOperation(operation) {
	let layerIds = [];
	let indexLayerIds = [];
	if (operation == "set-index-layers") {
		indexLayerIds = mapIndexLayerIds
	} else if (operation == "set-layer-order") {
		orderableLayers.forEach( function(l) { layerIds.push(l.id)});
		orderableIndexLayers.forEach( function(l) { indexLayerIds.push(l.id)});
	}
	const data = JSON.stringify({
		"operation": operation,
		"layerIds": layerIds,
		"indexLayerIds": indexLayerIds,
	});
	fetch(VOLUME.urls.summary, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json;charset=utf-8',
			'X-CSRFToken': CSRFTOKEN,
		},
		body: data,
	})
	.then(response => response.json())
	.then(result => {
		VOLUME = result;
		sheetsLoading = VOLUME.status == "initializing...";
		setLayersFromVolume();
		if (showMap == false && (VOLUME.ordered_layers.layers.length != 0 || VOLUME.ordered_layers.layers.length != 0)) {
			window.location.href = VOLUME.urls.summary;
		}
	});
}

function saveLayerConfig() {
	showLayerConfig = false;
	postOperation("set-layer-order");
}
function cancelLayerConfig() {
	showLayerConfig = false;
	setLayersFromVolume();
}

let settingIndexLayer = false;

function toggleFullscreen () {
  if (document.fullscreenElement == null) {
    let promise = document.getElementsByClassName('map-container')[0].requestFullscreen();
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
<main>
	<h1>{ VOLUME.title }</h1>
	<p>
		<a href={ VOLUME.urls.loc_resource } target="_blank">
			Preview in Library of Congress <i class="fa fa-external-link"></i>
		</a>
		<i class="fa fa-info-circle help-icon" on:click={() => loadTip = !loadTip}></i>
	</p>
	{#if loadTip}
	<div transition:slide>
		<p>&uarr; Before loading, this is the best way to see if the volume covers your part of town.</p>
	</div>
	{/if}
	{#if VOLUME.sheet_ct.loaded == 0 && USER_TYPE != 'anonymous' && !sheetsLoading}
		<button on:click={() => { postOperation("initialize") }}>Load Volume ({VOLUME.sheet_ct.total} sheet{#if VOLUME.sheet_ct.total != 1}s{/if})</button>
	{/if}

	{#if USER_TYPE == 'anonymous' }
	<div class="signin-reminder">
	<p><em>
		<!-- svelte-ignore a11y-invalid-attribute -->
		<a href="#" data-toggle="modal" data-target="#SigninModal" role="button" >sign in</a> or
		<a href="/account/signup">sign up</a> to work on this content
	</em></p>
	</div>
	{/if}

	<hr>
	<h3>Map Overview</h3>
	<div class="sheets-status-bar">
		<p><em>The preview map shows progress toward a full mosaic of this volume's content.</em></p>
	</div>
	<h4 class="section-toggle" on:click={() => showMap = !showMap}>
		<i class="fa {showMap == true ? 'fa-chevron-down' : 'fa-chevron-right'}" ></i>
		Preview Map ({VOLUME.items.layers.length} layers)
	</h4>
	<div class="map-container" style="display:{showMap == true ? 'flex' : 'none'}; justify-content: center; height:550px">
		<div id="map-panel">
			<div id="map" style="height: 100%;"></div>
		</div>
		<div id="layer-panel" style="display: {showLayerList == true ? 'flex' : 'none'}">
			<div class="layer-section-header" style="border-top-width: 1px;">
				<button class="control-btn" title="Reset extent" on:click={setMapExtent}>
					<i id="fs-icon" class="fa fa-refresh" />
				</button>
				<button class="control-btn" title={fullscreenBtnTitle} on:click={toggleFullscreen}>
					<i id="fs-icon" class="fa {fullscreenBtnIcon}" />
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
					{#if VOLUME.ordered_layers.index_layers.length == 0}
					<em>no layers set for key map</em>
					{:else}
					<input type=range bind:value={kGV} min=0 max=100>
					{/if}
				</div>
				{#if showLayerConfig && orderableIndexLayers.length > 0}
				<div class="layer-section-content">
					<DragDrop bind:data={orderableIndexLayers}/>
				</div>
				{/if}

				<div class="layer-section-header">
					<span>Layers</span>
					<i class="transparency-toggle {getClass(mGV)}" on:click={() => {mGV = toggleTransparency(mGV)}}></i>
				</div>
				<div class="layer-section-subheader">
					{#if VOLUME.ordered_layers.layers.length == 0}
					<em>no layers</em>
					{:else}
					<input type=range bind:value={mGV} min=0 max=100>
					{/if}
				</div>
				{#if showLayerConfig && orderableLayers.length > 0}
				<div class="layer-section-content">
					<DragDrop bind:data={orderableLayers}/>
				</div>
				{/if}
			</div>
			{#if USER_TYPE != 'anonymous'}
			<nav>
				<div>
					{#if showLayerConfig}
					<button on:click={saveLayerConfig}>Save</button>
					<button on:click={cancelLayerConfig}>Cancel</button>
					{:else}
					<button on:click={() => showLayerConfig = true} disabled={!layersPresent}>Arrange Layers</button>
					{/if}
				</div>
			</nav>
			{/if}
		</div>
	</div>
	<hr>
	<h3 style="">
		Georeferencing Overview
		<button id="refresh-button" title="refresh overview" on:click={() => { postOperation("refresh") }}>
			<i class="fa fa-refresh" />
		</button>
	</h3>
	<div class="sheets-status-bar">
		{#if VOLUME.loaded_by.name != "" && !sheetsLoading}
			<p><em>{VOLUME.sheet_ct.loaded}/{VOLUME.sheet_ct.total} sheet{#if VOLUME.sheet_ct.loaded != 1}s{/if} loaded by <a href={VOLUME.loaded_by.profile}>{VOLUME.loaded_by.name}</a> - {VOLUME.loaded_by.date}</em></p>
		{:else if sheetsLoading}
			<p style="float:left;"><em>{VOLUME.sheet_ct.loaded}/{VOLUME.sheet_ct.total} sheet{#if VOLUME.sheet_ct.loaded != 1}s{/if} loaded... refresh to update (you can safely leave this page).</em></p>
			<div class='lds-ellipsis' style="float:right;"><div></div><div></div><div></div><div></div></div>
		{:else if VOLUME.sheet_ct.loaded == 0}
			<p><em>No sheets loaded yet...</em></p>
		{/if}
	</div>
	<div class="documents-box">
		<h4 class="section-toggle" on:click={() => showUnprepared = !showUnprepared}>
			<i class="fa {showUnprepared == true ? 'fa-chevron-down' : 'fa-chevron-right'}" ></i>
			Unprepared ({VOLUME.items.unprepared.length})
		</h4>
		{#if showUnprepared}
		<div transition:slide>
			<p>Unprepared sheets need to be evaluated, and, if they contain more than one mapped area, split into separate pieces.</p>
			{#if VOLUME.items.unprepared.length == 0}
				<p><em>
				{#if VOLUME.sheet_ct.loaded == 0} <!-- this means they have been loaded already -->
				Sheets will appear here as they are loaded.
				{:else}
				All sheets have been prepared.
				{/if}
				</em></p>
			{:else}
			<p><em>Choose a sheet and click <strong>prepare &rarr;</strong> to start the process.</em></p>
			<div class="documents-column">
				{#each VOLUME.items.unprepared as document}
				<div class="document-item">
					<div><p>sheet {document.page_str}</p></div>
					<img src={document.urls.thumbnail} alt={document.title}>
					<div>
						<ul>
							<li><a href={document.urls.split} title="prepare this document">prepare &rarr;</a></li>
							<li><a href={document.urls.detail} title={document.title}>document detail &rarr;</a></li>
						</ul>
					</div>
				</div>
				{/each}
			</div>
			{/if}
		</div>
		{/if}
		<hr class="hr-dashed">
		<h4 class="section-toggle" on:click={() => showPrepared = !showPrepared}>
			<i class="fa {showPrepared == true ? 'fa-chevron-down' : 'fa-chevron-right'}" ></i>
			Prepared ({VOLUME.items.prepared.length})
			{#if VOLUME.items.splitting.length > 0}
				&mdash; {VOLUME.items.splitting.length} processing...
			{/if}
		</h4>
		{#if showPrepared}
		<div transition:slide>
			<p>Once a sheet has been prepared it is ready to be georeferenced.</p>
			{#if VOLUME.items.prepared.length == 0}
				<p><em>Documents will accumulate here when they are ready to be georeferenced.</em></p>
			{:else}
			<p><em>Choose a document and click <strong>georeference &rarr;</strong> to start the process.</em></p>
			<div class="documents-column">
				{#each VOLUME.items.prepared as document}
				<div class="document-item">
					<div><p>{document.title}</p></div>
					<img src={document.urls.thumbnail} alt={document.title}>
					<div>
						<ul>
							<li><a href={document.urls.georeference} title="georeference this document">georeference &rarr;</a></li>
							<li><a href={document.urls.detail} title={document.title}>document detail &rarr;</a></li>
						</ul>
					</div>
				</div>
				{/each}
			</div>
			{/if}
		</div>
		{/if}
		<hr class="hr-dashed">
		<h4 class="section-toggle" on:click={() => showGeoreferenced = !showGeoreferenced}>
			<i class="fa {showGeoreferenced == true ? 'fa-chevron-down' : 'fa-chevron-right'}" ></i>
			Georeferenced ({VOLUME.items.layers.length})
			{#if VOLUME.items.georeferencing.length > 0}
				&mdash; {VOLUME.items.georeferencing.length} processing...
			{/if}
		</h4>
		{#if showGeoreferenced}
		<div transition:slide>
			<p>Georeferenced documents are represented here as layers.</p>
			{#if VOLUME.items.layers.length == 0}
			<p><em>Layers will accumulate here as documents are georeferenced.</em></p>
			{:else}
			<p><em>
				Click <strong>trim &rarr;</strong> to add a mask polygon and trim the edges of a layer.<br>
				Click <strong>Set Index Layers</strong> to designate which layers show the <strong>key map</strong> for this volume (if applicable).
			</em></p>
			{#if USER_TYPE != 'anonymous'}
			<div style="margin-top:10px; margin-bottom:10px;">
				{#if VOLUME.items.layers.length > 0}
				<button on:click={() => settingIndexLayer = !settingIndexLayer}>Set Index Layers</button>
				{/if}
				{#if settingIndexLayer}
				<button on:click={() => { settingIndexLayer = false; postOperation("set-index-layers"); }}>Save</button>
				<button on:click={() => { settingIndexLayer = false; setLayersFromVolume(); }}>Cancel</button>
				{/if}
			</div>
			{/if}
			<div class="documents-column">
				{#each VOLUME.items.layers as layer}
				<div class="document-item">
					<div><p>{layer.title}</p></div>
					<img src={layer.urls.thumbnail} alt={document.title}>
					<div>
						<ul>
							<li><a href={layer.urls.trim} title="trim this layer">trim &rarr;</a></li>
							<li><a href={layer.urls.detail} title={layer.title}>layer detail &rarr;</a></li>
						</ul>
						{#if settingIndexLayer}
						<label>
							<input type=checkbox bind:group={mapIndexLayerIds} value={layer.alternate}> Set as index layer
						</label>
						{/if}
					</div>
				</div>
				{/each}
			</div>
			{/if}
		</div>
		{/if}
		<hr class="hr-dashed">
	</div>
</main>

<style>

main { 
	margin-bottom: 10px;
}

nav {
	display: flex;
	justify-content: center;
	background: rgb(235, 235, 235);
	padding: 5px;
}

h4.section-toggle {
	cursor: pointer;
	color: #2c689c;
}
h4.section-toggle:hover {
	color: #1b4060;
}
h4.section-toggle > i {
	font-size: .75em
}

i.help-icon {
	cursor: pointer;
	color: #2c689c;
}
i.help-icon:hover {
	color: #1b4060;
}

hr.hr-dashed {
	border-top: 1px dashed rgb(149, 149, 149);
	margin: 15px 0px;
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
}

.layer-section-header {
	display: flex;
	justify-content: space-between;
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

.sheets-status-bar p {
	margin: 0px;
}

.documents-column {
	display: flex;
	flex-direction: row;
	flex-wrap: wrap;
	gap: 20px;
	padding-bottom: 15px;
}

.documents-column p {
	margin: 0px;
}

.document-item {
	display: flex;
	flex-direction: column;
	justify-content: space-between;
	border: 1px solid gray;
	background: white;

}

.document-item img {
	margin: 15px;
	max-height: 200px;
	max-width: 200px;
	object-fit: scale-down;
}

.document-item div:first-child {
	text-align: center;
}

.document-item div:first-child, .document-item div:last-child {
	padding: 10px;
	background: #e6e6e6;
	width: 100%;
}

.document-item p, .document-item ul {
	margin: 0px;
}

.document-item ul {
	list-style-type: none;
	padding: 0;
}

#refresh-button {
	float: right;
}

#refresh-button i {
	font-size: .75em;
}

@media screen and (max-width: 768px){

	main {
		max-width: none;
	}

	.documents-column {
		flex-direction: column;
	}

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
