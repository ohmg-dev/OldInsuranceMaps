<script>
import { slide } from 'svelte/transition';

import IconContext from 'phosphor-svelte/lib/IconContext';
import { iconProps, makeTitilerXYZUrl } from "@lib/utils"

import ArrowRight from "phosphor-svelte/lib/ArrowRight";

import {getCenter} from 'ol/extent';

import Link from '@components/base/Link.svelte';
import TitleBar from '@components/layout/TitleBar.svelte';
import MultiMask from "@components/interfaces/MultiMask.svelte";
import ConditionalDoubleChevron from './buttons/ConditionalDoubleChevron.svelte';

import MapPreviewModal from './modals/MapPreviewModal.svelte'
import GeoreferenceOverviewModal from './modals/GeoreferenceOverviewModal.svelte'
import UnpreparedSectionModal from './modals/UnpreparedSectionModal.svelte'
import PreparedSectionModal from './modals/PreparedSectionModal.svelte'
import GeoreferencedSectionModal from './modals/GeoreferencedSectionModal.svelte'
import MultiMaskModal from './modals/MultiMaskModal.svelte'
import NonMapContentModal from './modals/NonMapContentModal.svelte'
import GeoreferencePermissionsModal from './modals/GeoreferencePermissionsModal.svelte'

import IconButton from "@components/base/IconButton.svelte";
import OpenModalButton from '@components/base/OpenModalButton.svelte';
import Modal, {getModal} from '@components/base/Modal.svelte';

import MapPreview from "@components/interfaces/MapPreview.svelte";
import SingleLayerViewer from '@components/interfaces/SingleLayerViewer.svelte';
import SingleDocumentViewer from '@components/interfaces/SingleDocumentViewer.svelte';
import DownloadSectionModal from './modals/ItemDownloadSectionModal.svelte';
import ItemDetails from './sections/ItemDetails.svelte';
    import SigninReminder from '../layout/SigninReminder.svelte';

export let VOLUME;
export let ANNOTATION_SETS;
export let CSRFTOKEN;
export let USER;
export let MAPBOX_API_KEY;
export let TITILER_HOST;
export let ROUTES;

console.log(ROUTES)

console.log(ANNOTATION_SETS)

let currentAnnotationSet = "main-content";
const annotationSetLookup = {}
$: {
	ANNOTATION_SETS.forEach(function (annoSet) {annotationSetLookup[annoSet.id] = annoSet})
}

let userCanEdit = false;
userCanEdit = USER.is_staff || (VOLUME.access == "any" && USER.is_authenticated) || (VOLUME.access == "sponsor" && VOLUME.sponsor == USER.username)

let currentIdentifier = VOLUME.identifier
function goToItem() {
	window.location = "/map/" + currentIdentifier
}
let currentDoc = "---";
function goToDocument() {
	window.location = "/resource/" + currentDoc
}

$: sheetsLoading = VOLUME.status == "initializing...";

let hash = window.location.hash.substr(1);

function updateAnnotationSet(e, layerId) {

	// a little bit of translation needed here during transition
	const category = e.target.options[e.target.selectedIndex].value
	const categorySlugLookup = {
		"main": "main-content",
		"key_map": "key-map",
		"congest_district": "congested-district-map",
		"graphic_map_of_volumes": "graphic-map-of-volumes",
	}

	const postData = JSON.stringify({
		operation: "update",
        resourceId: layerId,
        volumeId: VOLUME.identifier,
        categorySlug: categorySlugLookup[category]
	})

	fetch(ROUTES.post_annotation_set, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json;charset=utf-8',
			'X-CSRFToken': CSRFTOKEN,
		},
		body: postData,
	})
	.then(response => response.json())
	.then(result => {
		fetchAnnotationSets()
	});
}

const sectionVis = {
	"summary": (!hash && VOLUME.items.layers.length == 0) || hash == "summary",
	"preview": (!hash && VOLUME.items.layers.length > 0) || hash == "preview",
	"unprepared": hash == "unprepared",
	"prepared": hash == "prepared",
	"georeferenced": hash == "georeferenced",
	"nonmaps": hash == "nonmaps",
	"multimask": hash == "multimask",
	"download": hash == "download",
}

function toggleSection(sectionId) {
	sectionVis[sectionId] = !sectionVis[sectionId];
}

function setHash(hash){
	history.replaceState(null, document.title, `#${hash}`);
}

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
		// need to trigger a reinit of the MapPreview component
		VOLUME = result;
		sheetsLoading = VOLUME.status == "initializing...";
		if (operation == "refresh-lookups") {
			refreshingLookups = false;
		}
	});
}

function fetchAnnotationSets() {
	fetch(`${ROUTES.get_annotation_sets}?volume=${VOLUME.identifier}`, {headers: ROUTES.api_headers})
	.then(response => response.json())
	.then(result => {
		ANNOTATION_SETS = result  
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
if (VOLUME.urls.mosaic_geotiff) {
	mosaicUrl = makeTitilerXYZUrl({
		host: TITILER_HOST,
		url: VOLUME.urls.mosaic_geotiff
	})
	// make the OHM url here
	const mosaicUrlEncoded = makeTitilerXYZUrl({
		host: TITILER_HOST,
		url: VOLUME.urls.mosaic_geotiff,
		doubleEncode: true
	})
	const ll = getCenter(VOLUME.extent);
	ohmUrl = `https://www.openhistoricalmap.org/edit#map=16/${ll[1]}/${ll[0]}&background=custom:${mosaicUrlEncoded}`
}

let settingKeyMapLayer = false;

function resetMosaicPreview() {
	fetchAnnotationSets()
}
let modalDocUrl = "";
let modalDocImageSize = "";

let modalLyrUrl = "";
let modalLyrExtent = "";

</script>
<IconContext values={iconProps}>
<MapPreviewModal id={"modal-preview-map"} placeName={VOLUME.locale.display_name} viewerUrl={VOLUME.urls.viewer}/>
<GeoreferenceOverviewModal id={"modal-georeference-overview"} />
<UnpreparedSectionModal id={'modal-unprepared'} />
<PreparedSectionModal id={"modal-prepared"} />
<GeoreferencedSectionModal id={"modal-georeferenced"} />
<MultiMaskModal id={"modal-multimask"} />
<NonMapContentModal id={"modal-non-map"} />
<GeoreferencePermissionsModal id={"modal-permissions"} user={USER} userCanEdit={userCanEdit} item={VOLUME} />
<Modal id={"modal-doc-view"} full={true}>
{#key modalDocUrl}
	<SingleDocumentViewer LAYER_URL={modalDocUrl} IMAGE_SIZE={modalDocImageSize} />
{/key}
</Modal>
<Modal id={"modal-lyr-view"} full={true}>
{#key modalLyrUrl}
	<SingleLayerViewer LAYER_URL={modalLyrUrl} EXTENT={modalLyrExtent} MAPBOX_API_KEY={MAPBOX_API_KEY} TITILER_HOST={TITILER_HOST} />
{/key}
</Modal>
<main>
	<section class="breadcrumbs">
		{#each VOLUME.locale.breadcrumbs as bc, n}
		<Link href="/{bc.slug}">{bc.name}</Link>{#if n != VOLUME.locale.breadcrumbs.length-1}<ArrowRight size={12} />{/if}
		{/each}
		<ArrowRight size={12} />
		<select class="item-select" bind:value={currentIdentifier} on:change={goToItem}>
			{#each VOLUME.locale.volumes as v}
			<option value={v.identifier}>{v.year}{v.volume_no ? " vol. " + v.volume_no : ''}</option>
			{/each}
		</select>
		<!--
		<ArrowRight size={12} />
		<select class="item-select" bind:value={currentDoc} on:change={goToDocument}>
			<option value="---" disabled>go to...</option>
			{#each VOLUME.sheets as s}
			<option value={s.doc_id}>page {s.sheet_no}</option>
			{/each}
		</select>
		-->
	</section>
	<TitleBar TITLE={VOLUME.title} VIEWER_LINK={VOLUME.urls.viewer}/>
	<section>
		<div class="section-title-bar">
			<button class="section-toggle-btn" on:click={() => {toggleSection('summary')}} title={sectionVis['summary'] ? 'Collapse section' : 'Expand section'}>
				<ConditionalDoubleChevron down={sectionVis['summary']} size="md"/>
				<a id="summary"><h2>Summary</h2></a>
			</button>
		</div>
		{#if sectionVis['summary']}
		<div style="margin-bottom:10px;" transition:slide>
			<ItemDetails ITEM={VOLUME} {mosaicUrl} {ohmUrl}/>
		</div>
		{/if}
	</section>
	<section>
		<div class="section-title-bar">
			<button class="section-toggle-btn" disabled={VOLUME.items.layers.length == 0}
				on:click={() => {toggleSection('preview')}} title={sectionVis['preview'] ? 'Collapse section' : 'Expand section'}>
				<ConditionalDoubleChevron down={sectionVis['preview']} size="md"/>
				<a id="preview"><h2>Mosaic Preview ({VOLUME.items.layers.length} layers)</h2></a>
			</button>
			<OpenModalButton modalId="modal-preview-map" />
		</div>
		{#if sectionVis['preview']}
		<div class="section-content" transition:slide>
			{#key ANNOTATION_SETS}
				<MapPreview {ANNOTATION_SETS} {MAPBOX_API_KEY} {TITILER_HOST} />
			{/key}
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
			<div style="display:flex; align-items:center;">
				{#if USER.is_authenticated}
				<IconButton style="lite" icon="wrench" action={() => {postOperation("refresh-lookups")}} title="Regenerate summary (may take a moment)" />
				{/if}
				
				<!-- {#if userCanEdit}
				<OpenModalButton icon="lock-open" modalId="modal-permissions" />
				{:else}
				<OpenModalButton icon="lock" modalId="modal-permissions" />
				{/if} -->
				<OpenModalButton modalId="modal-georeference-overview" />
			</div>
		</div>
		<div>
			<div style="display:flex; justify-content:space-between; align-items:center;">
				<div>
					{#if VOLUME.sheet_ct.loaded < VOLUME.sheet_ct.total && userCanEdit && !sheetsLoading}
						<button on:click={() => { postOperation("initialize"); sheetsLoading = true; }}>Load Volume ({VOLUME.sheet_ct.total} sheet{#if VOLUME.sheet_ct.total != 1}s{/if})</button>
					{/if}
					<em><span>
						{#if sheetsLoading}
						Loading sheet {VOLUME.sheet_ct.loaded}/{VOLUME.sheet_ct.total}... (you can safely leave this page).
						{:else if VOLUME.sheet_ct.loaded == 0}
						No sheets loaded yet...
						{:else if VOLUME.sheet_ct.loaded < VOLUME.sheet_ct.total }
						{VOLUME.sheet_ct.loaded} of {VOLUME.sheet_ct.total} sheet{#if VOLUME.sheet_ct.total != 1}s{/if} loaded (initial load unsuccessful. Click <strong>Load Volume</strong> to retry)
						{/if}
					</span></em>
				</div>
			</div>
			{#if !USER.is_authenticated}
			<SigninReminder />
			{/if}
			<section class="subsection">
				<div class="subsection-title-bar">
					<button class="section-toggle-btn" on:click={() => toggleSection('unprepared')} disabled={VOLUME.items.unprepared.length == 0}
						title={sectionVis['unprepared'] ? 'Collapse section' : 'Expand section'}>
						<ConditionalDoubleChevron down={sectionVis['unprepared']} size="md" />
						<a id="unprepared">
							<h3 style="margin-top:5px;">
								Unprepared ({VOLUME.items.unprepared.length})
								{#if VOLUME.items.processing.unprep != 0}
								&mdash; {VOLUME.items.processing.unprep} in progress...
								{/if}
							</h3>
						</a>
					</button>
					<div class="button-list">
						<OpenModalButton modalId="modal-unprepared" />
						<!-- <IconButton style="lite" icon="link" action={() => {setHash("unprepared")}} title="Link to this section" /> -->
					</div>
				</div>
				{#if sectionVis['unprepared']}
				<div transition:slide>
					<div class="documents-column">
						{#each VOLUME.items.unprepared as document}
						<div class="document-item">
							<div><p><Link href={document.urls.resource} title={document.title}>Sheet {document.page_str}</Link></p></div>
							<button class="thumbnail-btn" on:click={() => {
								modalDocUrl=document.urls.image;
								modalDocImageSize=document.image_size;
								getModal('modal-doc-view').open();}} >
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
								{:else if userCanEdit}
								<ul>
									<li><Link href={document.urls.split} title="Prepare this document">prepare &rarr;</Link></li>
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
					<button class="section-toggle-btn" on:click={() => toggleSection("prepared")} disabled={VOLUME.items.prepared.length === 0} 
						title={sectionVis['prepared'] ? 'Collapse section' : 'Expand section'}>
						<ConditionalDoubleChevron down={sectionVis['prepared']} size="md" />
						<a id="prepared"><h3>
							Prepared ({VOLUME.items.prepared.length})
							{#if VOLUME.items.processing.prep != 0}
							&mdash; {VOLUME.items.processing.prep} in progress...
							{/if}
						</h3></a>
					</button>
					<OpenModalButton modalId="modal-prepared" />
				</div>
				{#if sectionVis['prepared']}
				<div transition:slide>
					<div class="documents-column">
						{#each VOLUME.items.prepared as document}
						<div class="document-item">
							<div><p><Link href={document.urls.resource} title={document.title}>{document.title}</Link></p></div>
							<button class="thumbnail-btn" on:click={() => {
								modalDocUrl=document.urls.image;
								modalDocImageSize=document.image_size;
								getModal('modal-doc-view').open();}} >
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
								{:else if userCanEdit}
								<ul>
									<li><Link href={document.urls.georeference} title="georeference this document">georeference &rarr;</Link></li>
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
					<button class="section-toggle-btn" on:click={() => toggleSection("georeferenced")} disabled={VOLUME.items.layers.length == 0}
						title={sectionVis['georeferenced'] ? 'Collapse section' : 'Expand section'}>
						<ConditionalDoubleChevron down={sectionVis['georeferenced']} size="md" />
						<a id="georeferenced"><h3>Georeferenced ({VOLUME.items.layers.length})</h3></a>
					</button>
					<OpenModalButton modalId="modal-georeferenced" />
				</div>
				{#if sectionVis['georeferenced']}
				<div transition:slide>
					<div style="margin: 10px 0px;">
						{#if VOLUME.items.layers.length > 0 && !settingKeyMapLayer}
						<button on:click={() => settingKeyMapLayer = !settingKeyMapLayer}
							disabled={!USER.is_authenticated}
							title={!USER.is_authenticated ? 'You must be signed in to classify layers' : 'Click to enable layer classification'}
							>Classify Layers</button>
						{/if}
						{#if settingKeyMapLayer}
						<button on:click={() => { settingKeyMapLayer = false; }}>Done</button>
						{/if}
					</div>
					<div class="documents-column">
						{#each VOLUME.items.layers as layer}
						<div class="document-item">
							<div><p><Link href={layer.urls.resource} title={layer.title}>{layer.title}</Link></p></div>
							<button class="thumbnail-btn" on:click={() => {
								modalLyrUrl=layer.urls.cog;
								modalLyrExtent=layer.extent;
								getModal('modal-lyr-view').open();}}>
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
								{:else if userCanEdit}
								<ul>
									<li><Link href={layer.urls.georeference} title="edit georeferencing">edit georeferencing &rarr;</Link></li>
									<li><Link href={layer.urls.resource} title="edit georeferencing">downloads & web services &rarr;</Link></li>
								</ul>
								{/if}
								{#if settingKeyMapLayer}
								<select bind:value={layerCategoryLookup[layer.slug]} on:change={(e) => {updateAnnotationSet(e, layer.id)}}>
									{#each layerCategories as layerCat}
									<option value={layerCat.value}>{layerCat.label}</option>
									{/each}
								</select>
								{/if}
							</div>
						</div>
						{/each}
					</div>
				</div>
				{/if}
			</section>
			<section class="subsection" style="border-bottom:none;">
				<div class="subsection-title-bar">
					<button class="section-toggle-btn" on:click={() => toggleSection("nonmaps")} disabled={VOLUME.items.nonmaps.length == 0}
						title={sectionVis['nonmaps'] ? 'Collapse section' : 'Expand section'}>
						<ConditionalDoubleChevron down={sectionVis['nonmaps']} size="md" />
						<a id="georeferenced"><h3>Non-Map Content ({VOLUME.items.nonmaps.length})</h3></a>
					</button>
					<OpenModalButton modalId="modal-non-map" />
				</div>
				{#if sectionVis['nonmaps']}
				<div transition:slide>
					<div class="documents-column">
						{#each VOLUME.items.nonmaps as nonmap}
						<div class="document-item">
							<div><p><Link href={nonmap.urls.resource} title={nonmap.title}>{nonmap.title}</Link></p></div>
							<Link href={nonmap.urls.resource} external={true} title="go to detail page for this document" classes={["zoom-in"]}>
								<img src={nonmap.urls.thumbnail} alt={nonmap.title}>
							</Link>
							{#if userCanEdit}
							<div>
								<ul>
									<li><button class="btn-link" on:click={() => {postGeoref(nonmap.urls.georeference, "set-status", "prepared")}} title="set this document back to 'prepared' so it can be georeferenced">this <em>is</em> a map</button></li>
								</ul>
							</div>
							{/if}
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
			<button class="section-toggle-btn" on:click={() => toggleSection('multimask')} disabled={VOLUME.items.layers.length == 0}
				title={sectionVis['multimask'] ? 'Collapse section' : 'Expand section'}>
				<ConditionalDoubleChevron down={sectionVis['multimask']} size="md" />
				<a id="multimask"><h2>MultiMask</h2></a>
			</button>
			<OpenModalButton modalId="modal-multimask" />
		</div>
		{#if sectionVis['multimask']}
		<div transition:slide>
			{#if !USER.is_authenticated}
				<SigninReminder />
			{/if}
			<select class="item-select" bind:value={currentAnnotationSet}>
				{#each ANNOTATION_SETS as annoSet}
				{#if annoSet.annotations}
				<option value={annoSet.id}>{annoSet.name}</option>
				{/if}
				{/each}
			</select>
			<span>
				{#if annotationSetLookup[currentAnnotationSet].multimask_geojson}
				{annotationSetLookup[currentAnnotationSet].multimask_geojson.features.length}/{annotationSetLookup[currentAnnotationSet].annotations.length}
				{:else}
				0/{annotationSetLookup[currentAnnotationSet].annotations.length}
				{/if}
			</span>
			{#key currentAnnotationSet}
			<MultiMask ANNOTATION_SET={annotationSetLookup[currentAnnotationSet]}
				{CSRFTOKEN}
				DISABLED={!userCanEdit}
				{MAPBOX_API_KEY}
				{TITILER_HOST}
				{ROUTES}
				resetMosaic={resetMosaicPreview}
			 />
			{/key}
		</div>
		{/if}
	</section>
</main>
</IconContext>

<style>

#summary, #preview, #unprepared, #prepared, #georeferenced, #multimask {
  scroll-margin-top: 50px;
}

a.no-link {
	color:unset;
	text-decoration:unset;
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

button:disabled {
	cursor: default;
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

.button-list {
	display:flex;
	flex-direction:row;
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
