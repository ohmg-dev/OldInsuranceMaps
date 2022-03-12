<script>
import { slide } from 'svelte/transition';

export let USER_AUTHENTICATED;
export let CSRFTOKEN;
export let STATUS;
export let RESOURCE_TYPE;
export let URLS;
export let SPLIT_SUMMARY;
export let GEOREFERENCE_SUMMARY;
export let TRIM_SUMMARY;
export let SESSION_HISTORY;

let showPrep = false;
let showGeoreference = false;
let showTrim = false;

let splitBtnEnabled = false;
let noSplitBtnEnabled = false;
let undoBtnTitle = "Undo this determination";

let georeferenceBtnEnable = false;
let georeferenceBtnTitle = "Create Control Points";
let trimBtnEnable = false;
let trimBtnTitle = "Create Mask";

let splitNeeded;
let undoBtnEnabled;
let processing;

$: {
  processing = STATUS == "splitting" || STATUS == "georeferencing" || STATUS == "trimming"
  splitNeeded = SPLIT_SUMMARY ? SPLIT_SUMMARY.split_needed : "unknown";
  undoBtnEnabled = SPLIT_SUMMARY ? SPLIT_SUMMARY.allow_reset : false;
  switch(STATUS) {
    case "unprepared":
      showPrep = true;
      if (USER_AUTHENTICATED) {
        splitBtnEnabled = true;
        noSplitBtnEnabled = true;
      }
      showGeoreference = false;
      georeferenceBtnEnable = false;
      showTrim = false;
      trimBtnEnable = false;
      break
    case "splitting":
      undoBtnEnabled = false;
      break;
    case "split":
      showPrep = true;
      break;
    case "prepared":
      splitBtnEnabled = false;
      noSplitBtnEnabled = false;
      showGeoreference = true;
      georeferenceBtnEnable = true;
      break;
    case "georeferenced":
      georeferenceBtnEnable = true;
      georeferenceBtnTitle = "Edit Control Points";
      trimBtnEnable = true;
      showTrim = true;
      break;
    case "trimmed":
      georeferenceBtnEnable = true;
      georeferenceBtnTitle = "Edit Control Points";
      trimBtnTitle = "Edit Mask";
      trimBtnEnable = true;
      break;
  }
}

function refresh() {
  fetch(URLS.refresh)
  .then(response => response.json())
  .then(result => {
    STATUS = result.STATUS;
    SPLIT_SUMMARY = result.SPLIT_SUMMARY;
    GEOREFERENCE_SUMMARY = result.GEOREFERENCE_SUMMARY;
    TRIM_SUMMARY = result.TRIM_SUMMARY;
    SESSION_HISTORY = result.SESSION_HISTORY;
  });
}

function setSplit(operation) {

  let data = JSON.stringify({
    "operation": operation,
  });

  fetch(URLS.split, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json;charset=utf-8',
        'X-CSRFToken': CSRFTOKEN,
      },
      body: data,
    })
    .then(response => response.json())
    .then(result => {
      refresh()
    });
}
</script>

<main>
  <section >
    <p><strong>Status:</strong> {STATUS}{processing ? " in progress..." : ""}
      <button id="refresh-button" title="refresh overview" on:click={refresh}><i class="fa fa-refresh" /></button>
    </p>
    {#if RESOURCE_TYPE == "layer"}
    <p><a href={URLS.document_detail}>jump to document &rarr;</a></p>
    {:else if RESOURCE_TYPE == "document" && STATUS == "georeferenced"}
    <p><a href={URLS.layer_detail}>jump to layer &rarr;</a></p>
    {/if}
  </section>
  <section>
    <h4 class="expandable" on:click={() => showPrep = !showPrep}>1. Preparation <i class="fa fa-{showPrep == true ? 'chevron-down' : 'chevron-right'}"></i></h4>
    {#if showPrep}
    <div transition:slide>
      <div class="section-btn-row">
        <button 
          title="Click to split this document"
          disabled={!splitBtnEnabled}
          onclick="window.location.href='{URLS.split}'"
          class="{splitNeeded == true ? 'btn-chosen': ''}">
          <i class="fa fa-cut" />Split Document
        </button>
        <button 
          title="Click to set this document as prepared"
          disabled={!noSplitBtnEnabled}
          on:click={() => {setSplit("no_split")}}
          class="{splitNeeded == false ? 'btn-chosen': ''}">
          <i class="fa fa-check-square-o" />No Split Needed
        </button>
        <button 
          title={undoBtnTitle}
          disabled={!undoBtnEnabled}
          on:click={() => {setSplit("undo")}}>
          <i class="fa fa-undo" />Undo
        </button>
      </div>
      <div class="section-body">
        {#if SPLIT_SUMMARY}
          <p>{SPLIT_SUMMARY.date_str} by 
            <a href={SPLIT_SUMMARY.user.profile}>{SPLIT_SUMMARY.user.name}</a>:
            {#if !SPLIT_SUMMARY.split_needed}
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
                  <li><strong>Status:</strong> {child.status}</li>
                  <li><a href={child.urls.progress_page} title="Document detail">document detail &rarr;</a></li>
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
    <h4 class="expandable" on:click={() => showGeoreference = !showGeoreference}>2. Georeferencing <i class="fa fa-{showGeoreference == true ? 'chevron-down' : 'chevron-right'}"></i></h4>
    {#if showGeoreference}
    <div transition:slide>
      <div class="section-btn-row">
        <button 
          title={georeferenceBtnTitle}
          disabled={!georeferenceBtnEnable}
          onclick="window.location.href='{URLS.georeference}'">
          <i class="fa fa-map-pin" />{georeferenceBtnTitle}
        </button>
      </div>
      <div class="section-body">
        {#if GEOREFERENCE_SUMMARY.gcp_geojson}
        <table>
          <caption>{GEOREFERENCE_SUMMARY.gcp_geojson.features.length} Control Points</caption>
          <tr>
            <th>Pixel X</th>
            <th>Pixel Y</th>
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
            <td class="coord-digit">{Math.round(feat.geometry.coordinates[0]*1000000)/1000000}</td>
            <td>{feat.properties.username}</td>
            <td>{feat.properties.note != null ? feat.properties.note : ""}</td>
          </tr>
          {/each}
        </table>
        {/if}
        {#if GEOREFERENCE_SUMMARY.sessions.length > 0}
        <table>
          <caption>Georeferencing Sessions</caption>
          <tr>
            <th>Date</th>
            <th>User</th>
            <th>GCPs</th>
            <th>Status</th>
          </tr>
          {#each GEOREFERENCE_SUMMARY.sessions as sesh, n}
          <tr>
            <td>{sesh.datetime}</td>
            <td><a href={sesh.user.profile}>{sesh.user.name}</a></td>
            <td>{sesh.gcps_ct}</td>
            <td>{sesh.status}</td>
          </tr>
          {/each}
        </table>
        {/if}
      </div>
    </div>
    {/if}
  </section>
  <section>
    <h4 class="expandable" on:click={() => showTrim = !showTrim}>3. Trimming <i class="fa fa-{showTrim == true ? 'chevron-down' : 'chevron-right'}"></i></h4>
    {#if showTrim}
      <div transition:slide>
        <div class="section-btn-row">
          <button 
            title={trimBtnTitle}
            disabled={!trimBtnEnable}
            onclick="window.location.href='{URLS.trim}'">
            <i class="fa fa-crop" />{trimBtnTitle}
          </button>
        </div>
        <div class="section-body">
          {#if TRIM_SUMMARY.sessions.length > 0}
          <table>
            <caption>Trimming Sessions</caption>
            <tr>
              <th>Date</th>
              <th>User</th>
              <th>Vertices</th>
            </tr>
            {#each TRIM_SUMMARY.sessions as sesh}
            <tr>
              <td>{sesh.datetime}</td>
              <td><a href={sesh.user.profile}>{sesh.user.name}</a></td>
              <td>{sesh.vertex_ct}</td>
            </tr>
            {/each}
          </table>
          {/if}
        </div>
      </div>
    {/if}
  </section>
  {#if SESSION_HISTORY.length > 0}
  <section>
    <table>
      <caption><h4>Full History</h4></caption>
      <tr>
        <th>#</th>
        <th>Action</th>
        <th>User</th>
        <th>Stage</th>
        <th>Status</th>
        <th>Date</th>
        <th>Time</th>
        <th>Details</th>
      </tr>
      {#each SESSION_HISTORY as session}
      <tr>
        <td>{session.id}</td>
        <td>{session.type}</td>
        <td><a href={session.user.profile}>{session.user.name}</a></td>
        <td>{session.stage}</td>
        <td>{session.status}</td>
        <td>{session.date_run_date != null ? session.date_run_date : '--'}</td>
        <td>{session.date_run_time != null ? session.date_run_time : '--'}</td>
        <td>{session.note != null ? session.note : '--'}</td>
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
  color: white;
  background-color: #2c689c;
  border-radius: 4px;
  border: 1px solid transparent;
}

button:hover:enabled {
  color: white;
  background-color: #204d74;
  border-color: #193b58;
}

.btn-chosen {
  border: 2px solid #2c2c2c;
  border-radius: 4px;
}

section {
  border-bottom: 1px dashed #ddd;
}

section h4 i {
  font-size: .65em;
}
section h4.expandable {
  color: #2c689c;
  cursor: pointer;
}

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
