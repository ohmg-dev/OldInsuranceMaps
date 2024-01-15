<script>
import { slide } from 'svelte/transition';

import IconContext from 'phosphor-svelte/lib/IconContext';
import { iconProps } from "../js/utils"

import Wrench from "phosphor-svelte/lib/Wrench";
import ArrowRight from "phosphor-svelte/lib/ArrowRight";
import ArrowsClockwise from "phosphor-svelte/lib/ArrowsClockwise";
import ArrowSquareOut from "phosphor-svelte/lib/ArrowSquareOut";

import {getCenter} from 'ol/extent';

import TitleBar from './components/TitleBar.svelte';
import VolumePreviewMap from "./components/VolumePreviewMap.svelte";
import MultiTrim from "./components/MultiTrim.svelte";
import ConditionalDoubleChevron from './components/ConditionalDoubleChevron.svelte';

import ItemPreviewMapModal from './components/modals/ItemPreviewMapModal.svelte'
import GeoreferenceOverviewModal from './components/modals/GeoreferenceOverviewModal.svelte'
import UnpreparedSectionModal from './components/modals/UnpreparedSectionModal.svelte'
import PreparedSectionModal from './components/modals/PreparedSectionModal.svelte'
import GeoreferencedSectionModal from './components/modals/GeoreferencedSectionModal.svelte'
import MultiMaskModal from './components/modals/MultiMaskModal.svelte'
import NonMapContentModal from './components/modals/NonMapContentModal.svelte'
import DocumentViewerModal from './components/modals/DocumentViewerModal.svelte'
import LayerViewerModal from './components/modals/LayerViewerModal.svelte'

import Modal, {getModal} from './components/modals/Base.svelte';

import OpenModal from './components/buttons/OpenModal.svelte';

import {makeTitilerXYZUrl} from '../js/utils';

import SingleLayerViewer from './components/SingleLayerViewer.svelte';
import SingleDocumentViewer from './components/SingleDocumentViewer.svelte';

export let VOLUME;
export let CSRFTOKEN;
export let USER_TYPE;
export let MAPBOX_API_KEY;
export let TITILER_HOST;

let current_identifier = VOLUME.identifier
function goToItem(identifier) {
	window.location = "/loc/" + current_identifier
}

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
$: showNonmaps = hash == 'nonmaps';
$: showMultimask = hash == 'multimask';
$: showDownload = hash == 'download';

let refreshingLookups = false;

let layerCategories = [
	{value: "graphic_map_of_volumes", label: "Graphic Map of Volumes"},
	{value: "key_map", label: "Key Map"},
	{value: "congested_district", label: "Congested District Map"},
	{value: "main", label: "Main Content (default)"},
]
let layerCategoryLookup = {};
function setLayerCategoryLookup(VOLUME) {
	layerCategoryLookup = {};
	for (let category in VOLUME.sorted_layers) {
		VOLUME.sorted_layers[category].forEach( function (lyr) {
			layerCategoryLookup[lyr.slug] = category;
		});
	}
}
$: setLayerCategoryLookup(VOLUME)

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
	if (operation == "refresh-lookups") {
		refreshingLookups = true;
	}
	const data = JSON.stringify({
		"operation": operation,
		"indexLayerIds": indexLayerIds,
		"layerCategoryLookup": layerCategoryLookup,
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

function postGeoref(url, operation, status) {
	const data = JSON.stringify({
		"operation": operation,
		"status": status,
	});
	fetch(url, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json;charset=utf-8',
			'X-CSRFToken': CSRFTOKEN,
		},
		body: data,
	})
	.then(response => response.json())
	.then(result => {
		postOperation("refresh");
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
		display: `View all ${VOLUME.locale.display_name} mosaics`,
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

let reinitMap2 = [{}]
let modalDocUrl = "";
let modalDocImageSize = "";

let reinitMap3 = [{}]
let modalLyrUrl = "";
let modalLyrExtent = "";

</script>
<IconContext values={iconProps}>
<ItemPreviewMapModal id={"modal-preview-map"} placeName={VOLUME.locale.display_name} viewerUrl={VOLUME.urls.viewer}/>
<GeoreferenceOverviewModal id={"modal-georeference-overview"} />
<UnpreparedSectionModal id={'modal-unprepared'} />
<PreparedSectionModal id={"modal-prepared"} />
<GeoreferencedSectionModal id={"modal-georeferenced"} />
<MultiMaskModal id={"modal-multimask"} />
<NonMapContentModal id={"modal-non-map"} />
<Modal id={"modal-doc-view"} full={true}>
{#each reinitMap2 as key (key)}
	<SingleDocumentViewer LAYER_URL={modalDocUrl} IMAGE_SIZE={modalDocImageSize} />
	{/each}
</Modal>
<Modal id={"modal-lyr-view"} full={true}>
{#each reinitMap3 as key (key)}
	<SingleLayerViewer LAYER_URL={modalLyrUrl} EXTENT={modalLyrExtent} MAPBOX_API_KEY={MAPBOX_API_KEY} TITILER_HOST={TITILER_HOST} />
{/each}
</Modal>
<main>
	<section class="breadcrumbs">
		{#each VOLUME.locale.breadcrumbs as bc, n}
		<a href="/{bc.slug}">{bc.name}</a>{#if n != VOLUME.locale.breadcrumbs.length-1}<ArrowRight size={12} />{/if}
		{/each}
		<ArrowRight size={12} />
		<select class="item-select" bind:value={current_identifier} on:change={goToItem}>
			{#each VOLUME.locale.volumes as v}
			<option value={v.identifier}>{v.year}{v.volume_no ? " vol. " + v.volume_no : ''}</option>
			{/each}
		</select>
	</section>
	<TitleBar LOCK_BUTTON={VOLUME.status == "locked"} TITLE={VOLUME.title} SIDE_LINKS={sideLinks} ICON_LINKS={[]}/>
	<section>
		<div class="section-title-bar">
			<button class="section-toggle-btn" disabled={VOLUME.items.layers.length == 0} 
				on:click={() => {setHash('preview')}}>
				<ConditionalDoubleChevron down={showMap} size="md"/>
				<a id="preview"><h2>Mosaic Preview ({VOLUME.items.layers.length} layers)</h2></a>
			</button>
			<OpenModal modalName="modal-preview-map" />
		</div>
		{#if showMap}
		<div class="section-content" transition:slide>
		<!-- <div class="section-content" style="display:{showMap == true ? 'block' : 'none'};"> -->
			{#each reinitMap as key (key)}
				<VolumePreviewMap VOLUME={VOLUME} MAPBOX_API_KEY={MAPBOX_API_KEY} TITILER_HOST={TITILER_HOST} />
			{/each}
		</div>
		{/if}
	</section>
	<section>
		<div class="section-title-bar">
			<div>
				<ConditionalDoubleChevron down={true} size="md" />
				<a id="overview" class="no-link">
					<h2 style="margin-right:10px; display:inline-block;">Georeferencing Overview</h2>
				</a>
			</div>
			{#if refreshingLookups}
				<div class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
			{/if}
			<OpenModal modalName="modal-georeference-overview" />
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
				<div class="control-btn-group">
					{#if USER_TYPE != "anonymous"}
					<button class="control-btn" title="Repair Summary (may take a moment)" on:click={() => {postOperation("refresh-lookups")}}>
						<Wrench />
					</button>
					{/if}
					<button class="control-btn" title="Refresh Summary" on:click={() => { postOperation("refresh") }}>
						<ArrowsClockwise />
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
					<OpenModal modalName="modal-unprepared" />
				</div>
				{#if showUnprepared}
				<div transition:slide>
					<div class="documents-column">
						{#each VOLUME.items.unprepared as document}
						<div class="document-item">
							<div><p><a href={document.urls.resource} title={document.title}>Sheet {document.page_str}</a></p></div>
							<button class="thumbnail-btn" on:click={() => {
								modalDocUrl=document.urls.image;
								modalDocImageSize=document.image_size;
								getModal('modal-doc-view').open();
								reinitMap2 = [{}]}} >
								<img style="cursor:zoom-in"
									src={document.urls.thumbnail}
									alt={document.title}
									/>
							</button>
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
					<OpenModal modalName="modal-prepared" />
				</div>
				{#if showPrepared}
				<div transition:slide>
					<div class="documents-column">
						{#each VOLUME.items.prepared as document}
						<div class="document-item">
							<div><p><a href={document.urls.resource} title={document.title}>{document.title}</a></p></div>
							<button class="thumbnail-btn" on:click={() => {
								modalDocUrl=document.urls.image;
								modalDocImageSize=document.image_size;
								getModal('modal-doc-view').open();
								reinitMap2 = [{}]}} >
								<img style="cursor:zoom-in"
									src={document.urls.thumbnail}
									alt={document.title}
									/>
							</button>
							<div>
								{#if document.lock_enabled}
								<ul style="text-align:center">
									<li><em>georeferencing in progress...</em></li>
									<li>{document.lock_details.user.name}</li>
								</ul>
								{:else}
								<ul>
									<li><a href={document.urls.georeference} title="georeference this document">georeference &rarr;</a></li>
									<li><button class="btn-link" on:click={() => {postGeoref(document.urls.georeference, "set-status", "nonmap")}}><em>set as non-map</em></button></li>
								</ul>
								{/if}
							</div>
						</div>
						{/each}
					</div>
				</div>
				{/if}
			</section>
			<section class="subsection">
				<div class="subsection-title-bar">
					<button class="section-toggle-btn" on:click={() => setHash("georeferenced")}>
						<ConditionalDoubleChevron down={showGeoreferenced} size="md" />
						<a id="georeferenced"><h3>Georeferenced ({VOLUME.items.layers.length})</h3></a>
					</button>
					<OpenModal modalName="modal-georeferenced" />
				</div>
				{#if showGeoreferenced}
				<div transition:slide>
					<div style="margin: 10px 0px;">
						{#if VOLUME.items.layers.length > 0 && !settingKeyMapLayer}
						<button on:click={() => settingKeyMapLayer = !settingKeyMapLayer}
							disabled={USER_TYPE == 'anonymous'}
							title={USER_TYPE == 'anonymous' ? 'You must be signed in to classify layers' : 'Click to enable layer classification'}
							>Classify Layers</button>
						{/if}
						{#if settingKeyMapLayer}
						<button on:click={() => { settingKeyMapLayer = false; postOperation("set-index-layers"); }}>Save</button>
						<button on:click={() => { settingKeyMapLayer = false; }}>Cancel</button>
						{/if}
					</div>
					<div class="documents-column">
						{#each VOLUME.items.layers as layer}
						<div class="document-item">
							<div><p><a href={layer.urls.resource} title={layer.title}>{layer.title}</a></p></div>
							<!-- <a href={layer.urls.view} target="_blank" title="inspect layer in standalone map" style="cursor:zoom-in">
								<img src={layer.urls.thumbnail} alt={document.title}>
							</a> -->
							<!-- <a  /> -->
							<button class="thumbnail-btn" on:click={() => {
								modalLyrUrl=layer.urls.cog;
								modalLyrExtent=layer.extent;
								getModal('modal-lyr-view').open();
								reinitMap3 = [{}]}}>
								<img style="cursor:zoom-in"
									src={layer.urls.thumbnail}
									alt={layer.title}
									>
							</button>
							<div>
								{#if layer.lock && layer.lock.enabled}
								<ul style="text-align:center">
									<li><em>session in progress...</em></li>
									<li>{layer.lock.username}</li>
								</ul>
								{:else}
								<ul>
									<li><a href={layer.urls.georeference} title="edit georeferencing">edit georeferencing &rarr;</a></li>
									<li><a href={layer.urls.resource} title="edit georeferencing">downloads & web services &rarr;</a></li>
									<!--
										<li><strong>Downloads</strong></li>
										<li>Image: <a href="{layer.urls.document}" title="Download JPEG">JPEG</a>
											&bullet;&nbsp;<a href="{layer.urls.cog}" title="Download GeoTIFF">GeoTIFF</a>
										</li>
										<li>GCPs: <a href="/mrm/{layer.slug}?resource=gcps-geojson" title="Download GCPs as GeoJSON">GeoJSON</a>
											&bullet;&nbsp;<a href="/mrm/{layer.slug}?resource=points" title="Download GCPs as QGIS .points file (EPSG:3857)">.points</a></li>
										-->
								</ul>
								{/if}
								{#if settingKeyMapLayer}
								<select bind:value={layerCategoryLookup[layer.slug]}>
									{#each layerCategories as layerCat}
									<option value={layerCat.value}>{layerCat.label}</option>
									{/each}
								</select>
								{/if}
							</div>
						</div>
						{/each}
					</div>
					<!-- {/if} -->
				</div>
				{/if}
			</section>
			<section class="subsection">
				<div class="subsection-title-bar">
					<button class="section-toggle-btn" on:click={() => setHash('multimask')}>
						<ConditionalDoubleChevron down={showMultimask} size="md" />
						<a id="multimask"><h3>MultiMask ({mmLbl})</h3></a>
					</button>
					<OpenModal modalName="modal-multimask" />
				</div>
				{#if showMultimask}
				<div transition:slide>
					<MultiTrim VOLUME={VOLUME}
						CSRFTOKEN={CSRFTOKEN}
						USER_TYPE={USER_TYPE}
						MAPBOX_API_KEY={MAPBOX_API_KEY}
						TITILER_HOST={TITILER_HOST} />
				</div>
				{/if}
			</section>
			<section class="subsection" style="border-bottom:none;">
				<div class="subsection-title-bar">
					<button class="section-toggle-btn" on:click={() => setHash("nonmaps")}>
						<ConditionalDoubleChevron down={showNonmaps} size="md" />
						<a id="georeferenced"><h3>Non-Map Content ({VOLUME.items.nonmaps.length})</h3></a>
					</button>
					<OpenModal modalName="modal-non-map" />
				</div>
				{#if showNonmaps}
				<div transition:slide>
					<div class="documents-column">
						{#each VOLUME.items.nonmaps as nonmap}
						<div class="document-item">
							<div><p><a href={nonmap.urls.resource} title={nonmap.title}>{nonmap.title}</a></p></div>
							<a href={nonmap.urls.resource} target="_blank" title="go to detail page for this document" style="cursor:zoom-in">
								<img src={nonmap.urls.thumbnail} alt={nonmap.title}>
							</a>
							<div>
								<ul>
									<li><button class="btn-link" on:click={() => {postGeoref(nonmap.urls.georeference, "set-status", "prepared")}} title="set this document back to 'prepared' so it can be georeferenced">this <em>is</em> a map</button></li>
								</ul>
							</div>
						</div>
						{/each}
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
					<br>Open in the <a href="{ohmUrl}" alt="Open mosaic in OHM Editor" target="_blank">Open Historical Map editor <ArrowSquareOut /></a>.
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
			<div>
				<ConditionalDoubleChevron down={true} size="md"/>
				<a id="contributors" class="no-link">
					<h2 style="margin-right:10px; display: inline-block;">Contributors & Attribution</h2>
				</a>
			</div>
			<div></div>
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
			<a href="{VOLUME.urls.loc_resource}" target="_blank">View item on loc.gov<ArrowSquareOut /></a></p>
		</div>
	</section>
</main>
</IconContext>
<style>

#preview, #unprepared, #prepared, #georeferenced, #multimask, #download, #contributors {
  scroll-margin-top: 50px;
}

a.no-link {
	color:unset;
	text-decoration:unset;
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

button.section-toggle-btn, a {
	text-decoration: none;
}

button.section-toggle-btn:hover {
	color: #1b4060;
}

button.section-toggle-btn:disabled, button.section-toggle-btn:disabled > a {
	color: grey;
}

button.thumbnail-btn {
	border: none;
	background: none;
	cursor: zoom-in;
}

section.breadcrumbs {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	padding: 5px 0px;
	font-size: .95em;
	border-bottom: none;
}

:global(section.breadcrumbs svg) {
	margin: 0px 2px;
}

.section-title-bar {
	display:flex;
	flex-direction:row;
	justify-content:space-between;
	align-items:center;
}

.subsection-title-bar {
	display:flex;
	flex-direction:row;
	justify-content:space-between;
	align-items:center;
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

select.item-select {
	margin-right: 3px;
	color: #2c689c;
	cursor: pointer;
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
