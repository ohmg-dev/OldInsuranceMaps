<script>
  import { slide } from 'svelte/transition';

  import Wrench from 'phosphor-svelte/lib/Wrench';

  import { getCenter } from 'ol/extent';

  import MultiMask from './interfaces/MultiMask.svelte';
  import ConditionalDoubleChevron from './buttons/ConditionalDoubleChevron.svelte';
  import InfoModalButton from './buttons/InfoModalButton.svelte';

  import Modal, { getModal } from './modals/BaseModal.svelte';
  import MapPreviewModal from './modals/MapPreviewModal.svelte';
  import GeoreferenceOverviewModal from './modals/GeoreferenceOverviewModal.svelte';
  import UnpreparedSectionModal from './modals/UnpreparedSectionModal.svelte';
  import PreparedSectionModal from './modals/PreparedSectionModal.svelte';
  import GeoreferencedSectionModal from './modals/GeoreferencedSectionModal.svelte';
  import MultiMaskModal from './modals/MultiMaskModal.svelte';
  import NonMapContentModal from './modals/NonMapContentModal.svelte';
  import GeoreferencePermissionsModal from './modals/GeoreferencePermissionsModal.svelte';
  import ConfirmNoSplitModal from './modals/ConfirmNoSplitModal.svelte';
  import ConfirmBulkNoSplitModal from './modals/ConfirmBulkNoSplitModal.svelte';
  import ConfirmUngeoreferenceModal from './modals/ConfirmUngeoreferenceModal.svelte';

  import MapPreview from './interfaces/MapPreview.svelte';
  import BasicDocViewer from './interfaces/BasicDocViewer.svelte';
  import BasicLayerViewer from './interfaces/BasicLayerViewer.svelte';
  import MapDetails from './overviews/sections/MapDetails.svelte';
  import SigninReminder from './common/SigninReminder.svelte';
  import LoadingEllipsis from './common/LoadingEllipsis.svelte';
  import LoadingMask from './common/LoadingMask.svelte';

  import MapBreadcrumbs from './breadcrumbs/MapBreadcrumbs.svelte';

  import UnpreparedCard from './cards/UnpreparedCard.svelte';
  import PreparedCard from './cards/PreparedCard.svelte';
  import LayerCard from './cards/LayerCard.svelte';
  import SkippedCard from './cards/SkippedCard.svelte';
  import NonMapCard from './cards/NonMapCard.svelte';

  import { getFromAPI, submitPostRequest } from '../lib/requests';
  import { makeTitilerXYZUrl } from '../lib/utils';
  import SkippedSectionHelpModal from './modals/SkippedSectionHelpModal.svelte';

  export let CONTEXT;
  export let MAP;
  export let LOCALE;
  export let SESSION_SUMMARY;
  export let LAYERSETS;
  export let LAYERSET_CATEGORIES;
  export let userFilterItems;

  const sessionLocks = { docs: {}, regs: {}, lyrs: {} };
  $: {
    sessionLocks.docs = {};
    sessionLocks.regs = {};
    sessionLocks.lyrs = {};
    MAP.locks.forEach((lock) => {
      if (lock.target_type == 'document' && MAP.item_lookup.unprepared.map((i) => i.id).includes(lock.target_id)) {
        sessionLocks.docs[lock.target_id] = lock;
      } else if (lock.target_type == 'region' && MAP.item_lookup.prepared.map((i) => i.id).includes(lock.target_id)) {
        sessionLocks.regs[lock.target_id] = lock;
      } else if (
        lock.target_type == 'layer' &&
        MAP.item_lookup.georeferenced.map((i) => i.id).includes(lock.target_id)
      ) {
        sessionLocks.lyrs[lock.target_id] = lock;
      }
    });
  }
  $: docsLockedCt = Object.keys(sessionLocks.docs).length;
  $: regsLockedCt = Object.keys(sessionLocks.regs).length;
  $: lyrsLockedCt = Object.keys(sessionLocks.lyrs).length;

  let multimaskKey = false;
  function reinitMultimask() {
    multimaskKey = !multimaskKey;
  }

  let previewKey = false;
  function reinitPreview() {
    previewKey = !previewKey;
  }

  let loadingDocids = [];
  $: {
    MAP.item_lookup.unprepared.forEach((doc) => {
      if (doc.file && loadingDocids.includes(doc.id)) {
        loadingDocids = loadingDocids.filter((item) => item !== doc.id);
      }
    });
  }

  let currentLayerSet = 'main-content';
  let layerSetLookup = {};
  let layerToLayerSetLookup = {};
  let layerToLayerSetLookupOrig = {};
  let layersToUpdate = {};
  function resetLayerSets(newLayerSets) {
    layerSetLookup = {};
    layerToLayerSetLookup = {};
    newLayerSets.forEach(function (ls) {
      layerSetLookup[ls.id] = ls;
      ls.layers.forEach(function (lyr) {
        layerToLayerSetLookup[lyr.slug] = ls.id;
        layerToLayerSetLookupOrig[lyr.slug] = ls.id;
      });

      let mosaicUrl;
      let ohmUrl;
      if (ls.mosaic_json_url) {
        mosaicUrl = makeTitilerXYZUrl({
          host: CONTEXT.titiler_host,
          url: ls.mosaic_json_url,
        });
        // make the OHM url here
        const mosaicUrlEncoded = makeTitilerXYZUrl({
          host: CONTEXT.titiler_host,
          url: ls.mosaic_json_url,
          doubleEncode: true,
        });
        const ll = getCenter(ls.extent);
        ohmUrl = `https://www.openhistoricalmap.org/edit#map=16/${ll[1]}/${ll[0]}&background=custom:${mosaicUrlEncoded}`;
      }
      if (ls.mosaic_cog_url) {
        mosaicUrl = makeTitilerXYZUrl({
          host: CONTEXT.titiler_host,
          url: ls.mosaic_cog_url,
        });
        // make the OHM url here
        const mosaicUrlEncoded = makeTitilerXYZUrl({
          host: CONTEXT.titiler_host,
          url: ls.mosaic_cog_url,
          doubleEncode: true,
        });
        const ll = getCenter(ls.extent);
        ohmUrl = `https://www.openhistoricalmap.org/edit#map=16/${ll[1]}/${ll[0]}&background=custom:${mosaicUrlEncoded}`;
      }
      ls.mosaicUrl = mosaicUrl;
      ls.ohmUrl = ohmUrl;
    });
    LAYERSETS = newLayerSets;
    reinitMultimask();
    reinitPreview();
  }
  resetLayerSets(LAYERSETS);

  let userCanEdit = false;
  userCanEdit =
    CONTEXT.user.is_staff ||
    (MAP.access == 'any' && CONTEXT.user.is_authenticated) ||
    (MAP.access == 'sponsor' && MAP.sponsor == CONTEXT.user.username);

  let currentIdentifier = MAP.identifier;
  function goToItem() {
    window.location = '/map/' + currentIdentifier;
  }
  let currentDoc = '---';
  function goToDocument() {
    window.location = '/document/' + currentDoc;
  }

  // $: bulkLoadInProgress = MAP.loading_documents;
  // $: {
  // 	if (bulkLoadInProgress && (MAP.progress.sheets_loaded == MAP.progress.sheets_total)) {
  // 		bulkLoadInProgress = false;
  // 	}
  // }
  $: documentsLoading = MAP.item_lookup.unprepared.some(function (doc) {
    return doc.loading_file;
  });

  let hash = window.location.hash.substr(1);

  const sectionVis = {
    summary: (!hash && MAP.item_lookup.georeferenced.length == 0) || hash == 'summary',
    preview: (!hash && MAP.item_lookup.georeferenced.length > 0) || hash == 'preview',
    unprepared: hash == 'unprepared',
    prepared: hash == 'prepared',
    georeferenced: hash == 'georeferenced',
    nonmaps: hash == 'nonmaps',
    skipped: hash == 'skipped',
    multimask: hash == 'multimask',
    download: hash == 'download',
  };

  function toggleSection(sectionId) {
    sectionVis[sectionId] = !sectionVis[sectionId];
  }

  function setHash(hash) {
    history.replaceState(null, document.title, `#${hash}`);
  }

  let intervalId;
  function manageAutoReload(run) {
    if (run) {
      intervalId = setInterval(pollMapSummary, 4000);
    } else {
      clearInterval(intervalId);
    }
  }

  let autoReload = false;
  $: {
    autoReload = MAP.locks.length > 0 || documentsLoading || MAP.loading_documents;
  }
  $: manageAutoReload(autoReload);

  function pollMapSummary() {
    getFromAPI(`/api/beta2/map/?map=${MAP.identifier}`, CONTEXT.ohmg_api_headers, (result) => {
      if (!previewRefreshable) {
        previewRefreshable = MAP.item_lookup.georeferenced.length != result.item_lookup.georeferenced.length;
      }
      MAP = result;
      processing = false;
    });
  }

  let refreshingLookups = false;
  function refreshLookups() {
    refreshingLookups = true;
    submitPostRequest(MAP.urls.summary, CONTEXT.ohmg_post_headers, 'refresh-lookups', {}, (result) => {
      if (
        MAP.item_lookup.unprepared.length != result.item_lookup.unprepared.length ||
        MAP.item_lookup.prepared.length != result.item_lookup.prepared.length ||
        MAP.item_lookup.georeferenced.length != result.item_lookup.georeferenced.length
      ) {
        fetchLayerSets();
        previewRefreshable = true;
      }
      MAP = result;
      refreshingLookups = false;
    });
  }

  function loadDocuments() {
    MAP.loading_documents = true;
    sectionVis['unprepared'] = true;
    submitPostRequest(MAP.urls.summary, CONTEXT.ohmg_post_headers, 'load-documents');
  }

  function fetchLayerSets() {
    getFromAPI(`/api/beta2/layersets/?map=${MAP.identifier}`, CONTEXT.ohmg_api_headers, (result) => {
      resetLayerSets(result);
      processing = false;
    });
  }

  function pollMapSummaryIfSuccess(response) {
    if (response.success) {
      pollMapSummary();
    } else {
      alert(response.message);
    }
    processing = false;
    bulkPrepareList = [];
  }
  function postDocumentUnprepare(documentId) {
    processing = true;
    submitPostRequest(`/document/${documentId}`, CONTEXT.ohmg_post_headers, 'unprepare', {}, pollMapSummaryIfSuccess);
  }
  function postLoadDocument(documentId) {
    documentsLoading = true;
    submitPostRequest(`/document/${documentId}`, CONTEXT.ohmg_post_headers, 'load-file');
  }

  function postRegionCategory(regionId, newCategory) {
    processing = true;
    submitPostRequest(
      `/region/${regionId}`,
      CONTEXT.ohmg_post_headers,
      'set-category',
      { 'new-category': newCategory },
      pollMapSummaryIfSuccess,
    );
  }

  function postSkipRegion(regionId, setTo) {
    processing = true;
    submitPostRequest(
      `/region/${regionId}`,
      CONTEXT.ohmg_post_headers,
      'set-skip',
      { skipped: setTo },
      pollMapSummaryIfSuccess,
    );
  }

  function submitClassifiedLayers() {
    processing = true;
    submitPostRequest(
      `/layerset/`,
      CONTEXT.ohmg_post_headers,
      'bulk-classify-layers',
      {
        'map-id': MAP.identifier,
        'update-list': Object.entries(layersToUpdate),
      },
      (response) => {
        if (!response.success) {
          alert(response.message);
        }
        previewRefreshable = true;
        processing = false;
      },
    );
  }

  function handleExistingMaskResponse(response) {
    if (response.success) {
      layersToUpdate[response.payload['resource-id']] = response.payload['category'];
    } else {
      const msg =
        'This layer is already included in the multimask for its ' +
        'current classification, and that mask will be deleted if ' +
        'you continue with this change. Set the layer back to its ' +
        'original classification to stop the change.';
      if (confirm(msg)) {
        layersToUpdate[response.payload['resource-id']] = response.payload['category'];
      }
    }
  }
  function checkForExistingMask(category, layerId) {
    submitPostRequest(
      `/layerset/`,
      CONTEXT.ohmg_post_headers,
      'check-for-existing-mask',
      {
        'resource-id': layerId,
        category: category,
      },
      handleExistingMaskResponse,
    );
  }

  let classifyingLayers = false;
  let bulkPreparing = false;
  let bulkPrepareList = [];

  let reinitModalMap = [{}];

  let modalIsGeospatial = false;
  let modalLyrUrl = '';
  let modalExtent = [];

  let splitDocumentId;
  let undoGeorefLayerId;

  let processing = false;

  let previewRefreshable = false;
</script>

<svelte:window
  on:click={() => {
    Array.from(document.getElementsByClassName('dropdown')).forEach((el) => {
      el.classList.remove('is-active');
    });
  }}
/>
<MapPreviewModal id={'modal-preview-map'} placeName={LOCALE.display_name} viewerUrl={MAP.urls.viewer} />
<GeoreferenceOverviewModal id={'modal-georeference-overview'} />
<UnpreparedSectionModal id={'modal-unprepared'} />
<PreparedSectionModal id={'modal-prepared'} />
<GeoreferencedSectionModal id={'modal-georeferenced'} />
<MultiMaskModal id={'modal-multimask'} />
<NonMapContentModal id={'modal-non-map'} />
<GeoreferencePermissionsModal id={'modal-permissions'} user={CONTEXT.user.username} {userCanEdit} item={MAP} />
<SkippedSectionHelpModal id="modal-skipped" />
<Modal id={'modal-simple-viewer'} full={true}>
  {#each reinitModalMap as key (key)}
    {#if modalIsGeospatial}
      <BasicLayerViewer {CONTEXT} LAYER_URL={modalLyrUrl} EXTENT={modalExtent} />
    {:else}
      <BasicDocViewer LAYER_URL={modalLyrUrl} EXTENT={modalExtent} />
    {/if}
  {/each}
</Modal>
<ConfirmNoSplitModal bind:processing {CONTEXT} documentId={splitDocumentId} callback={pollMapSummaryIfSuccess} />
<ConfirmBulkNoSplitModal bind:processing {CONTEXT} bind:bulkPrepareList callback={pollMapSummaryIfSuccess} />
<ConfirmUngeoreferenceModal bind:processing {CONTEXT} layerId={undoGeorefLayerId} callback={pollMapSummaryIfSuccess} />
{#if processing}
  <LoadingMask />
{/if}
<main>
  <MapBreadcrumbs {LOCALE} {MAP} />
  <section>
    <div class="section-title-bar">
      <button
        class="section-toggle-btn"
        title={sectionVis['summary'] ? 'Collapse section' : 'Expand section'}
        on:click={() => {
          toggleSection('summary');
        }}
      >
        <ConditionalDoubleChevron down={sectionVis['summary']} size="md" />
        <a id="summary"><h2>Summary</h2></a>
      </button>
    </div>
    {#if sectionVis['summary']}
      <div style="margin-bottom:10px;" transition:slide>
        <MapDetails {CONTEXT} {MAP} {SESSION_SUMMARY} {LAYERSETS} {userFilterItems} />
      </div>
    {/if}
  </section>
  <section>
    <div class="section-title-bar">
      <button
        class="section-toggle-btn"
        title={sectionVis['preview'] ? 'Collapse section' : 'Expand section'}
        disabled={MAP.item_lookup.georeferenced.length == 0}
        on:click={() => {
          toggleSection('preview');
        }}
      >
        <ConditionalDoubleChevron down={sectionVis['preview']} size="md" />
        <a id="preview"
          ><h2>
            Mosaic Preview ({MAP.item_lookup.georeferenced.length} layers)
          </h2></a
        >
      </button>
      <InfoModalButton modalId="modal-preview-map" />
    </div>
    {#if sectionVis['preview']}
      <div class="section-content" transition:slide>
        <MapPreview {CONTEXT} mapId={MAP.identifier} mapExtent={MAP.extent} bind:refreshable={previewRefreshable} />
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
          <button class="is-icon-link" on:click={refreshLookups} title="Regenerate summary (may take a moment)"
            ><Wrench /></button
          >
        {/if}
        <InfoModalButton modalId="modal-georeference-overview" />
      </div>
    </div>
    <div>
      <div style="display:flex; align-items:center;">
        {#if MAP.progress.loaded_pages < MAP.progress.total_pages && userCanEdit && !documentsLoading}
          <button
            class="button is-primary is-small"
            style="margin-left:10px; margin-right:10px;"
            title="Load documents"
            on:click={loadDocuments}
          >
            Load {MAP.progress.loaded_pages ? 'remaining' : 'all'} documents ({MAP.progress.total_pages -
              MAP.progress.loaded_pages})
          </button>
        {/if}
        <span>
          <em>
            {#if MAP.loading_documents}
              Loading document {MAP.progress.loaded_pages + 1}/{MAP.progress.total_pages}... (you can safely leave this
              page).
            {:else if MAP.progress.loaded_pages == 0}
              No content loaded yet...
            {:else if MAP.progress.loaded_pages < MAP.progress.total_pages}
              {MAP.progress.loaded_pages} of {MAP.progress.total_pages} document{#if MAP.progress.total_pages != 1}s{/if}
              loaded
            {/if}
          </em>
        </span>
      </div>
      {#if !CONTEXT.user.is_authenticated}
        <SigninReminder csrfToken={CONTEXT.csrf_token} />
      {/if}
      <section class="subsection">
        <div class="subsection-title-bar">
          <button
            class="section-toggle-btn"
            disabled={MAP.item_lookup.unprepared.length == 0}
            title={sectionVis['unprepared'] ? 'Collapse section' : 'Expand section'}
            on:click={() => toggleSection('unprepared')}
          >
            <ConditionalDoubleChevron down={sectionVis['unprepared']} size="md" />
            <a id="unprepared">
              <h3>
                Unprepared ({MAP.item_lookup.unprepared.length})
                {#if docsLockedCt}
                  &ndash; {docsLockedCt} locked...
                {/if}
              </h3>
            </a>
          </button>
          <InfoModalButton modalId="modal-unprepared" />
        </div>
        {#if sectionVis['unprepared']}
          <div transition:slide>
            <div style="margin: 10px 0px;">
              {#if MAP.item_lookup.unprepared.length > 0 && !bulkPreparing}
                <button
                  class="button is-primary"
                  disabled={!CONTEXT.user.is_authenticated}
                  title={!CONTEXT.user.is_authenticated
                    ? 'You must be signed in to prepare documents'
                    : 'Begin bulk preparation'}
                  on:click={() => (bulkPreparing = !bulkPreparing)}>Bulk prepare documents</button
                >
              {/if}
              {#if bulkPreparing}
                <button
                  class="button is-success"
                  disabled={bulkPrepareList.length === 0}
                  title="Submit documents for bulk preparation"
                  on:click={() => {
                    getModal('modal-confirm-bulk-no-split').open();
                    bulkPreparing = false;
                  }}>Submit</button
                >
                <button
                  class="button is-danger"
                  title="Cancel bulk preparation"
                  on:click={() => {
                    bulkPreparing = false;
                    layersToUpdate = {};
                    bulkPrepareList = [];
                  }}>Cancel</button
                >
              {/if}
            </div>
            <div class="documents-column">
              {#each MAP.item_lookup.unprepared as document}
                <UnpreparedCard
                  {CONTEXT}
                  {document}
                  {sessionLocks}
                  {userCanEdit}
                  bind:modalLyrUrl
                  bind:modalExtent
                  bind:modalIsGeospatial
                  bind:reinitModalMap
                  {postLoadDocument}
                  bind:documentsLoading
                  bind:splitDocumentId
                  bind:bulkPreparing
                  bind:bulkPrepareList
                />
              {/each}
            </div>
          </div>
        {/if}
      </section>
      <section class="subsection">
        <div class="subsection-title-bar">
          <button
            class="section-toggle-btn"
            on:click={() => toggleSection('prepared')}
            disabled={MAP.item_lookup.prepared.length === 0}
            title={sectionVis['prepared'] ? 'Collapse section' : 'Expand section'}
          >
            <ConditionalDoubleChevron down={sectionVis['prepared']} size="md" />
            <a id="prepared"
              ><h3>
                Prepared ({MAP.item_lookup.prepared.length})
                {#if regsLockedCt}
                  &ndash; {regsLockedCt} locked...
                {/if}
              </h3></a
            >
          </button>
          <InfoModalButton modalId="modal-prepared" />
        </div>
        {#if sectionVis['prepared']}
          <div transition:slide>
            <div class="documents-column">
              {#each MAP.item_lookup.prepared as region}
                <PreparedCard
                  {CONTEXT}
                  {region}
                  {sessionLocks}
                  {userCanEdit}
                  bind:modalLyrUrl
                  bind:modalExtent
                  bind:modalIsGeospatial
                  bind:reinitModalMap
                  {postDocumentUnprepare}
                  {postRegionCategory}
                  {postSkipRegion}
                />
              {/each}
            </div>
          </div>
        {/if}
      </section>
      <section class="subsection">
        <div class="subsection-title-bar">
          <button
            class="section-toggle-btn"
            on:click={() => toggleSection('georeferenced')}
            disabled={MAP.item_lookup.georeferenced.length == 0}
            title={sectionVis['georeferenced'] ? 'Collapse section' : 'Expand section'}
          >
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
          <InfoModalButton modalId="modal-georeferenced" />
        </div>
        {#if sectionVis['georeferenced']}
          <div transition:slide>
            <div style="margin: 10px 0px;">
              {#if MAP.item_lookup.georeferenced.length > 0 && !classifyingLayers}
                <button
                  class="button is-primary"
                  on:click={() => (classifyingLayers = !classifyingLayers)}
                  disabled={!CONTEXT.user.is_authenticated}
                  title={!CONTEXT.user.is_authenticated
                    ? 'You must be signed in to classify layers'
                    : 'Click to enable layer classification'}>Classify layers</button
                >
              {/if}
              {#if classifyingLayers}
                <button
                  class="button is-success"
                  disabled={Object.keys(layersToUpdate).length === 0}
                  title="Submit layer classification"
                  on:click={() => {
                    submitClassifiedLayers();
                    classifyingLayers = false;
                    layersToUpdate = {};
                    reinitMultimask();
                  }}>Submit</button
                >
                <button
                  class="button is-danger"
                  title="Cancel layer classification"
                  on:click={() => {
                    classifyingLayers = false;
                    layersToUpdate = {};
                    Object.keys(layerToLayerSetLookupOrig).forEach(function (k) {
                      layerToLayerSetLookup[k] = layerToLayerSetLookupOrig[k];
                    });
                  }}>Cancel</button
                >
              {/if}
            </div>
            <div class="documents-column">
              {#each MAP.item_lookup.georeferenced as layer}
                <LayerCard
                  {CONTEXT}
                  {MAP}
                  {LAYERSET_CATEGORIES}
                  {layer}
                  {sessionLocks}
                  {userCanEdit}
                  bind:modalLyrUrl
                  bind:modalExtent
                  bind:modalIsGeospatial
                  bind:reinitModalMap
                  bind:undoGeorefLayerId
                  bind:classifyingLayers
                  {layerToLayerSetLookup}
                  downloadEnabled={!MAP.hidden}
                  {checkForExistingMask}
                />
              {/each}
            </div>
          </div>
        {/if}
      </section>
      <section class="subsection">
        <div class="subsection-title-bar">
          <button
            class="section-toggle-btn"
            on:click={() => toggleSection('skipped')}
            disabled={MAP.item_lookup.skipped.length === 0}
            title={sectionVis['skipped'] ? 'Collapse section' : 'Expand section'}
          >
            <ConditionalDoubleChevron down={sectionVis['skipped']} size="md" />
            <a id="skipped"
              ><h3>
                Skipped ({MAP.item_lookup.skipped.length})
              </h3></a
            >
          </button>
          <InfoModalButton modalId="modal-skipped" />
        </div>
        {#if sectionVis['skipped']}
          <div transition:slide>
            <div class="documents-column">
              {#each MAP.item_lookup.skipped as region}
                <SkippedCard
                  {region}
                  {sessionLocks}
                  {userCanEdit}
                  bind:modalLyrUrl
                  bind:modalExtent
                  bind:modalIsGeospatial
                  bind:reinitModalMap
                  {postSkipRegion}
                />
              {/each}
            </div>
          </div>
        {/if}
      </section>
      <section class="subsection" style="border-bottom:none;">
        <div class="subsection-title-bar">
          <button
            class="section-toggle-btn"
            on:click={() => toggleSection('nonmaps')}
            disabled={MAP.item_lookup.nonmaps.length == 0}
            title={sectionVis['nonmaps'] ? 'Collapse section' : 'Expand section'}
          >
            <ConditionalDoubleChevron down={sectionVis['nonmaps']} size="md" />
            <a id="georeferenced"
              ><h3>
                Non-Map Content ({MAP.item_lookup.nonmaps.length})
              </h3></a
            >
          </button>
          <InfoModalButton modalId="modal-non-map" />
        </div>
        {#if sectionVis['nonmaps']}
          <div transition:slide>
            <div class="documents-column">
              {#each MAP.item_lookup.nonmaps as nonmap}
                <NonMapCard
                  {nonmap}
                  {sessionLocks}
                  {userCanEdit}
                  bind:modalLyrUrl
                  bind:modalExtent
                  bind:modalIsGeospatial
                  bind:reinitModalMap
                  {postRegionCategory}
                />
              {/each}
            </div>
          </div>
        {/if}
      </section>
    </div>
  </section>
  <section>
    <div class="section-title-bar">
      <button
        class="section-toggle-btn"
        on:click={() => toggleSection('multimask')}
        disabled={MAP.item_lookup.georeferenced.length == 0}
        title={sectionVis['multimask'] ? 'Collapse section' : 'Expand section'}
      >
        <ConditionalDoubleChevron down={sectionVis['multimask']} size="md" />
        <a id="multimask"><h2>MultiMask</h2></a>
      </button>
      <InfoModalButton modalId="modal-multimask" />
    </div>
    {#if sectionVis['multimask']}
      <div transition:slide>
        {#if !CONTEXT.user.is_authenticated}
          <SigninReminder csrfToken={CONTEXT.csrf_token} />
        {/if}
        <select
          class="item-select"
          bind:value={currentLayerSet}
          on:change={(e) => {
            reinitMultimask();
          }}
        >
          {#each LAYERSETS as ls}
            {#if ls.layers}
              <option value={ls.id}>{ls.name}</option>
            {/if}
          {/each}
        </select>
        <span>
          Masked layers:
          {#if layerSetLookup[currentLayerSet].multimask_geojson}
            {layerSetLookup[currentLayerSet].multimask_geojson.features.length}/{layerSetLookup[currentLayerSet].layers
              .length}
          {:else}
            0/{layerSetLookup[currentLayerSet].layers.length}
          {/if}
        </span>
        <span>
          <em
            >&mdash; <strong>Important:</strong> Do not work on a multimask while there is other work in progress on this
            map (you could lose work).</em
          >
        </span>
        {#key multimaskKey}
          <MultiMask
            LAYERSET={layerSetLookup[currentLayerSet]}
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
  #summary,
  #preview,
  #unprepared,
  #prepared,
  #georeferenced,
  #multimask {
    scroll-margin-top: 50px;
  }

  a.no-link {
    color: unset;
    text-decoration: unset;
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

  button.section-toggle-btn,
  a {
    text-decoration: none;
  }

  button.section-toggle-btn:hover {
    color: #1b4060;
  }

  button.section-toggle-btn:disabled,
  button.section-toggle-btn:disabled > a {
    color: grey;
  }

  button:disabled {
    cursor: default;
  }

  .section-title-bar {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }

  .subsection-title-bar {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }

  .documents-column {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 20px;
    padding-bottom: 15px;
  }

  select.item-select {
    margin-right: 3px;
    color: #2c689c;
    cursor: pointer;
  }

  @media screen and (max-width: 768px) {
    main {
      max-width: none;
    }
    .documents-column {
      flex-direction: column;
    }
  }
</style>
