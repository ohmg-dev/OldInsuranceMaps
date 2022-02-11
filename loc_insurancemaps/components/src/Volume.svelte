<script>
import {onMount} from 'svelte';
import { slide } from 'svelte/transition';

import DragDrop from 'svelte-dragdroplist';

import 'ol/ol.css';
import Map from 'ol/Map';

import LayerGroup from 'ol/layer/Group';

import {createEmpty} from 'ol/extent';
import {extend} from 'ol/extent';
import {transformExtent} from 'ol/proj';

import OSM from 'ol/source/OSM';
import TileWMS from 'ol/source/TileWMS';

import TileLayer from 'ol/layer/Tile';

// import ImageLayer from 'ol/layer/Image';
// import ImageWMS from 'ol/source/ImageWMS';

export let VOLUME;
export let CSRFTOKEN;
export let USER_TYPE;
export let GEOSERVER_WMS;

$: sheetsLoading = VOLUME.status == "initializing...";
let loadTip = false;
let unpreparedTip = false;
let preparedTip = false;
let georeferencedTip = false;

let map;
let showMap = VOLUME.ordered_layers.layers.length != 0 || VOLUME.ordered_layers.index_layers.length != 0;

let showMainGroup = true;
let showIndexGroup = true;

const baseGroup = new LayerGroup({
	// zIndex: 0
});
const indexGroup = new LayerGroup({
	// zIndex: 100
});
const mainGroup = new LayerGroup({
	// zIndex: 200
});

// let indexGroup;
// let mainGroup;

let layerRegistry = {}

let showLayerConfig = false;

let orderableLayers = [];
let orderableIndexLayers = [];
let mapIndexLayerIds = [];

function initMap() {
	map = new Map({ target: "map" });
	const osmLayer = new TileLayer({
		source: new OSM(),
		zIndex: 0,
	});

	baseGroup.getLayers().push(osmLayer)

	map.addLayer(baseGroup);
	map.addLayer(indexGroup);
	map.addLayer(mainGroup);
}

$: {
	if (map) {
		indexGroup.setVisible(showIndexGroup)
		mainGroup.setVisible(showMainGroup)
	}
}

function setLayersFromVolume(setExtent) {
	// empty the light layers lists used for interactivity, need to be repopulated
	orderableLayers = [];
	orderableIndexLayers = [];
	mapIndexLayerIds = [];

	mainGroup.getLayers().clear();
	indexGroup.getLayers().clear();

	const fullExtent = createEmpty();
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
		const extent3857 = transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857");
		extend(fullExtent, extent3857)
		layerRegistry[layerDef.geoserver_id] = newLayer;
		mainGroup.getLayers().push(newLayer)
	});

	VOLUME.ordered_layers.index_layers.forEach( function(layerDef, n) {
		const pName = layerDef.title.slice(layerDef.title.lastIndexOf('|')+1, layerDef.title.length)
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
		const extent3857 = transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857");
		extend(fullExtent, extent3857)
		layerRegistry[layerDef.geoserver_id] = newLayer;
		indexGroup.getLayers().push(newLayer)
	});

	if (setExtent) { map.getView().fit(fullExtent) };
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

onMount(() => {
	if (showMap) {
		initMap();
		setLayersFromVolume(true);
	}
});

let settingIndexLayer = false;

function toggleFullscreen () {
  if (document.fullscreenElement == null) {
    let promise = document.getElementsByClassName('map-container')[0].requestFullscreen();
  } else {
	document.exitFullscreen();
  }
}

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
	{#if showMap}
	<div class="map-container" style="display:flex; justify-content: center; height:550px">
		<div transition:slide class="map-panel">
			<div id="map" style="height: 100%"></div>
			<nav>
				<button title="Enter fullscreen" on:click={toggleFullscreen}><i id="fs-icon" class="fa fa-arrows-alt" /></button>
				<div>
					<label><input type=checkbox bind:checked={showMainGroup} disabled={VOLUME.ordered_layers.layers.length == 0}> Main Layers</label>
					<label><input type=checkbox bind:checked={showIndexGroup} disabled={VOLUME.ordered_layers.index_layers.length == 0}> Index Layers</label>
				</div>
			</nav>
			<nav>
				<p>All georeferenced layers for the volume are automatically added to this map.</p>
				{#if USER_TYPE != 'anonymous'}
				<div>
					{#if showLayerConfig}
					<button on:click={() => { showLayerConfig = false; postOperation("set-layer-order"); } }>Save</button>
					<button on:click={() => { showLayerConfig = false; setLayersFromVolume() }}>Cancel</button>
					{:else}
					<button on:click={() => showLayerConfig = true}>Change Layer Order</button>
					{/if}
				</div>
				{/if}
			</nav>
		</div>
		{#if showLayerConfig}
		<div transition:slide class="layer-panel">
			<div class="layer-panel-header">Index Layers</div>
			<div class="layer-panel-content">
				{#if orderableIndexLayers.length > 0}
				<DragDrop bind:data={orderableIndexLayers}/>
				{:else}
				<em>none</em>
				{/if}
			</div>
			<div class="layer-panel-header">Main Layers</div>
			<div class="layer-panel-content">
				{#if orderableLayers.length > 0}
				<DragDrop bind:data={orderableLayers}/>
				{:else}
				<em>none</em>
				{/if}
			</div>
		</div>
		{/if}
	</div>
	{:else}
	<p><em>A preview map will be shown here once one or more sheets have been georeferenced.</em></p>
	{/if}
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
		<h4>Unprepared ({VOLUME.items.unprepared.length})
			<i class="fa fa-info-circle help-icon" on:click={() => unpreparedTip = !unpreparedTip}></i>
		</h4>
		{#if unpreparedTip}
		<div transition:slide>
			<p>Unprepared sheets need to be evaluated, and, if they contain more than one mapped area, split into separate pieces.</p>
			{#if VOLUME.items.unprepared.length != 0}
			<ul>
				<li>Choose a sheet and click <strong>prepare &rarr;</strong> to start the process.</li>
			</ul>
			{/if}
		</div>
		{/if}
		<div class="documents-column">
			{#if VOLUME.items.unprepared.length == 0}
				<p><em>
				{#if VOLUME.sheet_ct.loaded == 0} <!-- this means they have been loaded already -->
				Sheets will appear here as they are loaded.
				{:else}
				All sheets have been prepared.
				{/if}
				</em></p>
			{:else}
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
			{/if}
		</div>
		<h4>
			Prepared ({VOLUME.items.prepared.length})
			{#if VOLUME.items.splitting.length > 0}
				&mdash; {VOLUME.items.splitting.length} processing...
			{/if}
			<i class="fa fa-info-circle help-icon" on:click={() => preparedTip = !preparedTip}></i>
		</h4>
		{#if preparedTip}
		<div transition:slide>
			<p>Once a sheet has been prepared it is ready to be georeferenced.</p>
			{#if VOLUME.items.prepared.length != 0}
			<ul>
				<li>Choose a document and click <strong>georeference &rarr;</strong> to start the process.</li>
			</ul>
			{/if}
		</div>
		{/if}
		<div class="documents-column">
			{#if VOLUME.items.prepared.length == 0}
				<p><em>Documents will accumulate here when they are ready to be georeferenced.</em></p>
			{:else}
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
			{/if}
		</div>
		<h4>
			Georeferenced ({VOLUME.items.layers.length})
			{#if VOLUME.items.georeferencing.length > 0}
				&mdash; {VOLUME.items.georeferencing.length} processing...
			{/if}
			<i class="fa fa-info-circle help-icon" on:click={() => georeferencedTip = !georeferencedTip}></i>
		</h4>
		{#if georeferencedTip}
		<div transition:slide>
			<p>Georeferenced documents are represented here as layers, and will also be shown in the preview map at the top of this page. Additionally, some volumes will have <em>index layers</em> that show the entire extent of the volume.</p>
			{#if VOLUME.items.georeferenced.length != 0}
			<ul>
				<li>Click <strong>trim &rarr;</strong> to add a mask polygon and trim the edges of the layer.</li>
				<li>Click <strong>Set Index Layers</strong> to designate which layers should be treated as <em>index layers</em> in the preview map (they will be underneath the main layers).</li>
			</ul>
			{/if}
		</div>
		{/if}
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
			{#if VOLUME.items.layers.length == 0}
				<p><em>
				Layers will accumulate here as documents are georeferenced.
				</em></p>
			{:else}
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
			{/if}
		</div>
	</div>
</main>

<style>

main { 
	margin-bottom: 10px;
}

nav {
	display: flex;
	justify-content: space-between;
	background: rgb(235, 235, 235);
	padding: 5px;
}

nav p {
	margin: 0;
}

i.help-icon {
	cursor: pointer;
	color: #2c689c;
}
i.help-icon:hover {
	color: #1b4060;
}

.map-panel {
	display: flex;
	flex-direction: column;
	width: 80%;
	border: 1px solid gray;
}

.layer-panel {
	width: 20%;
	background: rgb(235, 235, 235);
	border-top: 1px solid gray;
	border-right: 1px solid gray;
	border-bottom: 1px solid gray;

}

.layer-panel-header {
	text-align: center;
	height: 20px;
	width: 100%;
	background: lightgray;
}

.layer-panel-content {
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

</style>
