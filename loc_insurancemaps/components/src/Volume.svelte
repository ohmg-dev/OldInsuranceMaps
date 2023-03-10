<script>
import { slide } from 'svelte/transition';

import TitleBar from "../../../georeference/components/src/TitleBar.svelte";
import PlaceSelect from "./PlaceSelect.svelte";
import VolumePreviewMap from "./VolumePreviewMap.svelte";

export let VOLUME;
export let OTHER_VOLUMES;
export let CSRFTOKEN;
export let USER_TYPE;
export let MAPBOX_API_KEY;
export let TITILER_HOST;

$: sheetsLoading = VOLUME.status == "initializing...";

let layersPresent = VOLUME.items.layers.length > 0;
// This variable is used to trigger a reinit of the VolumePreviewMap component.
// See https://svelte.dev/repl/65c80083b515477784d8128c3655edac?version=3.24.1
let reinitMap = [{}]
let showMap = layersPresent
let showGeoref = true;
let showUnprepared = VOLUME.status == "initializing...";
let showPrepared = false;
let showGeoreferenced = false;

let refreshingLookups = false;

let mapIndexLayerIds = []; 

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
	if (VOLUME.sorted_layers.key_map.length > 0 ) {
		let referenceLayers = [];
		VOLUME.sorted_layers.key_map.forEach( function(layer) {
			referenceLayers.push(layer.slug);
		})
		return "reference="+referenceLayers.join(",")+"&"
	} else {
		return ""
	}
}

let intervalId;
function manageAutoReload(run) {
	if (run) {
		intervalId = setInterval(postOperation, 4000, "refresh");
	} else {
		clearInterval(intervalId)
	}
}
$: autoReload = sheetsLoading || VOLUME.items.processing.unprep != 0 || VOLUME.items.processing.prep != 0 || VOLUME.items.processing.geo_trim != 0;
$: manageAutoReload(autoReload)

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
		// trigger a reinit of the VolumePreviewMap component
		if (operation == "set-index-layers" || VOLUME.items.layers.length != result.items.layers.length) {
			reinitMap = [{}];
		}
		VOLUME = result;
		sheetsLoading = VOLUME.status == "initializing...";
		if (operation == "refresh-lookups") {
			refreshingLookups = false;
		}
		if (showMap == false && VOLUME.items.layers.length > 0) {
			window.location.href = VOLUME.urls.summary;
		}
	});
}

let settingKeyMapLayer = false;

const sideLinks = [
	{
		display: "Open in main viewer",
		url: VOLUME.urls.viewer,
		external: true,
	},
	{
		display: "Open in Library of Congress",
		url: VOLUME.urls.loc_resource,
		external: true,
	}
]

</script>

<div id="vModal" class="modal">
	<button id="closeModal" class="close close-vmodal" on:click={closeModal}>&times;</button>
	<div class="modal-content" style="text-align:center;">
		<img id="modalImg" alt="" src="">
		<div id="imgCaption"><h5>~</h5></div>
	</div>
</div>
<main>
	<TitleBar TITLE={VOLUME.title} BOTTOM_LINKS={OTHER_VOLUMES} SIDE_LINKS={sideLinks} ICON_LINKS={[]}/>
	<PlaceSelect VOLUME={VOLUME} />
	{#if VOLUME.sheet_ct.loaded < VOLUME.sheet_ct.total && USER_TYPE != 'anonymous' && !sheetsLoading}
		<button on:click={() => { postOperation("initialize"); sheetsLoading = true; }}>Load Volume ({VOLUME.sheet_ct.total} sheet{#if VOLUME.sheet_ct.total != 1}s{/if})</button>
	{/if}
	<section>
		<div class="section-title-bar">
			<button class="section-toggle-btn" on:click={() => showMap = !showMap} style="">
				<h2 style="margin-right:10px">Map Overview</h2>
				<i class="header fa {showMap == true ? 'fa-angle-double-down' : 'fa-angle-double-right'}"></i>
			</button>
		</div>
		<div class="section-content" style="display:{showMap == true ? 'block' : 'none'};">
			{#each reinitMap as key (key)}
				<VolumePreviewMap VOLUME={VOLUME} MAPBOX_API_KEY={MAPBOX_API_KEY} TITILER_HOST={TITILER_HOST} />
			{/each}
		</div>
	</section>
	<section>
		<div class="section-title-bar">
			<button class="section-toggle-btn" on:click={() => showGeoref = !showGeoref} style="">
				<h2 style="margin-right:10px">Georeferencing Overview</h2>
				<i class="header fa {showGeoref == true ? 'fa-angle-double-down' : 'fa-angle-double-right'}"></i>
			</button>
		</div>
		<div class="section-content" style="display:{showGeoref == true ? 'block' : 'none'};">
			<div style="display:flex; justify-content:space-between; align-items:center;">
				<div>
					<em><span>
						{#if sheetsLoading}
						Loading sheet {VOLUME.sheet_ct.loaded+1}/{VOLUME.sheet_ct.total}... (you can safely leave this page).
						{:else if VOLUME.sheet_ct.loaded == 0}
						No sheets loaded yet...
						{:else if VOLUME.sheet_ct.loaded < VOLUME.sheet_ct.total }
						{VOLUME.sheet_ct.loaded} of {VOLUME.sheet_ct.total} sheet{#if VOLUME.sheet_ct.total != 1}s{/if} loaded (initial load unsuccessful. Click <strong>Load Volume</strong> to retry)
						{:else}
						{VOLUME.sheet_ct.loaded} of {VOLUME.sheet_ct.total} sheet{#if VOLUME.sheet_ct.total != 1}s{/if} loaded by <a href={VOLUME.loaded_by.profile}>{VOLUME.loaded_by.name}</a> - {VOLUME.loaded_by.date}
						{/if}
					</span></em>
				</div>
				<div>
					{#if refreshingLookups}
					<div class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
				{/if}
				</div>
				<div>
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
			{#if USER_TYPE == 'anonymous' }
			<div class="signin-reminder">
			<p><em>
				<!-- svelte-ignore a11y-invalid-attribute -->
				<a href="#" data-toggle="modal" data-target="#SigninModal" role="button" >sign in</a> or
				<a href="/account/signup">sign up</a> to work on this content
			</em></p>
			</div>
			{/if}
			<section class="subsection">
				<div class="subsection-title-bar">
					<button class="section-toggle-btn" on:click={() => showUnprepared = !showUnprepared} style="">
						<h3 style="margin-right:10px">
							Unprepared ({VOLUME.items.unprepared.length})
							{#if VOLUME.items.processing.unprep != 0}
								&mdash; {VOLUME.items.processing.unprep} in progress...
							{/if}
						</h3>
						<i class="subheader fa {showUnprepared == true ? 'fa-angle-double-down' : 'fa-angle-double-right'}"></i>
					</button>
				</div>
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
							<div><p><a href={document.urls.resource} title={document.title}>Sheet {document.page_str}</a></p></div>
							<img style="cursor:zoom-in" on:click={() => {showImgModal(document.urls.image, document.title)}} src={document.urls.thumbnail} alt={document.title}>
							<div>
								{#if document.lock_enabled}
								<ul style="text-align:center">
									<li><em>preparation in progress.</em></li>
									<li><em>user: {document.lock_details.user.name}</em></li>
								</ul>
								{:else}
								<ul>
									<li><a href={document.urls.split} title="Prepare this document">prepare &rarr;</a></li>
								</ul>
								{/if}
							</div>
						</div>
						{/each}
					</div>
					{/if}
				</div>
				{/if}
			</section>
			<section class="subsection">
				<div class="subsection-title-bar">
					<button class="section-toggle-btn" on:click={() => showPrepared = !showPrepared} style="">
						<h3 style="margin-right:10px">Prepared ({VOLUME.items.prepared.length})</h3>
						<i class="subheader fa {showPrepared == true ? 'fa-angle-double-down' : 'fa-angle-double-right'}"></i>
					</button>
				</div>
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
							<div><p><a href={document.urls.resource} title={document.title}>{document.title}</a></p></div>
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
								</ul>
								{/if}
							</div>
						</div>
						{/each}
					</div>
					{/if}
				</div>
				{/if}
			</section>
			<section class="subsection" style="border-bottom:none;">
				<div class="subsection-title-bar">
					<button class="section-toggle-btn" on:click={() => showGeoreferenced = !showGeoreferenced} style="">
						<h3 style="margin-right:10px">Georeferenced ({VOLUME.items.layers.length})</h3>
						<i class="subheader fa {showGeoreferenced == true ? 'fa-angle-double-down' : 'fa-angle-double-right'}"></i>
					</button>
				</div>
				{#if showGeoreferenced}
				<div transition:slide>
					<p>Georeferenced documents are represented here as layers.</p>
					{#if VOLUME.items.layers.length == 0}
					<p><em>Layers will accumulate here as documents are georeferenced.</em></p>
					{:else}
					<p><em>
						Use <strong>Set Key Map</strong> to designate which layers show the <strong>key map</strong> for this volume (if applicable).
					</em></p>
					{#if USER_TYPE != 'anonymous'}
					<div style="margin-top:10px; margin-bottom:10px;">
						{#if VOLUME.items.layers.length > 0 && !settingKeyMapLayer}
						<button on:click={() => settingKeyMapLayer = !settingKeyMapLayer}>Set Key Map</button>
						{/if}
						{#if settingKeyMapLayer}
						<button on:click={() => { settingKeyMapLayer = false; postOperation("set-index-layers"); }}>Save</button>
						<button on:click={() => { settingKeyMapLayer = false; }}>Cancel</button>
						{/if}
					</div>
					{/if}
					<div class="documents-column">
						{#each VOLUME.items.layers as layer}
						<div class="document-item">
							<div><p><a href={layer.urls.resource} title={layer.title}>{layer.title}</a></p></div>
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
									<li><a href="{layer.urls.georeference}?{referenceLayersParam()}" title="edit georeferencing">edit georeferencing &rarr;</a></li>
									<!-- link for OHM editor with this layer as basemap -->
									<!-- layers returning 400 7/14/2022, disabling for now -->
									<!-- <li><a href={layer.urls.ohm_edit} title="open in OHM editor" target="_blank">OHM &rarr;</a></li> -->
								</ul>
								{/if}
								{#if settingKeyMapLayer}
								<label>
									<input type=checkbox bind:group={mapIndexLayerIds} value={layer.slug}> Use layer in Key Map
								</label>
								{/if}
							</div>
						</div>
						{/each}
					</div>
					{/if}
				</div>
				{/if}
			</section>
		</div>
	</section>
	<section>
		<div>
		<p style="float:left;"><em>
			{VOLUME.sessions.prep_ct} sheet{#if VOLUME.sessions.prep_ct != 1}s{/if} prepared{#if VOLUME.sessions.prep_ct > 0}&nbsp;by {#each VOLUME.sessions.prep_contributors as c, n}<a href="{c.profile}">{c.name}</a> ({c.ct}){#if n != VOLUME.sessions.prep_contributors.length-1}, {/if}{/each}{/if}
		</em></p></div>
		<div><p><em>
			{VOLUME.sessions.georef_ct} georeferencing session{#if VOLUME.sessions.georef_ct != 1}s{/if}{#if VOLUME.sessions.georef_ct > 0}&nbsp;by 
			{#each VOLUME.sessions.georef_contributors as c, n}<a href="{c.profile}">{c.name}</a> ({c.ct}){#if n != VOLUME.sessions.georef_contributors.length-1}, {/if}{/each}{/if}
		</em></p></div>
	</section>
</main>

<style>

main { 
	margin-bottom: 10px;
}

section {
	border-bottom: 1px solid rgb(149, 149, 149);
}

section.subsection {
	border-bottom: 1px dashed rgb(149, 149, 149);
}

button.section-toggle-btn {
	display: flex;
	justify-content: space-between;
	align-items: baseline;
	background: none;
	border: none;
	color: #2c689c;
	padding: 0;
}
i.header {
	font-size: 1.5em;
}

button.section-toggle-btn:hover {
	color: #1b4060;
}

button.section-toggle-btn > h2 {
	font-size: 1.6em;
}

button.section-toggle-btn > h3 {
	font-size: 1.3em;
	margin-top: 15px;
}
i.subheader {
	font-size: 1.3em;
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

.section-content {
	padding-bottom: 15px;
}

hr {
	margin-top: 15px;
	margin-bottom: 15px;
}

hr.hr-dashed {
	border-top: 1px dashed rgb(149, 149, 149);
	margin: 15px 0px;
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
	.documents-column {
		flex-direction: column;
	}
}
</style>
