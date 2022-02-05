<script>
import {onMount} from 'svelte';

import 'ol/ol.css';
import Map from 'ol/Map';

import {createEmpty} from 'ol/extent';
import {extend} from 'ol/extent';
import {transformExtent} from 'ol/proj'; 

import OSM from 'ol/source/OSM';
import TileWMS from 'ol/source/TileWMS';

import TileLayer from 'ol/layer/Tile';

export let VOLUME;
export let CSRFTOKEN;
export let USER_TYPE;
export let GEOSERVER_WMS;

let sheetsLoading = VOLUME.status == "initializing...";
let loadTip = false
let indexLayers = [];
function setIndexLayerList() {
	indexLayers = [];
	let olLayers = [];

	let extent = createEmpty()
	VOLUME.index_layers.forEach( function(layer) {
		indexLayers.push(layer.alternate)
		const olLayer = new TileLayer({
			source: new TileWMS({
				url: GEOSERVER_WMS,
				params: {
					'LAYERS': layer.geoserver_id,
					'TILED': true,
				},
			})
		});
		const extent3857 = transformExtent(layer.extent, "EPSG:4326", "EPSG:3857");
		extend(extent, extent3857)
		olLayers.push(olLayer);
	});
	
	if (olLayers.length > 0) {
		const osmLayer = new TileLayer({
			source: new OSM(),
		})
		olLayers.unshift(osmLayer)
		indexMap.setTarget("index-map")
		indexMap.getView().fit(extent);
		indexMap.setLayers(olLayers)
	} else {
		indexMap.setTarget(null)
	}
}

function postOperation(operation) {
	if (operation == "set-index-layers") { settingIndexLayer = false; }
	const data = JSON.stringify({
      "operation": operation,
	  "indexLayerIds": indexLayers,
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
		// full refresh needed if an index layer is added for the first time.
		const fullRefresh = VOLUME.index_layers.length == 0;
		VOLUME = result;
		sheetsLoading = VOLUME.status == "initializing...";
		if (operation == "set-index-layers") {
			if (fullRefresh) {
				window.location.href = VOLUME.urls.summary;
			}
			setIndexLayerList();
		}
	});
}

let indexMap;
onMount(() => {
  indexMap = new Map({ target: "index-map" });
  setIndexLayerList();
});

let settingIndexLayer = false;
</script>

<main>
	<h1>{ VOLUME.title }</h1>
	<p>
		<a href={ VOLUME.urls.loc_resource } target="_blank">
			Preview in Library of Congress <i class="fa fa-external-link"></i>
		</a>
		<!-- svelte-ignore a11y-invalid-attribute -->
		&nbsp;<a href="#" on:click={() => loadTip = !loadTip}><i class="fa fa-info-circle"></i></a>
	</p>
	<p hidden={!loadTip}>&uarr; Before loading, this is the best way to see if the volume covers your part of town.</p>

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
	<hr hidden={VOLUME.index_layers.length == 0}>
	<figure style="width:75%; border: 1px solid gray;" hidden={VOLUME.index_layers.length == 0}>
		<div id="index-map" hidden={VOLUME.index_layers.length == 0}></div>
		<figcaption>
		{#if VOLUME.index_layers.length == 0}
		Find and georeference the index maps(s) for this volume to display an overview here. Typically, the index
		map is on the first sheet of a volume, though very small volumes may not have one.
		{:else}
		Use the index map above to help determine which sheet you want to work on next. This is especially helpful
		in larger cities, where you may want to find your own neighborhood.
		{/if}
		</figcaption>
	</figure>
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
		<h4>Unprepared ({VOLUME.items.unprepared.length})</h4>
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
		</h4>
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
		</h4>
		<div style="margin-top:10px; margin-bottom:10px;">
			{#if VOLUME.items.layers.length > 0}
			<button on:click={() => settingIndexLayer = !settingIndexLayer}>Set Index Layers</button>
			{/if}
			{#if settingIndexLayer}
			<button on:click={() => { settingIndexLayer = false; setIndexLayerList() }}>Cancel</button>
			<button on:click={() => { postOperation("set-index-layers") } }>Save</button>
			{/if}
		</div>
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
							<input type=checkbox bind:group={indexLayers} value={layer.alternate}> Set as index layer
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

figcaption {
	margin: 5px;
	font-style: italic;
}

#index-map {
	height: 450px;
	width: 100%;
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