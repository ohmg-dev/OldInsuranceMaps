<script>
import { slide } from 'svelte/transition';
import {TableSort} from 'svelte-tablesort';

export let USER_AUTHENTICATED;
export let CSRFTOKEN;

export let DOCUMENT_ID;
export let LAYER_ALTERNATE;
export let STATUS;
export let RESOURCE_TYPE;
export let URLS;
export let SPLIT_SUMMARY;
export let GEOREFERENCE_SESSIONS;
export let MASK_SESSIONS;
export let ACTION_HISTORY;

let showPrep = false;
let showGeoreference = false;
let showTrim = false;

let georeferenceBtnEnable = false;
let georeferenceBtnTitle = "Create Control Points";
let trimBtnEnable = false;
let trimBtnTitle = "Create Mask";

$: {
  switch(STATUS) {
    case "unprepared":
      showPrep = true;
      break
    case "splitting":
      showPrep = true;
      break;
    case "split":
      showPrep = true;
      break;
    case "prepared":
      showGeoreference = true;
      georeferenceBtnEnable = true;
      break;
    case "georeferenced":
      georeferenceBtnTitle = "Edit Control Points";
      georeferenceBtnEnable = true;
      trimBtnEnable = true;
      showTrim = true;
      break;
  }
}

function refresh() {
  fetch(URLS.refresh)
  .then(response => response.json())
  .then(result => {
    STATUS = result.STATUS;
    SPLIT_SUMMARY = result.SPLIT_SUMMARY;
    GEOREFERENCE_SESSIONS = result.GEOREFERENCE_SESSIONS;
    MASK_SESSIONS = result.MASK_SESSIONS;
  });
}
</script>

<main>
  <section style="border-bottom:1px solid lightgray;">
    <p><strong>Status:</strong> {STATUS}
      <button id="refresh-button" title="refresh overview" on:click={refresh}><i class="fa fa-refresh" /></button>
    </p>
    {#if RESOURCE_TYPE == "layer"}
    <p><a href={URLS.document_detail}>jump to document &rarr;</a></p>
    {:else if RESOURCE_TYPE == "document" && STATUS == "georeferenced"}
    <p><a href={URLS.layer_detail}>jump to layer &rarr;</a></p>
    {/if}
  </section>
  <section>
    <h4 on:click={() => showPrep = !showPrep}>1. Preparation <i class="fa fa-{showPrep == true ? 'chevron-down' : 'chevron-right'}"></i></h4>
    {#if showPrep}
    <div transition:slide>
      <button 
        title={georeferenceBtnTitle}
        disabled={!georeferenceBtnEnable}
        onclick="window.location.href='{URLS.split}'">
        <i class="fa fa-cut" />Split Document
      </button>
      <button 
        title={georeferenceBtnTitle}
        disabled={!georeferenceBtnEnable}
        onclick="window.location.href='{URLS.georeference}'">
        <i class="fa  fa-check-square-o" />No Split Needed
      </button>
    {#if STATUS == "unprepared"}
    <p>
      <a href="{URLS.split}">
      <i class="fa fa-cut"></i>
      prepare document</a>
    </p>
    <p>This document must be prepared before it can be georeferenced.</p>
    {:else if STATUS == "splitting"}
      <em><p>
        Splitting in progress...
      </p></em>
    {:else}
      <p>Prepared by 
        <a href={SPLIT_SUMMARY.split_by.profile}>{SPLIT_SUMMARY.split_by.name}</a>,
        {SPLIT_SUMMARY.date_str}
      </p>
      <p>Result:
        {#if SPLIT_SUMMARY.no_split_needed}
        No split needed.
        {:else if SPLIT_SUMMARY.child_docs.length > 0}
        Split into {SPLIT_SUMMARY.child_docs.length} new document{#if SPLIT_SUMMARY.child_docs.length != 1}s{/if},
        each must be georeferenced individually.
        {:else if SPLIT_SUMMARY.parent_doc}
        Split from <a href={SPLIT_SUMMARY.parent_doc.urls.progress_page}>{SPLIT_SUMMARY.parent_doc.title}</a>.
        {/if}
      </p>
      {#if SPLIT_SUMMARY.child_docs.length > 0}
      <div class="documents-column">
        {#each SPLIT_SUMMARY.child_docs as child}
        <div class="document-item">
          <div>
            {child.title}
          </div>
          <img src={child.urls.thumbnail} alt={child.title} title={child.title}>
          <div>
            <ul>
              <li><a href={child.urls.georeference} title="Georeference document">georeference &rarr;</a></li>
              <li><a href={child.urls.progress_page} title="View progress">progress overview &rarr;</a></li>
              <li><a href={child.urls.progress_page} title="Document detail">document detail &rarr;</a></li>
            </ul>
          </div>
        </div>
        {/each}
      </div>
      {/if}
    {/if}
    </div>
    {/if}
  </section>
  <section>
    <h4 on:click={() => showGeoreference = !showGeoreference}>2. Georeferencing <i class="fa fa-{showGeoreference == true ? 'chevron-down' : 'chevron-right'}"></i></h4>
    {#if showGeoreference}
    <div transition:slide>
      <button 
        title={georeferenceBtnTitle}
        disabled={!georeferenceBtnEnable}
        onclick="window.location.href='{URLS.georeference}'">
        <i class="fa fa-map-pin" />{georeferenceBtnTitle}
      </button>
    <p>
      {#if STATUS == "georeferencing"}
      <em><p>
        georeferencing in progress...
      </p></em>
      {/if}
    </p>
    <!-- {#if DOCUMENT.status == "georeferenced"} -->
      {#each GEOREFERENCE_SESSIONS as sesh, n}
      <p>
      {#if n == 0}Georeferenced by {:else}Updated by {/if}
        <a href={sesh.user.profile}>{sesh.user.name}</a>, {sesh.date_str} -
        <em>
        {sesh.gcps_ct} control point{#if sesh.gcps_ct != 1}s{/if} --
        {sesh.status}{#if sesh.status != "completed"}...{/if}
        </em>
      </p>
      {/each}
    {#if GEOREFERENCE_SESSIONS.length > 0}
    <table>
      <caption>Georeferencing Sessions</caption>
      <tr>
        <th style="max-width:300px;">Date</th>
        <th style="width:65px;">User</th>
        <th style="width:65px;">GCPs</th>
        <th>Status</th>
      </tr>
      {#each GEOREFERENCE_SESSIONS as sesh, n}
      <tr>
        <td>{sesh.date_str}</td>
        <td><a href={sesh.user.profile}>{sesh.user.name}</a></td>
        <td>{sesh.gcps_ct}</td>
        <td>{sesh.status}</td>
      </tr>
      {/each}
    </table>
    {/if}
    </div>
    {/if}
  </section>
  <section style="border-bottom:1px solid lightgray;">
    <h4 on:click={() => showTrim = !showTrim}>3. Trimming <i class="fa fa-{showTrim == true ? 'chevron-down' : 'chevron-right'}"></i></h4>
    {#if showTrim}
      <div transition:slide>
        <button 
        title={trimBtnTitle}
        disabled={!trimBtnEnable}
        onclick="window.location.href='{URLS.trim}'">
        <i class="fa fa-crop" />{trimBtnTitle}
      </button>
        {#each MASK_SESSIONS as sesh, n}
        <p>
        {#if n == 0}Trimmed by {:else}Adjusted by {/if}
          <a href={sesh.user.profile}>{sesh.user.name}</a>, {sesh.date_str} -
          {#if sesh.vertex_ct == 0}
          no mask
          {:else}
          {sesh.vertex_ct} vertices
          {/if}
        </p>
        {/each}
        </div>
      {/if}
  </section>
  
  {#if ACTION_HISTORY.length > 0}
  <section>
    <table>
      <caption>History</caption>
      <tr>
        <th style="max-width:300px;">Action Type</th>
        <th style="width:65px;">User</th>
        <th style="width:65px;">Date</th>
        <th>Details</th>
      </tr>
      {#each ACTION_HISTORY as action, n}
      <tr>
        <td>{action.type}</td>
        <td><a href={action.user.profile}>{action.user.name}</a></td>
        <td>{action.date}</td>
        <td>{action.details}</td>
      </tr>
      {/each}
    </table>
    
  </section>
  {/if}
</main>

<style>

main {
  display: flex;
  flex-direction: column;
}

i {
  width: 20px;
  text-align: center;
}

button:enabled {
  color: #fff;
  background-color: #2c689c;
  border-radius: 4px;
  border: 1px solid transparent;
}

button:hover:enabled {
  background-color: #204d74;
  border-color: #193b58;
}

section h4 i {
  font-size: .65em;
}
section h4 {
  color: #2c689c;
  cursor: pointer;
}

/* section .content {
  -o-transition: all 1s;
  -moz-transition: all 1s;
  -webkit-transition: all 1s;
  transition: all 1s;
} */

.section-content {
  -webkit-transition-property: height, visibility;
  transition-property: height, visibility;
  -webkit-transition-duration: 0.35s;
  transition-duration: 0.35s;
  -webkit-transition-timing-function: ease;
  transition-timing-function: ease;
}

/* table.tablesort {
	width:100%;
}

th.sortable, td {
	padding: 5px;
}

thead tr {
  background-color: #eaeaea;
}

tbody tr:nth-child(even){
  background-color: #f6f6f6;
}

tbody tr:nth-child(odd){
  background-color: #ffffff;
} */

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

</style>
