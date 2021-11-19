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
  <div class="title-bar">
    <h1>{DOCUMENT.title}</h1>
    {#if !USER_AUTHENTICATED}
    <div class="signin-reminder">
      <p><em>
        <a href="#" data-toggle="modal" data-target="#SigninModal" role="button" >sign in</a> or
        <a href="/account/register">sign up</a> to work on this document
      </em></p>
    </div>
    {/if}
  </div>
  <content>
    <section>
      <div>
        <h4 style="">Progress Page <button id="refresh-button" title="refresh overview" on:click={refresh}><i class="fa fa-refresh" /></button></h4>
      </div>
      <div>
        <h3>1. Preparation</h3>
        {#if DOCUMENT.status == "unprepared"}
        <p>This document must be prepared before it can be georeferenced.</p>
        <p>
          <a href="{DOCUMENT.urls.split}">
          <i class="fa fa-cut"></i>
          prepare document</a>
        </p>
        {:else if DOCUMENT.status == "splitting"}
          <em><p>
            currently processing...
          </p></em>
        {:else}
          <p>Evaluated by 
            <a href={SPLIT_SUMMARY.split_by.profile}>{SPLIT_SUMMARY.split_by.name}</a>,
            {SPLIT_SUMMARY.date_str} - 
            <em>
            {#if SPLIT_SUMMARY.no_split_needed}
            no split needed
            {:else if SPLIT_SUMMARY.child_docs.length > 0}
            split into {SPLIT_SUMMARY.child_docs.length} new document{#if SPLIT_SUMMARY.child_docs.length != 1}s{/if}
            {:else if SPLIT_SUMMARY.parent_doc}
            split from <a href={SPLIT_SUMMARY.parent_doc.urls.progress_page}>parent document</a>
            {/if}
            </em>
          </p>
          {#if SPLIT_SUMMARY.child_docs.length > 0}
          <div class="documents-column">
            {#each SPLIT_SUMMARY.child_docs as child}
            <div class="document-item">
              <img src={child.urls.thumbnail} alt={child.title} title={child.title}>
              <div>
                <ul>
                  <li><a href={child.urls.progress_page} title="view summary">view summary &rarr;</a></li>
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
        {#if DOCUMENT.status == "unprepared" || DOCUMENT.status == "splitting"}
        <p><em>n/a</em></p>
        {:else if SPLIT_SUMMARY.child_docs.length > 0}
        <p><em>each child document above must be georeferenced individually</em></p>
        {:else if DOCUMENT.status == "prepared"}
          {#if USER_AUTHENTICATED}
          <p>
            <a href="{DOCUMENT.urls.georeference}">
            <i class="fa fa-map-pin"></i>
            georeference document</a>
          </p>
          {:else}
          <p><em>you must be signed in to georeference this document</em></p>
          {/if}
        {:else}
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
          {#if DOCUMENT.status != "georeferencing"}
          <p>
            <a href="{DOCUMENT.urls.georeference}">
            <i class="fa fa-edit"></i>
            edit georeferencing</a>
          </p>
          {/if}
        <!-- {:else if DOCUMENT.status == "georeferencing"}
          <em><p>
            currently processing...
          </p></em> -->
        {/if}
      </div>
      <div>
        <h3>3. Trimming</h3>
        {#if DOCUMENT.status != "georeferenced"}
        <p><em>n/a</em></p>
        {:else if MASK_SESSIONS.length == 0}
        <p>
          <a href="{LAYER.urls.trim}">
          <i class="fa fa-crop"></i>
          trim layer</a>
        </p>
        {:else}
        {#each MASK_SESSIONS as sesh, n}
          <p>
          {#if n == 0}Trimmed by {:else}Adjusted by {/if}
            <a href={sesh.user.profile}>{sesh.user.name}</a>, {sesh.date_str} -
            <em>
            {#if sesh.vertex_ct == 0}
            no mask
            {:else}
            {sesh.vertex_ct} vertices
            {/if}
            </em>
          </p>
          {/each}
          <p>
            <a href="{LAYER.urls.trim}">
            <i class="fa fa-crop"></i>
            edit trimming</a>
          </p>
        {/if}
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
