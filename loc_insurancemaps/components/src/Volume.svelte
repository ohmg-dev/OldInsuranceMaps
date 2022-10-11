<script>
import { slide } from 'svelte/transition';

import 'ol/ol.css';
import Map from 'ol/Map';

import {createEmpty} from 'ol/extent';
import {extend} from 'ol/extent';
import {transformExtent} from 'ol/proj';
import {createXYZ} from 'ol/tilegrid';

import OSM from 'ol/source/OSM';
import XYZ from 'ol/source/XYZ';
import TileWMS from 'ol/source/TileWMS';

import Crop from 'ol-ext/filter/Crop';

import GeoJSON from 'ol/format/GeoJSON';

import TileLayer from 'ol/layer/Tile';
import LayerGroup from 'ol/layer/Group';

import Utils from './js/ol-utils';
const utils = new Utils();

export let VOLUME;
export let OTHER_VOLUMES;
export let CSRFTOKEN;
export let USER_TYPE;
export let GEOSERVER_WMS;
export let MAPBOX_API_KEY;
export let USE_TITILER;
export let TITILER_HOST;

$: sheetsLoading = VOLUME.status == "initializing...";
let previewMapTip = false;

let map;
let layersPresent = VOLUME.ordered_layers.layers.length != 0 || VOLUME.ordered_layers.index_layers.length != 0;
let showMap = layersPresent
let showUnprepared = VOLUME.status == "initializing...";
let showPrepared = false;
let showGeoreferenced = false;

let refreshingLookups = false;

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

function referenceLayersParam() {
	let referenceLayers = [];
	VOLUME.ordered_layers.index_layers.forEach( function(layer) {
		referenceLayers.push(layer.alternate)
	})
	return "reference="+referenceLayers.join(",")
}

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
};

$: {
	if (showMap && map == undefined) {
		setTimeout(function() {
			initMap();
			setLayersFromVolume(true);
		}, 100);
	}
}

function setMapExtent() {
	if (map) {
		const extent3857 = transformExtent(VOLUME.extent, "EPSG:4326", "EPSG:3857");
		map.getView().fit(extent3857);
	}
}

const tileGrid = createXYZ({
	tileSize: 512,
});

function setLayersFromVolume(setExtent) {
	// empty the light layers lists used for interactivity, need to be repopulated
	mapIndexLayerIds = [];

	mainGroup.getLayers().clear();
	keyGroup.getLayers().clear();

	VOLUME.ordered_layers.layers.forEach( function(layerDef, n) {
		// push to the lightweight list used for the draggable layer list
		const pName = layerDef.title.slice(layerDef.title.lastIndexOf('|')+6, layerDef.title.length)

		// create the actual ol layers and add to group.
		let newLayer;
		if (USE_TITILER) {
			newLayer = new TileLayer({
				source: new XYZ({
					url: utils.makeTitilerXYZUrl(TITILER_HOST, layerDef.urls.cog),
				}),
				extent: transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857")
			});
		} else {
			newLayer = new TileLayer({
				source: new TileWMS({
					url: GEOSERVER_WMS,
					params: {
						'LAYERS': layerDef.geoserver_id,
						'TILED': true,
					},
					tileGrid: tileGrid,
				}),
				extent: transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857")
			});
		}

		mainGroup.getLayers().push(newLayer)


		if (VOLUME.multimask) {		
			Object.entries(VOLUME.multimask).forEach(kV => {
				if (kV[0] == layerDef.name) {
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

	VOLUME.ordered_layers.index_layers.forEach( function(layerDef, n) {
		const pName = layerDef.title.slice(layerDef.title.lastIndexOf('|')+6, layerDef.title.length)
		mapIndexLayerIds.push(layerDef.alternate)

		// create the actual ol layers and add to group.
		let newLayer;
		if (USE_TITILER) {
			newLayer = new TileLayer({
				source: new XYZ({
					url: utils.makeTitilerXYZUrl(TITILER_HOST, layerDef.urls.cog),
				}),
				extent: transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857")
			});
		} else {
			newLayer = new TileLayer({
				source: new TileWMS({
					url: GEOSERVER_WMS,
					params: {
						'LAYERS': layerDef.geoserver_id,
						'TILED': true,
					},
					tileGrid: tileGrid,
				}),
							extent: transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857")
			});
		}

		keyGroup.getLayers().push(newLayer)
	});

	if (setExtent) { setMapExtent() };
}

let intervalId;
function manageAutoReload(run) {
	if (run) {
		intervalId = setInterval(postOperation, 4000, "refresh");
	} else {
		clearInterval(intervalId)
	}
}
$: manageAutoReload(sheetsLoading)

function postOperation(operation) {
	let indexLayerIds = [];
	if (operation == "set-index-layers") {
		indexLayerIds = mapIndexLayerIds
	} else if (operation == "refresh-lookups") {
		refreshingLookups = true;
	}
	const data = JSON.stringify({
		"operation": operation,
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
		let resetExtent = false
		if (operation == "refresh-lookups") {
			resetExtent = true;
			refreshingLookups = false;
		}
		setLayersFromVolume(resetExtent);
		if (showMap == false && (VOLUME.ordered_layers.layers.length != 0 || VOLUME.ordered_layers.layers.length != 0)) {
			window.location.href = VOLUME.urls.summary;
		}
	});
}

let settingKeyMapLayer = false;

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

<div id="vModal" class="modal">
	<button id="closeModal" class="close close-vmodal" on:click={closeModal}>&times;</button>
	<div class="modal-content" style="text-align:center;">
		<img id="modalImg" alt="" src="">
		<div id="imgCaption"><h5>~</h5></div>
	</div>
</div>
<main>
	<div class="title-section">
		<div>
			<h1 style="margin: 10px 0px;">{ VOLUME.title }</h1>
			{#if OTHER_VOLUMES.length > 1}
			<p>Jump to &rarr;
			{#each OTHER_VOLUMES as ov, n}
				{#if n != 0}&nbsp;&bullet;&nbsp;{/if}
				{#if ov.url}<a href={ov.url} title={ov.name}>{ov.year}</a>{:else}{ov.year}{/if}
			{/each}
			</p>
			{/if}
		</div>
		<div class="link-box">
			<a href="{VOLUME.urls.viewer}">Show in Viewer</a>
			<a href={ VOLUME.urls.loc_resource } target="_blank">
				Show in Library of Congress <i class="fa fa-external-link"></i>
			</a>
		</div>
	</div>
	{#if VOLUME.sheet_ct.loaded < VOLUME.sheet_ct.total && USER_TYPE != 'anonymous' && !sheetsLoading}
		<button on:click={() => { postOperation("initialize"); sheetsLoading = true; }}>Load Volume ({VOLUME.sheet_ct.total} sheet{#if VOLUME.sheet_ct.total != 1}s{/if})</button>
	{/if}
	<hr>
	<h3>Map Overview</h3>
	<h4 class="section-toggle">
		<span on:click={() => showMap = !showMap}>
			<i class="fa {showMap == true ? 'fa-chevron-down' : 'fa-chevron-right'}" ></i>
			Preview Map ({VOLUME.items.layers.length} layers)
		</span>
		<i class="fa fa-info-circle help-icon" on:click={() => previewMapTip = !previewMapTip}></i>
	</h4>
	{#if previewMapTip}
	<div transition:slide>
		<p>The preview map shows progress toward a full mosaic of this volume's content. For a more immersive experience, view this volume in the <a href="{VOLUME.urls.viewer}">main viewer</a> where you can also compare it against other years.</p>
	</div>
	{/if}
	<div class="map-container" style="display:{showMap == true ? 'flex' : 'none'}; justify-content: center; height:550px">
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
					{#if VOLUME.ordered_layers.index_layers.length == 0}
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
					{#if VOLUME.ordered_layers.layers.length == 0}
					<em>no layers</em>
					{:else}
					<input type=range bind:value={mGV} min=0 max=100>
					{/if}
				</div>
			</div>
			<nav>
				<a href={VOLUME.urls.trim}>Trim Layers</a>
			</nav>
		</div>
	</div>
	<hr>
	<div style="display:flex; justify-content:space-between; align-items:center;">
		<h3>Georeferencing Overview</h3>
		<div>
			{#if refreshingLookups}
			<div class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
			{/if}
			<button class="control-btn" title="Refresh Summary" on:click={() => { postOperation("refresh") }}>
				<i class="fa fa-refresh" />
			</button>
			{#if USER_TYPE != "anonymous"}
			<button id="repair-button" class="control-btn" title="Repair Summary (may take a moment)" on:click={() => {postOperation("refresh-lookups")}}>
				<i class="fa fa-wrench" />
			</button>
			{/if}
		</div>
	</div>
	<div class="sheets-status-bar">
		<!-- {#if (VOLUME.loaded_by.name != "" && !sheetsLoading) || VOLUME.sheet_ct.loaded < VOLUME.sheet_ct.total }
			<p><em>{VOLUME.sheet_ct.loaded}/{VOLUME.sheet_ct.total} sheet{#if VOLUME.sheet_ct.loaded != 1}s{/if} loaded by <a href={VOLUME.loaded_by.profile}>{VOLUME.loaded_by.name}</a> - {VOLUME.loaded_by.date}</em></p>
		{:else if sheetsLoading}
			<p style="float:left;"><em>Loading sheet {VOLUME.sheet_ct.loaded+1}/{VOLUME.sheet_ct.total}... refresh to update (you can safely leave this page).</em></p>
			<div class='lds-ellipsis' style="float:right;"><div></div><div></div><div></div><div></div></div>
		{:else if VOLUME.sheet_ct.loaded == 0}
			<p><em>No sheets loaded yet...</em></p>
		{/if} -->
		<p style="float:left;"><em>

			{#if sheetsLoading}
			Loading sheet {VOLUME.sheet_ct.loaded+1}/{VOLUME.sheet_ct.total}... (you can safely leave this page).
			{:else if VOLUME.sheet_ct.loaded == 0}
			No sheets loaded yet...
			{:else if VOLUME.sheet_ct.loaded < VOLUME.sheet_ct.total }
			{VOLUME.sheet_ct.loaded} of {VOLUME.sheet_ct.total} sheet{#if VOLUME.sheet_ct.total != 1}s{/if} loaded (initial load unsuccessful. Click <strong>Load Volume</strong> to retry)
			{:else}
			{VOLUME.sheet_ct.loaded} of {VOLUME.sheet_ct.total} sheet{#if VOLUME.sheet_ct.total != 1}s{/if} loaded by <a href={VOLUME.loaded_by.profile}>{VOLUME.loaded_by.name}</a> - {VOLUME.loaded_by.date}
			{/if}
		</em></p>
		{#if sheetsLoading}
		<div class='lds-ellipsis' style="float:right;"><div></div><div></div><div></div><div></div></div>
		{/if}
		
	</div>

	{#if USER_TYPE == 'anonymous' }
	<div class="signin-reminder">
	<p><em>
		<!-- svelte-ignore a11y-invalid-attribute -->
		<a href="#" data-toggle="modal" data-target="#SigninModal" role="button" >sign in</a> or
		<a href="/account/signup">sign up</a> to work on this content
	</em></p>
	</div>
	{/if}
	<div class="documents-box">
		<h4 class="section-toggle" on:click={() => showUnprepared = !showUnprepared}>
			<i class="fa {showUnprepared == true ? 'fa-chevron-down' : 'fa-chevron-right'}" ></i>
			Unprepared ({VOLUME.items.unprepared.length})
			{#if VOLUME.items.processing.unprep != 0}
				&mdash; {VOLUME.items.processing.unprep} processing...
			{/if}
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
					<img style="cursor:zoom-in" on:click={() => {showImgModal(document.urls.image, document.title)}} src={document.urls.thumbnail} alt={document.title}>
					<div>
						{#if document.lock && document.lock.enabled}
						<ul style="text-align:center">
							<li><em>session in progress...</em></li>
							<li>{document.lock.username}</li>
						</ul>
						{:else}
						<ul>
							<li><a href={document.urls.split} title="prepare this document">prepare &rarr;</a></li>
							<li><a href={document.urls.detail} title={document.title}>document detail &rarr;</a></li>
						</ul>
						{/if}
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
			{#if VOLUME.items.processing.prep != 0}
				&mdash; {VOLUME.items.processing.prep} processing...
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
					<img style="cursor:zoom-in" on:click={() => {showImgModal(document.urls.image, document.title)}} src={document.urls.thumbnail} alt={document.title}>
					<div>
						{#if document.lock && document.lock.enabled}
						<ul style="text-align:center">
							<li><em>session in progress...</em></li>
							<li>{document.lock.username}</li>
						</ul>
						{:else}
						<ul>
							<li><a href="{document.urls.georeference}?{referenceLayersParam()}" title="georeference this document">georeference &rarr;</a></li>
							<li><a href={document.urls.detail} title={document.title}>document detail &rarr;</a></li>
						</ul>
						{/if}
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
			{#if VOLUME.items.processing.geo_trim != 0}
				&mdash; {VOLUME.items.processing.geo_trim} processing...
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
				Click <strong>Create Key Map</strong> to designate which layers show the <strong>key map</strong> for this volume (if applicable).
			</em></p>
			{#if USER_TYPE != 'anonymous'}
			<div style="margin-top:10px; margin-bottom:10px;">
				{#if VOLUME.items.layers.length > 0 && !settingKeyMapLayer}
				<button on:click={() => settingKeyMapLayer = !settingKeyMapLayer}>Create Key Map</button>
				{/if}
				{#if settingKeyMapLayer}
				<button on:click={() => { settingKeyMapLayer = false; postOperation("set-index-layers"); }}>Save</button>
				<button on:click={() => { settingKeyMapLayer = false; setLayersFromVolume(); }}>Cancel</button>
				{/if}
			</div>
			{/if}
			<div class="documents-column">
				{#each VOLUME.items.layers as layer}
				<div class="document-item">
					<div><p>{layer.title}</p></div>
					<a href={layer.urls.view} target="_blank" title="inspect layer in standalone map" style="cursor:zoom-in">
						<img src={layer.urls.thumbnail} alt={document.title}>
					</a>
					<div>
						{#if layer.lock && layer.lock.enabled}
						<ul style="text-align:center">
							<li><em>session in progress...</em></li>
							<li>{layer.lock.username}</li>
						</ul>
						{:else}
						<ul>
							<li><a href={layer.urls.trim} title="trim this layer">trim &rarr;</a></li>
							<li><a href="{layer.urls.georeference}?{referenceLayersParam()}" title="edit georeferencing">edit georeferencing &rarr;</a></li>
							<li><a href={layer.urls.detail} title={layer.title}>layer detail &rarr;</a></li>
							<!-- link for OHM editor with this layer as basemap -->
							<!-- layers returning 400 7/14/2022, disabling for now -->
							<!-- <li><a href={layer.urls.ohm_edit} title="open in OHM editor" target="_blank">OHM &rarr;</a></li> -->
						</ul>
						{/if}
						{#if settingKeyMapLayer}
						<label>
							<input type=checkbox bind:group={mapIndexLayerIds} value={layer.alternate}> Use layer in Key Map
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

@media screen and (max-width: 768px){

	main {
		max-width: none;
	}

	.documents-column, .title-section {
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

.title-section {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-top: 20px;
}

.title-section div {
	display: flex;
	flex-direction: column;
}

.title-section div.link-box {
	background: #e6e6e6;
	padding: 10px;
	margin: 10px;
	box-shadow: gray 0px 0px 5px;
	border-radius: 4px;
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
