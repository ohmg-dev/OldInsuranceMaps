<script>
import { slide } from 'svelte/transition';

import Scissors from "phosphor-svelte/lib/Scissors";
import CheckSquareOffset from "phosphor-svelte/lib/CheckSquareOffset";
import ArrowCounterClockwise from "phosphor-svelte/lib/ArrowCounterClockwise";
import ArrowRight from "phosphor-svelte/lib/ArrowRight";
import MapPin from "phosphor-svelte/lib/MapPin";
import Trash from "phosphor-svelte/lib/Trash";

import 'ol/ol.css';

import {getCenter} from 'ol/extent';

import Link from '@components/base/Link.svelte';
import TitleBar from '@components/layout/TitleBar.svelte';
import SessionList from '@components/lists/SessionList.svelte';
import SimpleViewer from '@components/interfaces/SimpleViewer.svelte';
import ConditionalDoubleChevron from './buttons/ConditionalDoubleChevron.svelte';
import ToolUIButton from '@components/base/ToolUIButton.svelte';

import ResourceDetails from './sections/ResourceDetails.svelte';

import { makeTitilerXYZUrl } from '@lib/utils';

export let CONTEXT;
export let RESOURCE;
export let VOLUME;
export let SPLIT_SUMMARY;
export let GEOREFERENCE_SUMMARY;

const EXTENT = RESOURCE.type == "layer" ? RESOURCE.extent : [0, -RESOURCE.image_size[1], RESOURCE.image_size[0], 0]
const LAYER_URL = RESOURCE.type == "layer" ? RESOURCE.urls.cog : RESOURCE.urls.image

let ll;
let doubleEncodedXYZUrl;
let viewerUrl;
let xyzUrl;
let ohmUrl;
if (RESOURCE.type == "layer") {
  xyzUrl = makeTitilerXYZUrl({
    host: CONTEXT.titiler_host,
    url: RESOURCE.urls.cog,
  });
  doubleEncodedXYZUrl = makeTitilerXYZUrl({
    host: CONTEXT.titiler_host,
    url: RESOURCE.urls.cog,
    doubleEncode: true,
  });
  ll = getCenter(RESOURCE.extent);
  viewerUrl = `/viewer/${VOLUME.locale.slug}/?${VOLUME.identifier}=100#/center/${ll[0]},${ll[1]}/zoom/18`;
} else if (RESOURCE.layer){
  xyzUrl = makeTitilerXYZUrl({
    host: CONTEXT.titiler_host,
    url: RESOURCE.layer.urls.cog,
    doubleEncode: true,
  });
  doubleEncodedXYZUrl = makeTitilerXYZUrl({
    host: CONTEXT.titiler_host,
    url: RESOURCE.layer.urls.cog,
    doubleEncode: true,
  });
  ll = getCenter(RESOURCE.layer.extent);
}
if (doubleEncodedXYZUrl && ll) {
  ohmUrl = `https://www.openhistoricalmap.org/edit#map=16/${ll[1]}/${ll[0]}&background=custom:${doubleEncodedXYZUrl}`
}

const sectionVis = {
  "summary": true,
  "preview": true,
	"prep": true,
	"georef": true,
	"history": true,
}

function toggleSection(sectionId) {
	sectionVis[sectionId] = !sectionVis[sectionId];
}

let splitBtnEnabled = false;
let noSplitBtnEnabled = false;
let undoBtnTitle = "Undo this determination";

let georeferenceBtnEnable = false;
let georeferenceBtnTitle = "Create Control Points";

let splitNeeded;
let undoBtnEnabled;
let processing;

// pretty clumsy but works for now. for SessionList make joined params from ids
let filterParamsList = ['sort=oldest_first']
if (RESOURCE.type === 'document') {
  filterParamsList.push(`resource=${RESOURCE.id}`)
  if (RESOURCE.layer) {
    filterParamsList.push(`resource=${RESOURCE.layer.id}`)
  }
} else if (RESOURCE.type === 'layer') {
  filterParamsList.push(`resource=${RESOURCE.id}`)
  filterParamsList.push(`resource=${RESOURCE.document.id}`)
}
const filterParam = filterParamsList.join('&')

$: {
  processing = RESOURCE.status == "splitting" || RESOURCE.status == "georeferencing"
  splitNeeded = SPLIT_SUMMARY ? SPLIT_SUMMARY.split_needed : "unknown";
  undoBtnEnabled = SPLIT_SUMMARY ? SPLIT_SUMMARY.allow_reset : false;
  switch(RESOURCE.status) {
    case "unprepared":
      if (CONTEXT.user.is_authenticated) {
        splitBtnEnabled = true;
        noSplitBtnEnabled = true;
      }
      sectionVis['georef'] = false;
      sectionVis['download'] = false;
      georeferenceBtnEnable = false;
      break
    case "splitting":
      undoBtnEnabled = false;
      break;
    case "prepared":
      splitBtnEnabled = false;
      noSplitBtnEnabled = false;
      georeferenceBtnEnable = true;
      break;
    case "georeferenced":
      sectionVis['georef'] = false;
      georeferenceBtnEnable = true;
      georeferenceBtnTitle = "Edit Control Points";
      break;
  }
}

function setSplit(operation) {

  let data = JSON.stringify({
    "operation": operation,
  });

  fetch(RESOURCE.urls.split, {
      method: 'POST',
      headers: CONTEXT.ohmg_post_headers,
      body: data,
    })
    .then(response => response.json())
    .then(result => {
      window.location = window.location
    });
}

function unGeoreference() {

  let data = JSON.stringify({
    "operation": "ungeoreference",
  });

  fetch(RESOURCE.urls.georeference, {
      method: 'POST',
      headers: CONTEXT.ohmg_post_headers,
      body: data,
    })
    .then(response => response.json())
    .then(result => {
      if (RESOURCE.type == "layer") {
        window.location = RESOURCE.document.urls.resource
      } else {
        window.location = window.location
      }
    });
}

const iconLinks = [
  {
    visible: true,
    enabled: RESOURCE.type == "layer",
    iconClass: 'document',
    alt: RESOURCE.document ? 'Go to document: ' + RESOURCE.document.title : '',
    url: RESOURCE.document ? RESOURCE.document.urls.resource : '',
  },
  {
    visible: true,
    enabled: RESOURCE.type == "document" && RESOURCE.layer,
    iconClass: 'layer',
    alt: RESOURCE.layer ? 'Go to layer: ' + RESOURCE.layer.title : 'Layer not yet made',
    url: RESOURCE.layer ? RESOURCE.layer.urls.resource : '',
  },
  {
    visible: true,
    enabled: true,
    iconClass: 'volume',
    alt: 'Go to volume: ' + VOLUME.title,
    url: VOLUME.urls.summary,
  },
  {
    visible: true,
    enabled: RESOURCE.type == "layer",
    iconClass: 'camera',
    alt: 'Open in main viewer',
    url: viewerUrl,
  }
]
let reinitMap = [{}]

let currentIdentifier = VOLUME.identifier
function goToItem() {
	window.location = "/map/" + currentIdentifier
}
let currentDoc = RESOURCE.id;
function goToDocument() {
	window.location = "/resource/" + currentDoc
}
</script>

<main>
  <section class="breadcrumbs">
		{#each VOLUME.locale.breadcrumbs as bc, n}
		<Link href="/{bc.slug}">{bc.name}</Link>{#if n != VOLUME.locale.breadcrumbs.length-1}<ArrowRight size={12} />{/if}
		{/each}
		<ArrowRight size={12} />
    <Link href={VOLUME.urls.summary}>{VOLUME.year}</Link>
    <!--
		<ArrowRight size={12} />
		<select class="item-select" bind:value={currentDoc} on:change={goToDocument}>
			<option value="---" disabled>go to...</option>
			{#each VOLUME.sheets as s}
			<option value={s.doc_id}>page {s.sheet_no}</option>
			{/each}
		</select>-->
	</section>
  <TitleBar TITLE={RESOURCE.title} ICON_LINKS={iconLinks} />
  <section>
    <button class="section-toggle-btn" on:click={() => toggleSection('summary')} disabled={false}>
      <ConditionalDoubleChevron down={sectionVis['summary']} size="md" />
        <h2>Summary</h2>
    </button>
    {#if sectionVis['summary']}
    <div transition:slide>
      <ResourceDetails {CONTEXT} {RESOURCE} />
    </div>
    {/if}
  </section>
  <section>
    <button class="section-toggle-btn" on:click={() => toggleSection('preview')} disabled={false}>
      <ConditionalDoubleChevron down={sectionVis['preview']} size="md" />
        <h2>{RESOURCE.type == "document" ? "Document" : "Layer"} Preview</h2>
    </button>
    {#if sectionVis['preview']}
    <div transition:slide>
      <div id="map-panel">
        {#each reinitMap as key (key)}
        <SimpleViewer {CONTEXT} {LAYER_URL} {EXTENT} GEOSPATIAL={RESOURCE.type == "layer"} />
        {/each}
      </div>
    </div>
    {/if}
  </section>
  <section>
    <button class="section-toggle-btn" on:click={() => toggleSection('prep')} disabled={false}>
      <ConditionalDoubleChevron down={sectionVis['prep']} size="md" />
        <h2>Preparation</h2>
    </button>
    {#if sectionVis['prep']}
    <div transition:slide>
      <div class="control-btn-group">
        <ToolUIButton
          onlyIcon={false}
          title="Split this document"
          disabled={!splitBtnEnabled}
          action={() => {window.location.href='{RESOURCE.urls.split}'}}>
          <!-- class="control-btn{splitNeeded == true ? ' btn-chosen': ''}"> -->
          <Scissors /> Split
        </ToolUIButton>
        <ToolUIButton
          onlyIcon={false}
          title="This document does not need to be split"
          disabled={!noSplitBtnEnabled}
          action={() => {setSplit("no_split")}}>
          <!-- class="control-btn{splitNeeded == false ? ' btn-chosen': ''}"> -->
          <CheckSquareOffset /> No split needed
        </ToolUIButton>
        <!-- DISABLE UNDO OPERATIONS TEMPORARILY
        {#if CONTEXT.user.is_authenticated}
        <ToolUIButton
          title={undoBtnTitle}
          disabled={!undoBtnEnabled}
          action={() => {setSplit("undo")}}>
          <ArrowCounterClockwise />
        </ToolUIButton>
        {/if}
        -->
      </div>
      <div class="section-body">
        {#if SPLIT_SUMMARY}
          <p>{SPLIT_SUMMARY.date_str} by 
            <Link href={SPLIT_SUMMARY.user.profile}>{SPLIT_SUMMARY.user.name}</Link>:
            {#if !SPLIT_SUMMARY.split_needed}
            No split needed.
            {:else if SPLIT_SUMMARY.child_docs.length > 0}
            Split into {SPLIT_SUMMARY.child_docs.length} new document{#if SPLIT_SUMMARY.child_docs.length != 1}s{/if},
            each must be georeferenced individually.
            {:else if SPLIT_SUMMARY.parent_doc}
            Split from <Link href={SPLIT_SUMMARY.parent_doc.urls.resource}>{SPLIT_SUMMARY.parent_doc.title}</Link>.
            {/if}
          </p>
          {#if SPLIT_SUMMARY.child_docs.length > 0}
          <div class="documents-column">
            {#each SPLIT_SUMMARY.child_docs as child}
            <div class="document-item">
              <div>
                <Link href={child.urls.resource} title="{child.title}">{child.title.split(" | ")[1]}</Link>
              </div>
              <img src={child.urls.thumbnail} alt={child.title} title={child.title}>
              <div>
                <ul>
                  <li><strong>Status:</strong> {child.status}</li>
                  <li><Link href={child.urls.georeference} title="Document detail">
                    {#if child.status == "georeferenced"}edit georeferencing &rarr;
                    {:else}georeference &rarr;
                    {/if}
                  </Link></li>
                </ul>
              </div>
            </div>
            {/each}
          </div>
          {/if}
        {/if}
      </div>
    </div>
    {/if}
  </section>
  <section>
    <button class="section-toggle-btn" on:click={() => toggleSection('georef')} disabled={false}>
      <ConditionalDoubleChevron down={sectionVis['georef']} size="md" />
        <h2>Georeferencing</h2>
    </button>
    {#if sectionVis['georef']}
    <div transition:slide>
      <div class="control-btn-group">
        <ToolUIButton
          onlyIcon= {false}
          title={georeferenceBtnTitle}
          disabled={!georeferenceBtnEnable}
          action={() => {window.location.href=RESOURCE.urls.georeference}}>
          <MapPin />{georeferenceBtnTitle}
        </ToolUIButton>
        <!-- DISABLE UNDO OPERATIONS TEMPORARILY
        {#if CONTEXT.user.is_authenticated && CONTEXT.user.is_staff}
        <ToolUIButton
          title="Remove all georeferencing for this resource"
          disabled={RESOURCE.status != "georeferenced"}
          action={unGeoreference}>
          <Trash />
        </ToolUIButton>
        {/if}
        -->
      </div>
      <div class="section-body">
        {#if GEOREFERENCE_SUMMARY.gcp_geojson}
        <table>
          <caption>{GEOREFERENCE_SUMMARY.gcp_geojson.features.length} Control Points</caption>
          <tr>
            <th>X</th>
            <th>Y</th>
            <th>Lng</th>
            <th>Lat</th>
            <th>User</th>
            <th>Note</th>
          </tr>
          {#each GEOREFERENCE_SUMMARY.gcp_geojson.features as feat}
          <tr>
            <td class="coord-digit">{feat.properties.image[0]}</td>
            <td class="coord-digit">{feat.properties.image[1]}</td>
            <td class="coord-digit">{Math.round(feat.geometry.coordinates[0]*1000000)/1000000}</td>
            <td class="coord-digit">{Math.round(feat.geometry.coordinates[1]*1000000)/1000000}</td>
            <td>{feat.properties.username}</td>
            <td>{feat.properties.note != null ? feat.properties.note : "--"}</td>
          </tr>
          {/each}
        </table>
        {/if}
      </div>
    </div>
    {/if}
  </section>
  <section style="border-bottom:none;">
    <button class="section-toggle-btn" on:click={() => toggleSection('history')} disabled={false}>
      <ConditionalDoubleChevron down={sectionVis['history']} size="md" />
        <h2>Session History</h2>
    </button>
    {#if sectionVis['history']}
    <div transition:slide>
      <SessionList {CONTEXT} FILTER_PARAM={filterParam} showResource={false} paginate={false} limit={"0"}/>
    </div>
    {/if}
  </section>
</main>

<style>

#map-panel {
  width: 100%;
  height: 500px;
}

section {
	border-bottom: 1px solid rgb(149, 149, 149);
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

button.section-toggle-btn {
	text-decoration: none;
}

button.section-toggle-btn:hover {
	color: #1b4060;
}

button.section-toggle-btn:disabled {
	color: grey;
}

/* button.section-toggle-btn:disabled > a {
	color: grey;
} */

.section-body {
  margin: 10px 0px;
}

table {
	min-width:100%;
  border: 1px solid #ddd;
}

table caption {
  color: #333;
  text-align: center;
}

th, td {
	padding: 4px;
}

th {
  font-variant: small-caps;
  font-size: .85em;
}

tr:nth-child(even) {
  background-color: #f6f6f6;
}

tr:nth-child(odd) {
  background-color: #ffffff;
}

.coord-digit {
  font-family: Menlo, monospace;
  font-size: .85em;
}

.documents-column {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 20px;
}

.document-item {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border: 1px solid gray;
  background: white;
  max-width: 45%;
  /* height: 150px; */ 

}

.document-item img {
  margin: 10px;
  max-height: 200px;
  max-width: 200px;

}

.document-item div:first-child {
  text-align: center;
}

.document-item div:first-child, .document-item div:last-child {
  padding: 5px;
  background: #e6e6e6;
  width: 100%;
}

.document-item ul {
  list-style-type: none;
  padding: 0;
}

section.breadcrumbs {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	padding: 5px 0px;
	font-size: .95em;
	border-bottom: none;
}

/* select.item-select {
	margin-right: 3px;
	color: #2c689c;
	cursor: pointer;
} */

:global(section.breadcrumbs svg) {
	margin: 0px 2px;
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
