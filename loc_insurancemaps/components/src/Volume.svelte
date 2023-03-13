<script>
import { slide } from 'svelte/transition';

import {getCenter} from 'ol/extent';

import TitleBar from "../../../georeference/components/src/TitleBar.svelte";
import PlaceSelect from "./PlaceSelect.svelte";
import VolumePreviewMap from "./VolumePreviewMap.svelte";

import Utils from './js/ol-utils';
const utils = new Utils();

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
let showMultimask = false;
let showDownload = true;

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

let mmLbl = "0/0";
if (VOLUME.multimask != undefined) {
	mmLbl = `${Object.keys(VOLUME.multimask).length}/${VOLUME.items.layers.length}`;
}
let mosaicUrl;
let ohmUrl;
if (VOLUME.urls.mosaic) {
	mosaicUrl = utils.makeTitilerXYZUrl(TITILER_HOST, VOLUME.urls.mosaic)

	// make the OHM url here
	const ll = getCenter(VOLUME.extent);
	ohmUrl = `https://www.openhistoricalmap.org/edit#map=15/${ll[1]}/${ll[0]}?background=custom:${mosaicUrl}`
}

let settingKeyMapLayer = false;

const sideLinks = [
	{
		display: "Open in main viewer",
		url: VOLUME.urls.viewer,
		external: true,
	},
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
			<button class="section-toggle-btn" disabled={VOLUME.items.layers.length == 0} on:click={() => showMap = !showMap} style="">
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
						<i class="subheader fa {showUnprepared == true ? 'fa-angle-down' : 'fa-angle-right'}"></i>
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
						<i class="subheader fa {showPrepared == true ? 'fa-angle-down' : 'fa-angle-right'}"></i>
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
			<section class="subsection">
				<div class="subsection-title-bar">
					<button class="section-toggle-btn" on:click={() => showGeoreferenced = !showGeoreferenced} style="">
						<a id="georeferenced"><h3 style="margin-right:10px">Georeferenced ({VOLUME.items.layers.length})</h3></a>
						<i class="subheader fa {showGeoreferenced == true ? 'fa-angle-down' : 'fa-angle-right'}"></i>
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
									<li><strong>Downloads</strong></li>
									<li>Image: <a href="{layer.urls.document}" title="Download JPEG">JPEG</a>
										&bullet;&nbsp;<a href="{layer.urls.cog}" title="Download GeoTIFF">GeoTIFF</a>
									</li>
									<li>GCPs: <a href="/mrm/{layer.slug}?resource=gcps-geojson" title="Download GCPs as GeoJSON">GeoJSON</a>
										&bullet;&nbsp;<a href="/mrm/{layer.slug}?resource=points" title="Download GCPs as QGIS .points file (EPSG:3857)">.points</a></li>
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
			<section class="subsection" style="border-bottom:none;">
				<div class="subsection-title-bar">
					<button class="section-toggle-btn" on:click={() => showMultimask = !showMultimask} style="">
						<h3 style="margin-right:10px">Multimask ({mmLbl})</h3>
						<i class="subheader fa {showMultimask == true ? 'fa-angle-down' : 'fa-angle-right'}"></i>
					</button>
				</div>
				{#if showMultimask}
				<div transition:slide>
					<p>
					{#if !VOLUME.multimask}
						No multimask has been created yet for this volume.
					{/if}
					</p>
					<a href={VOLUME.urls.trim}>{#if VOLUME.multimask}Edit{:else}Create{/if} Multimask</a>
				</div>
				{/if}
			</section>
		</div>
	</section>
	<section>
		<div class="section-title-bar">
			<button class="section-toggle-btn" on:click={() => showDownload = !showDownload}>
				<h2 style="margin-right:10px">Download & Web Services</h2>
				<i class="header fa {showDownload == true ? 'fa-angle-double-down' : 'fa-angle-double-right'}"></i>
			</button>
		</div>
		<div class="section-content" style="display:{showDownload == true ? 'block' : 'none'};">
			<section class="subsection">
				<p style="font-size:.9em;"><em>
					Only layers that have been trimmed in the Multimask will appear in the mosaic.
				</em></p>
			</section>
			<section class="subsection" style="padding-top:15px;">
				<p>GeoTIFF mosaic downloads of this entire volume are available <a href="https://about.oldinsurancemaps.net/contact/">upon request</a>. Untrimmed individual layers can be downloaded as GeoTIFFs through the <a href="#georeferenced">Georeferenced</a> section above.</p>
			</section>
			<section class="subsection" style="padding-top:15px; border-bottom:none;">
				<p>XYZ Tiles URL</p>
				{#if !VOLUME.urls.mosaic}
				<p style="font-size:.9em; color:red;"><em>
					A mosaic endpoint has not yet been generated for this volume. You can get an XYZ endpoint for each individual layer in the <a href="#georeferenced">Georeferenced</a> section above.
				</em></p>
				{:else}
				<pre>{mosaicUrl}</pre>
				<p>Here is documentation for how to use this URL in:
					<a href="https://leafletjs.com/reference.html#tilelayer">Leaflet</a>,
					<a href="https://openlayers.org/en/latest/examples/xyz.html">OpenLayers</a>,
					<a href="https://maplibre.org/maplibre-gl-js-docs/example/map-tiles/">Mapbox/MapLibre GL JS</a>,
					<a href="https://docs.qgis.org/3.22/en/docs/user_manual/managing_data_source/opening_data.html#using-xyz-tile-services">QGIS</a>, and
					<a href="https://esribelux.com/2021/04/16/xyz-tile-layers-in-arcgis-platform/">ArcGIS</a>.
				</p>
				{/if}
				<p><em>If you appreciate these resources, please consider <a href="/#support">supporting this project</a>.</em></p>
			</section>
		</div>
	</section>
	<section style="border-bottom:none;">
		<div class="section-title-bar">
			<h2 style="margin-right:10px">Contributors & Attribution</h2>
		</div>
		<div class="section-content" style="display:flex'; flex-direction:column;">
			<p>
				{VOLUME.sessions.prep_ct} sheet{#if VOLUME.sessions.prep_ct != 1}s{/if} prepared{#if VOLUME.sessions.prep_ct > 0}&nbsp;by 
				{#each VOLUME.sessions.prep_contributors as c, n}<a href="{c.profile}">{c.name}</a> ({c.ct}){#if n != VOLUME.sessions.prep_contributors.length-1}, {/if}{/each}{/if}
				<br>
				{VOLUME.sessions.georef_ct} georeferencing session{#if VOLUME.sessions.georef_ct != 1}s{/if}{#if VOLUME.sessions.georef_ct > 0}&nbsp;by 
				{#each VOLUME.sessions.georef_contributors as c, n}<a href="{c.profile}">{c.name}</a> ({c.ct}){#if n != VOLUME.sessions.georef_contributors.length-1}, {/if}{/each}{/if}
			</p>
			<p><strong>Credit Line: Library of Congress, Geography and Map Division, Sanborn Maps Collection.</strong>
			<a href="{VOLUME.urls.loc_resource}" target="_blank">View on loc.gov <i class="fa fa-external-link"></i></a></p>
		</div>
	</section>
</main>

<style>

main { 
	margin-bottom: 10px;
}

h2 {
	font-size: 1.6em;
}

h3 {
	font-size: 1.3em;
	margin-top: 15px;
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
i.subheader {
	font-size: 1.3em;
}

button.section-toggle-btn:hover {
	color: #1b4060;
}

button.section-toggle-btn:disabled {
	color: grey;
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
