<script>
import { slide } from 'svelte/transition';

import Icon from 'svelte-icons-pack/Icon.svelte';
import FiTool from 'svelte-icons-pack/fi/FiTool';
import FiRefreshCcw from 'svelte-icons-pack/fi/FiRefreshCcw';
import FiExternalLink from 'svelte-icons-pack/fi/FiExternalLink';

import {getCenter} from 'ol/extent';

import TitleBar from '../components/TitleBar.svelte';
import PlaceSelect from "../components/PlaceSelect.svelte";
import VolumePreviewMap from "../components/VolumePreviewMap.svelte";
import MultiTrim from "../components/MultiTrim.svelte";
import ConditionalDoubleChevron from '../components/ConditionalDoubleChevron.svelte';

import {makeTitilerXYZUrl} from '../js/utils';

export let VOLUME;
export let OTHER_VOLUMES;
export let CSRFTOKEN;
export let USER_TYPE;
export let MAPBOX_API_KEY;
export let TITILER_HOST;

$: sheetsLoading = VOLUME.status == "initializing...";

// This variable is used to trigger a reinit of the VolumePreviewMap component.
// See https://svelte.dev/repl/65c80083b515477784d8128c3655edac?version=3.24.1
let reinitMap = [{}]

let hash = window.location.hash.substr(1);
if (VOLUME.items.layers.length > 0 && hash === "") {
	setHash("preview")
}

$: showMap = hash == 'preview';
$: showUnprepared = hash == 'unprepared';
$: showPrepared = hash == 'prepared';
$: showGeoreferenced = hash == 'georeferenced';
$: showMultimask = hash == 'multimask';
$: showDownload = hash == 'download';

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
	});
}

let mmLbl = `0/${VOLUME.items.layers.length}`;
if (VOLUME.multimask != undefined) {
	mmLbl = `${Object.keys(VOLUME.multimask).length}/${VOLUME.sorted_layers.main.length}`;
}
let mosaicUrl;
let ohmUrl;
if (VOLUME.urls.mosaic_json) {
	mosaicUrl = makeTitilerXYZUrl({
		host: TITILER_HOST,
		url: VOLUME.urls.mosaic_json
	})
	// make the OHM url here
	const mosaicUrlEncoded = makeTitilerXYZUrl({
		host: TITILER_HOST,
		url: VOLUME.urls.mosaic_json,
		doubleEncode: true
	})
	const ll = getCenter(VOLUME.extent);
	ohmUrl = `https://www.openhistoricalmap.org/edit#map=16/${ll[1]}/${ll[0]}&background=custom:${mosaicUrlEncoded}`
}

let settingKeyMapLayer = false;

const sideLinks = [
	{
		display: "Open in main viewer",
		url: VOLUME.urls.viewer,
		external: true,
	},
]

function setHash(newHash) {
	// override the exception that allows the preview map to be shown on initial load
	// showPreviewOnLoad = false;
	if (hash == newHash) { 
		history.replaceState(null, document.title, window.location.pathname + window.location.search);
		hash = null
	} else {
		history.replaceState(null, document.title, `#${newHash}`);
		hash = newHash
	}
}

</script>

<div id="vModal" class="modal">
	<button id="closeModal" class="close close-vmodal" on:click={closeModal}>&times;</button>
	<div class="modal-content" style="text-align:center;">
		<img id="modalImg" alt="" src="">
		<div id="imgCaption"><h5>~</h5></div>
	</div>
</div>
<main>
	<TitleBar TITLE={VOLUME.title} SIDE_LINKS={sideLinks} ICON_LINKS={[]}/>
	<section>
		<p>
			{#each OTHER_VOLUMES as link, n}
            {#if n != 0}&nbsp;&bullet;&nbsp;{/if}
            {#if link.url}<a href={link.url} title={link.alt ? link.alt : link.display}>{link.display}</a>{:else}{link.display}{/if}
			{/each}
			<PlaceSelect VOLUME={VOLUME} />
        </p>
	</section>
	<section>
		<div class="section-title-bar">
			<button class="section-toggle-btn" disabled={VOLUME.items.layers.length == 0} 
				on:click={() => {setHash('preview')}}>
				<ConditionalDoubleChevron down={showMap} size="md"/>
				<a id="preview"><h2>Mosaic Preview</h2></a>
			</button>
		</div>
		{#if showMap}
		<div class="section-content" transition:slide>
		<!-- <div class="section-content" style="display:{showMap == true ? 'block' : 'none'};"> -->
			{#each reinitMap as key (key)}
				<VolumePreviewMap VOLUME={VOLUME} MAPBOX_API_KEY={MAPBOX_API_KEY} TITILER_HOST={TITILER_HOST} />
			{/each}
			<div style="margin-top: 5px;">
				<p>The preview map shows progress toward a full mosaic of this volume's content.</p>
			</div>
		</div>
		{/if}
	</section>
	<section>
		<div class="section-title-bar">
			<ConditionalDoubleChevron down={true} size="md" /><a id="overview" class="no-link">
				<h2 style="margin-right:10px; display:inline-block;">Georeferencing Overview</h2>
			</a>
		</div>
		<div>
			<div style="display:flex; justify-content:space-between; align-items:center;">
				<div>
					{#if VOLUME.sheet_ct.loaded < VOLUME.sheet_ct.total && USER_TYPE != 'anonymous' && !sheetsLoading}
						<button on:click={() => { postOperation("initialize"); sheetsLoading = true; }}>Load Volume ({VOLUME.sheet_ct.total} sheet{#if VOLUME.sheet_ct.total != 1}s{/if})</button>
					{/if}
					<em><span>
						{#if sheetsLoading}
						Loading sheet {VOLUME.sheet_ct.loaded}/{VOLUME.sheet_ct.total}... (you can safely leave this page).
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
				<div class="control-btn-group">
					{#if USER_TYPE != "anonymous"}
					<button class="control-btn" title="Repair Summary (may take a moment)" on:click={() => {postOperation("refresh-lookups")}}>
						<Icon src={FiTool} />
					</button>
					{/if}
					<button class="control-btn" title="Refresh Summary" on:click={() => { postOperation("refresh") }}>
						<Icon src={FiRefreshCcw} />
					</button>
				</div>
			</div>
			{#if USER_TYPE == 'anonymous' }
			<div class="signin-reminder">
			<p><em>
				<a href="/account/login">sign in</a> or
				<a href="/account/signup">sign up</a> to work on this content
			</em></p>
			</div>
			{/if}
			<section class="subsection">
				<div class="subsection-title-bar">
					<button class="section-toggle-btn" on:click={() => setHash("unprepared")}>
						<ConditionalDoubleChevron down={showUnprepared} size="md" />
						<a id="unprepared">
							<h3>
								Unprepared ({VOLUME.items.unprepared.length})
								{#if VOLUME.items.processing.unprep != 0}
								&mdash; {VOLUME.items.processing.unprep} in progress...
								{/if}
							</h3>
						</a>
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
					<button class="section-toggle-btn" on:click={() => setHash("prepared")}>
						<ConditionalDoubleChevron down={showPrepared} size="md" />
						<a id="prepared"><h3>
							Prepared ({VOLUME.items.prepared.length})
							{#if VOLUME.items.processing.prep != 0}
							&mdash; {VOLUME.items.processing.prep} in progress...
							{/if}
						</h3></a>
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
								{#if document.lock_enabled}
								<ul style="text-align:center">
									<li><em>georeferencing in progress...</em></li>
									<li>{document.lock_details.user.name}</li>
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
					<button class="section-toggle-btn" on:click={() => setHash("georeferenced")}>
						<ConditionalDoubleChevron down={showGeoreferenced} size="md" />
						<a id="georeferenced"><h3>Georeferenced ({VOLUME.items.layers.length})</h3></a>
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
					<button class="section-toggle-btn" on:click={() => setHash('multimask')}>
						<ConditionalDoubleChevron down={showMultimask} size="md" />
						<a id="multimask"><h3>MultiMask ({mmLbl})</h3></a>
					</button>
				</div>
				{#if showMultimask}
				<div transition:slide>
					<MultiTrim VOLUME={VOLUME}
						CSRFTOKEN={CSRFTOKEN}
						USER_TYPE={USER_TYPE}
						MAPBOX_API_KEY={MAPBOX_API_KEY}
						TITILER_HOST={TITILER_HOST} />
					<div style="margin-top: 5px;">
						<p>Only layers with a mask will be included in MosaicJSON or GeoTIFF mosaic output.</p>
					</div>
				</div>
				{/if}
			</section>
		</div>
	</section>
	
	<section>
		<div class="section-title-bar">
			<button class="section-toggle-btn" on:click={() => setHash("download")}>
				<ConditionalDoubleChevron down={showDownload} size="md"/>
				<a id="download">
					<h2 style="margin-right:10px; display: inline-block;">Download & Web Services</h2>
				</a>
			</button>
		</div>
		{#if showDownload}
		<div transition:slide class="section-content">
			<section class="subsection">
				<p style="font-size:.9em;"><em>
					Only layers that have been trimmed in the <a href="#multimask">Multimask</a> will appear in the mosaic. You can access untrimmed layers individually through the <a href="#georeferenced">Georeferenced</a> section above. If you appreciate these resources, please consider <a href="/#support">supporting this project</a>.
				</em></p>
			</section>
			<section class="subsection" style="padding-top:15px;">
				<p><strong>XYZ Tiles URL</strong></p>
				{#if !VOLUME.urls.mosaic_json}
				<p style="font-size:.9em; color:red;"><em>
					A mosaic endpoint has not yet been generated for this volume.
				</em></p>
				{:else}
				<pre>{mosaicUrl}</pre>
				<p>Use this URL in:
					<a href="https://leafletjs.com/reference.html#tilelayer">Leaflet</a>,
					<a href="https://openlayers.org/en/latest/examples/xyz.html">OpenLayers</a>,
					<a href="https://maplibre.org/maplibre-gl-js-docs/example/map-tiles/">Mapbox/MapLibre GL JS</a>,
					<a href="https://docs.qgis.org/3.22/en/docs/user_manual/managing_data_source/opening_data.html#using-xyz-tile-services">QGIS</a>, and
					<a href="https://esribelux.com/2021/04/16/xyz-tile-layers-in-arcgis-platform/">ArcGIS</a>.
					<br>Open in the <a href="{ohmUrl}" alt="Open mosaic in OHM Editor" target="_blank">Open Historical Map editor <Icon src={FiExternalLink} /></a>.
				</p>
				{/if}
			</section>
			<section class="subsection" style="padding-top:15px; border-bottom:none;">
				<p><strong>GeoTIFF</strong> mosaic downloads of this entire volume are available <a href="mailto:hello@oldinsurancemaps.net">upon request</a>.</p>
			</section>
		</div>
		{/if}
	</section>
	<section style="border-bottom:none;">
		<div class="section-title-bar">
			<ConditionalDoubleChevron down={true} size="md"/><a id="contributors" class="no-link">
				<h2 style="margin-right:10px; display: inline-block;">Contributors & Attribution</h2>
			</a>
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
			<a href="{VOLUME.urls.loc_resource}" target="_blank">View item on loc.gov <Icon src={FiExternalLink} /></a></p>
		</div>
	</section>
</main>

<style>

#preview, #unprepared, #prepared, #georeferenced, #multimask, #download, #contributors {
  scroll-margin-top: 50px;
}

a.no-link {
	color:unset;
	text-decoration:unset;
}

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

button.section-toggle-btn, a {
	text-decoration: none;
}

button.section-toggle-btn:hover {
	color: #1b4060;
}

button.section-toggle-btn:disabled, button.section-toggle-btn:disabled > a {
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
