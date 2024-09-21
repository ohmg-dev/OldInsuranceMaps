<script>
import { slide } from 'svelte/transition';

import { makeTitilerXYZUrl } from "@lib/utils"

import ArrowRight from "phosphor-svelte/lib/ArrowRight";
import Question from "phosphor-svelte/lib/Question";
import Wrench from "phosphor-svelte/lib/Wrench";

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

import Modal, {getModal} from '@components/base/Modal.svelte';

import MapPreview from "@components/interfaces/MapPreview.svelte";
import SimpleViewer from '@components/interfaces/SimpleViewer.svelte';
import DownloadSectionModal from './modals/ItemDownloadSectionModal.svelte';
import MapDetails from './sections/MapDetails.svelte';
    import SigninReminder from '../layout/SigninReminder.svelte';
	import LoadingEllipsis from '../base/LoadingEllipsis.svelte';

export let CONTEXT;
export let MAP;
export let LOCALE;
export let SESSION_SUMMARY;
export let ANNOTATION_SETS;
export let ANNOTATION_SET_OPTIONS;

// console.log(MAP)
// console.log(ANNOTATION_SETS)

const sessionLocks = {"docs": {}, "regs": {}, "lyrs": {}}
$: {
	sessionLocks.docs = {}
	sessionLocks.regs = {}
	sessionLocks.lyrs = {}
	MAP.locks.forEach((lock) => {
		if (lock.target_type == "document" && MAP.item_lookup.unprepared.map(i => i.id).includes(lock.target_id)) {
			sessionLocks.docs[lock.target_id] = lock
		} else if (lock.target_type == "region" && MAP.item_lookup.prepared.map(i => i.id).includes(lock.target_id)) {
			sessionLocks.regs[lock.target_id] = lock
		} else if (lock.target_type == "layer" && MAP.item_lookup.georeferenced.map(i => i.id).includes(lock.target_id)) {
			sessionLocks.lyrs[lock.target_id] = lock
		}
	})
}
$: docsLockedCt = Object.keys(sessionLocks.docs).length
$: regsLockedCt = Object.keys(sessionLocks.regs).length
$: lyrsLockedCt = Object.keys(sessionLocks.lyrs).length

let multimaskKey = false;
function reinitMultimask() {
	multimaskKey = !multimaskKey
}

let previewKey = false;
function reinitPreview() {
	previewKey = !previewKey
}


let currentAnnotationSet = "main-content";
let annotationSetLookup = {};
let layerAnnotationLookup = {};
let origLayerAnnotationLookup = {};
let annotationsToUpdate = {};
function resetAnnotationSets(newAnnotationSets) {
	annotationSetLookup = {}
	layerAnnotationLookup = {}
	newAnnotationSets.forEach(function (annoSet) {
		annotationSetLookup[annoSet.id] = annoSet;
		annoSet.layers.forEach(function (anno) {
			layerAnnotationLookup[anno.slug] = annoSet.id;
			origLayerAnnotationLookup[anno.slug] = annoSet.id;
		})

		let mosaicUrl;
		let ohmUrl;
		if (annoSet.mosaic_json_url) {
			mosaicUrl = makeTitilerXYZUrl({
				host: CONTEXT.titiler_host,
				url: annoSet.mosaic_json_url
			})
			// make the OHM url here
			const mosaicUrlEncoded = makeTitilerXYZUrl({
				host: CONTEXT.titiler_host,
				url: annoSet.mosaic_json_url,
				doubleEncode: true
			})
			const ll = getCenter(annoSet.extent);
			ohmUrl = `https://www.openhistoricalmap.org/edit#map=16/${ll[1]}/${ll[0]}&background=custom:${mosaicUrlEncoded}`
		}
		if (annoSet.mosaic_cog_url) {
			mosaicUrl = makeTitilerXYZUrl({
				host: CONTEXT.titiler_host,
				url: annoSet.mosaic_cog_url
			})
			// make the OHM url here
			const mosaicUrlEncoded = makeTitilerXYZUrl({
				host: CONTEXT.titiler_host,
				url: annoSet.mosaic_cog_url,
				doubleEncode: true
			})
			const ll = getCenter(annoSet.extent);
			ohmUrl = `https://www.openhistoricalmap.org/edit#map=16/${ll[1]}/${ll[0]}&background=custom:${mosaicUrlEncoded}`
		}
		annoSet.mosaicUrl = mosaicUrl;
		annoSet.ohmUrl = ohmUrl;
	})
	ANNOTATION_SETS = newAnnotationSets;
	reinitMultimask();
	reinitPreview();
}
resetAnnotationSets(ANNOTATION_SETS)

let userCanEdit = false;
userCanEdit = CONTEXT.user.is_staff || (MAP.access == "any" && CONTEXT.user.is_authenticated) || (MAP.access == "sponsor" && MAP.sponsor == CONTEXT.user.username)

let currentIdentifier = MAP.identifier
function goToItem() {
	window.location = "/map/" + currentIdentifier
}
let currentDoc = "---";
function goToDocument() {
	window.location = "/resource/" + currentDoc
}

$: sheetsLoading = MAP.status == "initializing...";

let hash = window.location.hash.substr(1);

function checkForExistingMask(category, layerId) {

	const postData = JSON.stringify({
		operation: "check-for-existing-mask",
        resourceId: layerId,
        volumeId: MAP.identifier,
		categorySlug: category,
	})

	fetch(CONTEXT.urls.post_annotation_set, {
		method: 'POST',
		headers: CONTEXT.ohmg_post_headers,
		body: postData,
	})
	.then(response => response.json())
	.then(result => {
		if (result.status == "fail") {
			const msg = "This layer is already included in the multimask for its current classification, and that mask will be deleted if you continue with this change.<br>Set the layer back to its original classification to stop the change."
			if (confirm(msg)) {annotationsToUpdate[layerId] = category};
		} else {
			annotationsToUpdate[layerId] = category
		}
	});
}

function updateAnnotationSets() {

	const postData = JSON.stringify({
		operation: "update",
		volumeId: MAP.identifier,
		updateList: Object.entries(annotationsToUpdate)
	})

	fetch(CONTEXT.urls.post_annotation_set, {
		method: 'POST',
		headers: CONTEXT.ohmg_post_headers,
		body: postData,
	})
	.then(response => response.json())
	.then(result => {
		fetchAnnotationSets()
	});
}

const sectionVis = {
	"summary": (!hash && MAP.item_lookup.georeferenced.length == 0) || hash == "summary",
	"preview": (!hash && MAP.item_lookup.georeferenced.length > 0) || hash == "preview",
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

let intervalId;
function manageAutoReload(run) {
	if (run) {
		intervalId = setInterval(pollMapSummary, 4000);
	} else {
		clearInterval(intervalId)
	}
}
$: autoReload = sheetsLoading || MAP.locks.length > 0;
$: manageAutoReload(autoReload)

function pollMapSummary() {
	fetch(`${CONTEXT.urls.get_map}?map=${MAP.identifier}`, {
		headers: CONTEXT.ohmg_api_headers,
	})
	.then(response => response.json())
	.then(result => {
		if (
			MAP.item_lookup.unprepared.length != result.item_lookup.unprepared.length ||
			MAP.item_lookup.prepared.length != result.item_lookup.prepared.length ||
			MAP.item_lookup.georeferenced.length != result.item_lookup.georeferenced.length
		) {
			fetchAnnotationSets();
		}
		MAP = result;
	});
}

let refreshingLookups = false;
function postOperation(operation) {
	let indexLayerIds = [];
	if (operation == "refresh-lookups") {
		refreshingLookups = true;
	}
	const data = JSON.stringify({
		"operation": operation,
		"indexLayerIds": indexLayerIds,
	});
	fetch(MAP.urls.summary, {
		method: 'POST',
		headers: CONTEXT.ohmg_post_headers,
		body: data,
	})
	.then(response => response.json())
	.then(result => {
		// need to trigger a reinit of the MapPreview/Multimask components
		// with new annotationsets
		if (
			MAP.item_lookup.unprepared.length != result.item_lookup.unprepared.length ||
			MAP.item_lookup.prepared.length != result.item_lookup.prepared.length ||
			MAP.item_lookup.georeferenced.length != result.item_lookup.georeferenced.length
		) {
			fetchAnnotationSets();
		}
		MAP = result;
		sheetsLoading = MAP.status == "initializing...";
		if (operation == "refresh-lookups") {
			refreshingLookups = false;
		}
	});
}

function fetchAnnotationSets() {
	fetch(`${CONTEXT.urls.get_layersets}?map=${MAP.identifier}`, {
		headers: CONTEXT.ohmg_api_headers
	})
	.then(response => response.json())
	.then(result => {
		resetAnnotationSets(result)
	});
}

function postGeoref(url, operation, status) {
	const data = JSON.stringify({
		"operation": operation,
		"status": status,
	});
	fetch(url, {
		method: 'POST',
		headers: CONTEXT.ohmg_post_headers,
		body: data,
	})
	.then(response => response.json())
	.then(result => {
		pollMapSummary();
	});
}

let classifyingLayers = false;

let reinitModalMap = [{}]

let modalIsGeospatial = false;
let modalLyrUrl = "";
let modalExtent = []

</script>
<MapPreviewModal id={"modal-preview-map"} placeName={LOCALE.display_name} viewerUrl={MAP.urls.viewer}/>
<GeoreferenceOverviewModal id={"modal-georeference-overview"} />
<UnpreparedSectionModal id={'modal-unprepared'} />
<PreparedSectionModal id={"modal-prepared"} />
<GeoreferencedSectionModal id={"modal-georeferenced"} />
<MultiMaskModal id={"modal-multimask"} />
<NonMapContentModal id={"modal-non-map"} />
<GeoreferencePermissionsModal id={"modal-permissions"} user={CONTEXT.user.username} userCanEdit={userCanEdit} item={MAP} />
<Modal id={"modal-simple-viewer"} full={true}>
{#each reinitModalMap as key (key)}
	<SimpleViewer {CONTEXT} LAYER_URL={modalLyrUrl} EXTENT={modalExtent} GEOSPATIAL={modalIsGeospatial} />
{/each}
</Modal>
<main>
	<section class="breadcrumbs">
		{#each LOCALE.breadcrumbs as bc, n}
		<Link href="/{bc.slug}">{bc.name}</Link>{#if n != LOCALE.breadcrumbs.length-1}<ArrowRight size={12} />{/if}
		{/each}
		<ArrowRight size={12} />
		<select class="item-select" bind:value={currentIdentifier} on:change={goToItem}>
			{#each LOCALE.maps as m}
			<option value={m.identifier}>{m.title}</option>
			{/each}
		</select>
		<!--
		<ArrowRight size={12} />
		<select class="item-select" bind:value={currentDoc} on:change={goToDocument}>
			<option value="---" disabled>go to...</option>
			{#each MAP.sheets as s}
			<option value={s.doc_id}>page {s.sheet_no}</option>
			{/each}
		</select>
		-->
	</section>
	<TitleBar TITLE={MAP.title} VIEWER_LINK={MAP.urls.viewer}/>
	<section>
		<div class="section-title-bar">
			<button class="section-toggle-btn" on:click={() => {toggleSection('summary')}} title={sectionVis['summary'] ? 'Collapse section' : 'Expand section'}>
				<ConditionalDoubleChevron down={sectionVis['summary']} size="md"/>
				<a id="summary"><h2>Summary</h2></a>
			</button>
		</div>
		{#if sectionVis['summary']}
		<div style="margin-bottom:10px;" transition:slide>
			<MapDetails {CONTEXT} {MAP} {SESSION_SUMMARY} {ANNOTATION_SETS}/>
		</div>
		{/if}
	</section>
	<section>
		<div class="section-title-bar">
			<button class="section-toggle-btn" disabled={MAP.item_lookup.georeferenced.length == 0}
				on:click={() => {toggleSection('preview')}} title={sectionVis['preview'] ? 'Collapse section' : 'Expand section'}>
				<ConditionalDoubleChevron down={sectionVis['preview']} size="md"/>
				<a id="preview"><h2>Mosaic Preview ({MAP.item_lookup.georeferenced.length} layers)</h2></a>
			</button>
			<button class="is-icon-link" on:click={() => {getModal('modal-preview-map').open()}} ><Question /></button>
		</div>
		{#if sectionVis['preview']}
		<div class="section-content" transition:slide>
			{#key previewKey}
				<MapPreview {CONTEXT} {ANNOTATION_SETS} />
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
				<LoadingEllipsis />
			{/if}
			<div style="display:flex; align-items:center;">
				{#if CONTEXT.user.is_authenticated}
				<button class="is-icon-link" on:click={() => {postOperation("refresh-lookups")}} title="Regenerate summary (may take a moment)"><Wrench /></button>
				{/if}
				<button class="is-icon-link" on:click={() => {getModal('modal-georeference-overview').open()}} ><Question /></button>
			</div>
		</div>
		<div>
			<div style="display:flex; align-items:center;">
				<span>
					<em>
					{#if sheetsLoading}
					Loading sheet {MAP.progress.loaded_pages+1}/{MAP.progress.total_pages}... (you can safely leave this page).
					{:else if MAP.progress.loaded_pages == 0}
					No sheets loaded yet...
					{:else if MAP.progress.loaded_pages < MAP.progress.total_pages }
					{MAP.progress.loaded_pages} of {MAP.progress.total_pages} sheet{#if MAP.progress.total_pages != 1}s{/if} loaded (initial load unsuccessful. Click <strong>Load Volume</strong> to retry)
					{/if}
					</em>
				</span>
				{#if MAP.progress.loaded_pages < MAP.progress.total_pages && userCanEdit && !sheetsLoading}
					<button class="button is-primary is-small" style="margin-left:10px;" on:click={() => { postOperation("initialize"); sheetsLoading = true; }}>Load Volume ({MAP.progress.total_pages} sheet{#if MAP.progress.total_pages != 1}s{/if})</button>
				{/if}
			</div>
			{#if !CONTEXT.user.is_authenticated}
			<SigninReminder csrfToken={CONTEXT.csrf_token} />
			{/if}
			<section class="subsection">
				<div class="subsection-title-bar">
					<button class="section-toggle-btn" on:click={() => toggleSection('unprepared')} disabled={MAP.item_lookup.unprepared.length == 0}
						title={sectionVis['unprepared'] ? 'Collapse section' : 'Expand section'}>
						<ConditionalDoubleChevron down={sectionVis['unprepared']} size="md" />
						<a id="unprepared">
						<h3 style="margin-top:5px;">
							Unprepared ({MAP.item_lookup.unprepared.length})
							{#if docsLockedCt}
							&ndash; {docsLockedCt} locked...
							{/if}		
						</h3>
						</a>
					</button>
					<button class="is-icon-link" on:click={() => {getModal('modal-unprepared').open()}} ><Question /></button>
				</div>
				{#if sectionVis['unprepared']}
				<div transition:slide>
					<div class="documents-column">
						{#each MAP.item_lookup.unprepared as document}
						<div class="document-item">
							<div><p><Link href={document.urls.resource} title={document.title}>{MAP.document_page_type} {document.page_number}</Link></p></div>
							<button class="thumbnail-btn" on:click={() => {
								modalLyrUrl=document.urls.image;
								modalExtent=[0, -document.image_size[1], document.image_size[0], 0];
								modalIsGeospatial=false;
								getModal('modal-simple-viewer').open();
								reinitModalMap = [{}];
								}} >
								<img style="cursor:zoom-in"
									src={document.urls.thumbnail}
									alt={document.title}
									/>
							</button>
							<div>
								{#if sessionLocks.docs[document.id]}
								<ul style="text-align:center">
									<li><em>preparation in progress...</em></li>
									<li><em>user: {sessionLocks.docs[document.id].user.username}</em></li>
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
					<button class="section-toggle-btn" on:click={() => toggleSection("prepared")} disabled={MAP.item_lookup.prepared.length === 0} 
						title={sectionVis['prepared'] ? 'Collapse section' : 'Expand section'}>
						<ConditionalDoubleChevron down={sectionVis['prepared']} size="md" />
						<a id="prepared"><h3>
							Prepared ({MAP.item_lookup.prepared.length})
							{#if regsLockedCt}
							&ndash; {regsLockedCt} locked...
							{/if}
						</h3></a>
					</button>
					<button class="is-icon-link" on:click={() => {getModal('modal-prepared').open()}} ><Question /></button>
				</div>
				{#if sectionVis['prepared']}
				<div transition:slide>
					<div class="documents-column">
						{#each MAP.item_lookup.prepared as region}
						<div class="document-item">
							<div><p><Link href={region.urls.resource} title={region.title}>{region.title}</Link></p></div>
							<button class="thumbnail-btn" on:click={() => {
								modalLyrUrl=region.urls.image;
								modalExtent=[0, -region.image_size[1], region.image_size[0], 0];
								modalIsGeospatial=false;
								getModal('modal-simple-viewer').open();
								reinitModalMap = [{}];
								}} >
								<img style="cursor:zoom-in"
									src={region.urls.thumbnail}
									alt={region.title}
									/>
							</button>
							<div>
								{#if sessionLocks.regs[region.id]}
								<ul style="text-align:center">
									<li><em>georeferencing in progress...</em></li>
									<li>user: {sessionLocks.regs[region.id].user.username}</li>
								</ul>
								{:else if userCanEdit}
								<ul>
									<li><Link href={region.urls.georeference} title="georeference this document">georeference &rarr;</Link></li>
									<li><button class="is-text-link" title="click to move this document to the non-map section" on:click={() => {postGeoref(region.urls.georeference, "set-status", "nonmap")}}>set as non-map</button></li>
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
					<button class="section-toggle-btn" on:click={() => toggleSection("georeferenced")} disabled={MAP.item_lookup.georeferenced.length == 0}
						title={sectionVis['georeferenced'] ? 'Collapse section' : 'Expand section'}>
						<ConditionalDoubleChevron down={sectionVis['georeferenced']} size="md" />
						<a id="georeferenced">
						<h3>
							Georeferenced ({MAP.item_lookup.georeferenced.length})
							{#if lyrsLockedCt}
							&ndash; {lyrsLockedCt} locked...
							{/if}
						</h3>
						</a>
					</button>
					<button class="is-icon-link" on:click={() => {getModal('modal-georeferenced').open()}} ><Question /></button>
				</div>
				{#if sectionVis['georeferenced']}
				<div transition:slide>
					<div style="margin: 10px 0px;">
						{#if MAP.item_lookup.georeferenced.length > 0 && !classifyingLayers}
						<button class="button is-primary"
							on:click={() => classifyingLayers = !classifyingLayers}
							disabled={!CONTEXT.user.is_authenticated}
							title={!CONTEXT.user.is_authenticated ? 'You must be signed in to classify layers' : 'Click to enable layer classification'}
							>Classify Layers</button>
						{/if}
						{#if classifyingLayers}
						<button class="button is-success"
							disabled={Object.keys(annotationsToUpdate).length === 0} on:click={() => {
							updateAnnotationSets();
							classifyingLayers = false;
							annotationsToUpdate = {};
							reinitMultimask();
						}}>Save</button>
						<button class="button is-danger"
							on:click={() => {
							classifyingLayers = false;
							annotationsToUpdate = {};
							Object.keys(origLayerAnnotationLookup).forEach(function(k) {layerAnnotationLookup[k] = origLayerAnnotationLookup[k]})
						}}>Cancel</button>
						{/if}
					</div>
					<div class="documents-column">
						{#each MAP.item_lookup.georeferenced as layer}
						<div class="document-item">
							<div><p><Link href={layer.urls.resource} title={layer.title}>{layer.title}</Link></p></div>
							<button class="thumbnail-btn" on:click={() => {
								modalLyrUrl=layer.urls.cog;
								modalExtent=layer.extent;
								modalIsGeospatial=true;
								getModal('modal-simple-viewer').open();
								reinitModalMap = [{}]}}>
								<img style="cursor:zoom-in"
									src={layer.urls.thumbnail}
									alt={layer.title}
									>
							</button>
							<div>
								{#if sessionLocks.lyrs[layer.id]}
								<ul style="text-align:center">
									<li><em>session in progress...</em></li>
									<li>user: {sessionLocks.lyrs[layer.id].user.username}</li>
								</ul>
								{:else if userCanEdit}
								<ul>
									<li><Link href={layer.urls.georeference} title="edit georeferencing">edit georeferencing &rarr;</Link></li>
									<li><Link href={layer.urls.resource} title="edit georeferencing">downloads & web services &rarr;</Link></li>
								</ul>
								{/if}
								{#if classifyingLayers}
								<select bind:value={layerAnnotationLookup[layer.slug]} on:change={(e) => {
										checkForExistingMask(e.target.options[e.target.selectedIndex].value, layer.id)
										// updateAnnotationSet(e.target.options[e.target.selectedIndex].value, layer.id);
									}}>
									{#each ANNOTATION_SET_OPTIONS as annoOpt}
									<option value={annoOpt.slug}>{annoOpt.display_name}</option>
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
					<button class="section-toggle-btn" on:click={() => toggleSection("nonmaps")} disabled={MAP.item_lookup.nonmaps.length == 0}
						title={sectionVis['nonmaps'] ? 'Collapse section' : 'Expand section'}>
						<ConditionalDoubleChevron down={sectionVis['nonmaps']} size="md" />
						<a id="georeferenced"><h3>Non-Map Content ({MAP.item_lookup.nonmaps.length})</h3></a>
					</button>
					<button class="is-icon-link" on:click={() => {getModal('modal-non-map').open()}} ><Question /></button>
				</div>
				{#if sectionVis['nonmaps']}
				<div transition:slide>
					<div class="documents-column">
						{#each MAP.item_lookup.nonmaps as nonmap}
						<div class="document-item">
							<div><p><Link href={nonmap.urls.resource} title={nonmap.title}>{nonmap.title}</Link></p></div>
							<button class="thumbnail-btn" on:click={() => {
								modalLyrUrl=nonmap.urls.image;
								modalExtent=[0, -nonmap.image_size[1], nonmap.image_size[0], 0];
								modalIsGeospatial=false;
								getModal('modal-simple-viewer').open();
								reinitModalMap = [{}];
								}} >
								<img style="cursor:zoom-in"
									src={nonmap.urls.thumbnail}
									alt={nonmap.title}
									/>
							</button>
							{#if userCanEdit}
							<div>
								<ul>
									<li><button class="is-text-link" on:click={() => {postGeoref(nonmap.urls.georeference, "set-status", "prepared")}} title="click to set this document back to 'prepared' so it can be georeferenced">this <em>is</em> a map</button></li>
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
			<button class="section-toggle-btn" on:click={() => toggleSection('multimask')} disabled={MAP.item_lookup.georeferenced.length == 0}
				title={sectionVis['multimask'] ? 'Collapse section' : 'Expand section'}>
				<ConditionalDoubleChevron down={sectionVis['multimask']} size="md" />
				<a id="multimask"><h2>MultiMask</h2></a>
			</button>
			<button class="is-icon-link" on:click={() => {getModal('modal-multimask').open()}} ><Question /></button>
		</div>
		{#if sectionVis['multimask']}
		<div transition:slide>
			{#if !CONTEXT.user.is_authenticated}
				<SigninReminder csrfToken={CONTEXT.csrf_token} />
			{/if}
			<select class="item-select" bind:value={currentAnnotationSet} on:change={(e) => {
					reinitMultimask();
				}}>
				{#each ANNOTATION_SETS as annoSet}
				{#if annoSet.layers}
				<option value={annoSet.id}>{annoSet.name}</option>
				{/if}
				{/each}
			</select>
			<span>
				Masked layers: 
				{#if annotationSetLookup[currentAnnotationSet].multimask_geojson}
				{annotationSetLookup[currentAnnotationSet].multimask_geojson.features.length}/{annotationSetLookup[currentAnnotationSet].layers.length}
				{:else}
				0/{annotationSetLookup[currentAnnotationSet].layers.length}
				{/if}
			</span>
			<span>
				<em>&mdash; <strong>Important:</strong> Do not work on a multimask while there is other work in progress on this map (you could lose work).</em>
			</span>
			{#key multimaskKey}
			<MultiMask ANNOTATION_SET={annotationSetLookup[currentAnnotationSet]}
				{CONTEXT}
				DISABLED={!userCanEdit}
				resetMosaic={reinitPreview}
			 />
			{/key}
		</div>
		{/if}
	</section>
</main>

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
