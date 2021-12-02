<script>
import {onMount} from 'svelte';

import 'ol/ol.css';
import Map from 'ol/Map';
import View from 'ol/View';

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
	<div class="title-bar">
		<h1>{VOLUME.title}</h1>
		<p><a href={VOLUME.urls.loc} target="_blank">View item in Library of Congress <i class="fa fa-external-link"></i></a></p>
	</div>
	<hr>
	<figure>
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
	{#if USER_TYPE == 'anonymous' }
	<div class="signin-reminder">
	<p><em>
		<a href="#" data-toggle="modal" data-target="#SigninModal" role="button" >sign in</a> or
		<a href="/account/register">sign up</a> to work on this volume
	</em></p>
	</div>
	{/if}
	<h3 style="">
		Georeferencing Overview
		<button id="refresh-button" title="refresh overview" on:click={() => { postOperation("refresh") }}>
			<i class="fa fa-refresh" />
		</button>
	</h3>
	<div class="sheets-status-bar">
		{#if VOLUME.loaded_by.name != "" && !sheetsLoading}
			<p><em>sheets loaded by <a href={VOLUME.loaded_by.profile}>{VOLUME.loaded_by.name}</a></em></p>
		{/if}
		{#if VOLUME.sheet_ct.loaded == 0 && USER_TYPE != 'anonymous' && !sheetsLoading}
			<button on:click={() => { postOperation("initialize") }}>load sheets</button>
		{/if}
		{#if sheetsLoading}
			<p style="float:left;"><em>loading sheet {VOLUME.sheet_ct.loaded + 1}/{VOLUME.sheet_ct.total}...</em></p>
			<div class='lds-ellipsis' style="float:right;"><div></div><div></div><div></div><div></div></div>
		{/if}
	</div>
	<div class="documents-box">
		<h4>Unprepared ({VOLUME.items.unprepared.length})</h4>
		<div class="documents-column">
			{#each VOLUME.items.unprepared as document}
			<div class="document-item">
				<div><p>sheet {document.page_str}</p></div>
				<img src={document.urls.thumbnail} alt={document.title}>
				<div>
					<ul>
						{#if USER_TYPE != "anonymous"}
						<li><a href={document.urls.split} title="prepare this document">prepare &rarr;</a></li>
						{/if}
						<li><a href={document.urls.detail} title={document.title}>document detail &rarr;</a></li>
						<li><a href={document.urls.progress_page} title="view summary">georeferencing summary &rarr;</a></li>
					</ul>
				</div>
			</div>
			{/each}
		</div>
		<h4>
			Prepared ({VOLUME.items.prepared.length})
			{#if VOLUME.items.splitting.length > 0}
				&mdash; {VOLUME.items.splitting.length} processing...
			{/if}
		</h4>
		<div class="documents-column">
			{#each VOLUME.items.prepared as document}
			<div class="document-item">
				<div><p>sheet {document.page_str}</p></div>
				<img src={document.urls.thumbnail} alt={document.title}>
				<div>
					<ul>
						{#if USER_TYPE != "anonymous"}
						<li><a href={document.urls.georeference} title="georeference this document">georeference &rarr;</a></li>
						{/if}
						<li><a href={document.urls.detail} title={document.title}>document detail &rarr;</a></li>
						<li><a href={document.urls.progress_page} title="view summary">georeferencing summary &rarr;</a></li>
					</ul>
				</div>
			</div>
			{/each}
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
			{#each VOLUME.items.layers as layer}
			<div class="document-item">
				<div><p>sheet {layer.page_str}</p></div>
				<img src={layer.urls.thumbnail} alt={document.title}>
				<div>
					<ul>
						{#if USER_TYPE != "anonymous"}
						<li><a href={layer.urls.georeference} title="edit georeferencing">edit georeferencing &rarr;</a></li>
						<li><a href={layer.urls.trim} title="trim this layer">trim &rarr;</a></li>
						{/if}
						<li><a href={layer.urls.detail} title={layer.title}>layer detail &rarr;</a></li>
						<li><a href={layer.urls.progress_page} title="view summary">georeferencing summary &rarr;</a></li>
					</ul>
					{#if settingIndexLayer}
					<label>
						<input type=checkbox bind:group={indexLayers} value={layer.alternate}> Set as index layer
					</label>
					{/if}
				</div>
			</div>
			{/each}
		</div>
	</div>
</main>



<style>

main { 
	margin-bottom: 10px;
}

hr {
	border-top-color:rgb(149, 149, 149);
}

#index-map {
	height: 450px;
	width: 100%;
}

figcaption {
	margin: 5px;
	font-style: italic;
}

	.loc-hr {
		
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

	.signin-reminder {
		background: #e6e6e6;
		text-align: center;
		padding: 5px;
		margin: 5px;
	}

	.signin-reminder p {
		margin: 0px;
	}

	.documents-column {
		display: flex;
		flex-direction: row;
		flex-wrap: wrap;
		gap: 20px;
	}

	.document-item {
		/* padding: 20px; */
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

	h1 {
		font-size: 2.5em;
		font-weight: 100;
		text-shadow: 2px 2px 2px rgba(0, 0, 0, 0.4);
	}

	h2, h3 {
		text-shadow: 1px 1px 1px rgba(0, 0, 0, 0.4);
	}

	@media screen and (max-width: 768px){

		main {
			max-width: none;
		}

		.documents-column {
			flex-direction: column;
		}

	}

	.rotate{
    -moz-transition: all 2s linear;
    -webkit-transition: all 2s linear;
    transition: all 2s linear;
}

.rotate.down{
    -ms-transform: rotate(180deg);
    -moz-transform: rotate(180deg);
    -webkit-transform: rotate(180deg);
    transform: rotate(180deg);
}


	select {
		color: rgb(59, 57, 57);
		width: 100%;
		height: 2em;
		font-size: 1.25em;
		font-weight: 700;
	}

	select:disabled {
		color: #acacac;
	}

	/* pure css loading bar */
	/* from https://loading.io/css/ */
	.lds-ellipsis {
		display: inline-block;
		position: relative;
		width: 80px;
		height: 20px;
	}
	.lds-ellipsis div {
		position: absolute;
		top: 10px;
		width: 13px;
		height: 13px;
		border-radius: 50%;
		background: #000;
		animation-timing-function: cubic-bezier(0, 1, 1, 0);
	}
	.lds-ellipsis div:nth-child(1) {
		left: 8px;
		animation: lds-ellipsis1 0.6s infinite;
	}
	.lds-ellipsis div:nth-child(2) {
		left: 8px;
		animation: lds-ellipsis2 0.6s infinite;
	}
	.lds-ellipsis div:nth-child(3) {
		left: 32px;
		animation: lds-ellipsis2 0.6s infinite;
	}
	.lds-ellipsis div:nth-child(4) {
		left: 56px;
		animation: lds-ellipsis3 0.6s infinite;
	}
	@keyframes lds-ellipsis1 {
		0% {
			transform: scale(0);
		}
		100% {
			transform: scale(1);
		}
	}
	@keyframes lds-ellipsis3 {
		0% {
			transform: scale(1);
		}
		100% {
			transform: scale(0);
		}
		}
		@keyframes lds-ellipsis2 {
		0% {
			transform: translate(0, 0);
		}
		100% {
			transform: translate(24px, 0);
		}
	}
</style>