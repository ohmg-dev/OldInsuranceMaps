<script>
export let DOCUMENT;
export let LAYER;
export let USER_AUTHENTICATED;
export let SPLIT_SUMMARY;
export let GEOREFERENCE_SESSIONS;
export let MASK_SESSIONS;
export let CSRFTOKEN;

function refresh() {
  fetch(DOCUMENT.urls.progress_page, {
    method: 'POST',
    headers: {
          'Content-Type': 'application/json;charset=utf-8',
          'X-CSRFToken': CSRFTOKEN,
        },
  })
  .then(response => response.json())
  .then(result => {
    DOCUMENT = result.DOCUMENT;
    LAYER = result.LAYER;
    SPLIT_SUMMARY = result.SPLIT_SUMMARY;
    GEOREFERENCE_SESSIONS = result.GEOREFERENCE_SESSIONS;
    MASK_SESSIONS = result.MASK_SESSIONS;
  });
}

</script>

<main>
  <!-- <div class="title-bar">
    <h1>{DOCUMENT.title}</h1>
    
  </div> -->
  {#if !USER_AUTHENTICATED}
    <div class="signin-reminder">
      <p><em>
        <!-- svelte-ignore a11y-invalid-attribute -->
        <a href="#" data-toggle="modal" data-target="#SigninModal" role="button" >sign in</a> or
        <a href="/account/register">sign up</a> to work on this document
      </em></p>
    </div>
    {/if}
  <content>
    <section>
      <div>
        <h4 style="">Current status: {DOCUMENT.status} <button id="refresh-button" title="refresh overview" on:click={refresh}><i class="fa fa-refresh" /></button></h4>
      </div>
      <div>
        <h3>1. Preparation</h3>
        {#if DOCUMENT.status == "unprepared"}
        <p>
          <a href="{DOCUMENT.urls.split}">
          <i class="fa fa-cut"></i>
          prepare document</a>
        </p>
        <p>This document must be prepared before it can be georeferenced.</p>
        {:else if DOCUMENT.status == "splitting"}
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
      <div>
        <h3>2. Georeferencing</h3>
        <p>
          {#if DOCUMENT.status == "unprepared" || DOCUMENT.status == "splitting" || DOCUMENT.status == null}
          <span style="color:gray;">
            <i class="fa fa-map-pin"></i>georeference document
          </span>
          {:else if DOCUMENT.status == "georeferencing" }
          <em><p>
            Georeferencing in progress...
          </p></em>
          {:else}
          <a href="{DOCUMENT.urls.georeference}">
            <i class="fa fa-map-pin"></i>georeference document
          </a>
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
        <!-- {/if} -->
      </div>
      <div>
        <h3>3. Trimming</h3>
        <p>
          {#if DOCUMENT.status != "georeferenced"}
          <span style="color:gray;">
            <i class="fa fa-crop"></i>trim layer
          </span>
          {:else}
          <a href="{LAYER.urls.trim}">
            <i class="fa fa-crop"></i>trim layer
          </a>
          {/if}
        </p>
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
    </section>
    <section class="full-image-panel">
      <div>
        <img title={DOCUMENT.title} src="{DOCUMENT.urls.image}" alt="{DOCUMENT.title}"/>
        <h4><a href={DOCUMENT.urls.detail} alt="go to detail page">document detail &rarr;</h4>
      </div>
      {#if LAYER}
      <div>
        <img title={LAYER.title} src="{LAYER.urls.thumbnail}" alt="{LAYER.title}"/>
        <h4><a href={LAYER.urls.detail} alt="go to detail page">layer detail &rarr;</h4>
      </div>
      {/if}
    </section>
  </content>
</main>

<style>

  main {
    display: flex;
    flex-direction: column;
  }

  content {
    display: flex;
    flex-direction: row;
  }

  section {
    display: flex;
    flex-direction: column;
    width: 50%;
  }

  i {
    width: 20px;
    text-align: center;
  }

  .full-image-panel {
    text-align: center;
  }

  .full-image-panel img {
    display: inline-block;
    max-width: 250px;
    max-height: 250px;
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

</style>
