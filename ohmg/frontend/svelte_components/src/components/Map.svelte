<script>

  import Wrench from 'phosphor-svelte/lib/Wrench';

  import InfoModalButton from './buttons/InfoModalButton.svelte';

  import ExpandableSection from './base/ExpandableSection.svelte';
  import TabbedSection from './base/TabbedSection.svelte';
  import Modal, { getModal } from './base/Modal.svelte';

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

  import SigninReminder from './common/SigninReminder.svelte';
  import LoadingEllipsis from './common/LoadingEllipsis.svelte';
  import LoadingMask from './common/LoadingMask.svelte';

  import MultimaskSection from './map/MultimaskSection.svelte'
  import MosaicDownload from './map/MosaicDownload.svelte';
  import Details from './map/Details.svelte';

  import MapContributors from './tables/MapContributors.svelte';
  import Sessions from './tables/Sessions.svelte';

  import MapBreadcrumbs from './breadcrumbs/MapBreadcrumbs.svelte';

  import UnpreparedCard from './cards/UnpreparedCard.svelte';
  import PreparedCard from './cards/PreparedCard.svelte';
  import LayerCard from './cards/LayerCard.svelte';
  import SkippedCard from './cards/SkippedCard.svelte';
  import NonMapCard from './cards/NonMapCard.svelte';

  import { getFromAPI, submitPostRequest } from '../lib/requests';
  import SkippedSectionHelpModal from './modals/SkippedSectionHelpModal.svelte';

  export let CONTEXT;
  export let MAP;
  export let LOCALE;
  export let SESSION_SUMMARY;
  export let LAYERSETS;
  export let LAYERSET_CATEGORIES;

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

  let mosaicSectionActiveTab = "preview";
  let detailsSectionActiveTab = "details";
</script>

<svelte:window
  on:click={() => {
    Array.from(document.getElementsByClassName('dropdown')).forEach((el) => {
      el.classList.remove('is-active');
    });
  }}
/>
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
  <ExpandableSection TITLE="Summary" bind:EXPANDED={sectionVis['summary']}>
    <TabbedSection tabs={[
      {id: "details", title: "Details"},
      {id: "stats", title: "Stats"},
      {id: "activity", title: "Activity"},
    ]} bind:activeTab={detailsSectionActiveTab}>
      {#if detailsSectionActiveTab == "details"}
        <Details {MAP} {SESSION_SUMMARY} />
      {:else if detailsSectionActiveTab == "stats"}
        <div>
          <p>
            These users have contributed to the creation of the content within this map, by preparing or georeferencing
            images. Currently, trimming or "multimask" work is not reflected in this table.
          </p>
        </div>
        <MapContributors {CONTEXT} mapId={MAP.identifier} />
      {:else if detailsSectionActiveTab == "activity"}
        <div>
          <p>
            Below is complete record of all preparation or georeferencing actions that have been performed on documents
            within this map. Currently, trimming or "multimask" work is not reflected in this table.
          </p>
        </div>
        <Sessions {CONTEXT} mapFilter={{ id: MAP.identifier }} showMap={false} paginate={true} limit="50" />
      {/if}
    </TabbedSection>
  </ExpandableSection>
  <ExpandableSection 
      TITLE="Mosaic"
      DISABLED={MAP.item_lookup.georeferenced.length == 0}
      bind:EXPANDED={sectionVis['preview']}
    >
    <TabbedSection tabs={[
      {id: "preview", title: "Preview"},
      {id: "multimask", title: "MultiMask"},
      {id: "download", title: "Downloads & Services"},
    ]} bind:activeTab={mosaicSectionActiveTab}>
      {#if mosaicSectionActiveTab == "preview"}
        {#key previewKey}
            <MapPreview {CONTEXT}
              mapId={MAP.identifier}
              mapExtent={MAP.extent}
              locale={LOCALE}
              bind:refreshable={previewRefreshable} />
        {/key}
      {:else if mosaicSectionActiveTab == "multimask"}
        <MultimaskSection
          {CONTEXT}
          mapId={MAP.identifier}
          {reinitMultimask}
          bind:multimaskKey
          {userCanEdit} />
      {:else if mosaicSectionActiveTab == "download"}
        <MosaicDownload
          {CONTEXT}
          {MAP}
          {LAYERSETS} />
      {/if}
    </TabbedSection>
  </ExpandableSection>
  <section>
    <div class="section-title-bar">
      <div>
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
    </div>
  </section>
  <ExpandableSection
      TITLE={`Unprepared (${MAP.item_lookup.unprepared.length})${docsLockedCt ? ` – ${docsLockedCt} locked...` : ''}`}
      DISABLED={MAP.item_lookup.unprepared.length == 0}
      INFO_MODAL_ID="modal-unprepared"
      IS_SUBSECTION={true}
      bind:EXPANDED={sectionVis['unprepared']}
    >
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
  </ExpandableSection>
  <ExpandableSection
      TITLE={`Prepared (${MAP.item_lookup.prepared.length})${regsLockedCt ? ` – ${regsLockedCt} locked...` : ''}`}
      DISABLED={MAP.item_lookup.prepared.length == 0}
      INFO_MODAL_ID="modal-prepared"
      IS_SUBSECTION={true}
      bind:EXPANDED={sectionVis['prepared']}
    >
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
   </ExpandableSection>
   <ExpandableSection
      TITLE={`Georeferenced (${MAP.item_lookup.georeferenced.length})${lyrsLockedCt ? ` – ${lyrsLockedCt} locked...` : ''}`}
      DISABLED={MAP.item_lookup.georeferenced.length == 0}
      INFO_MODAL_ID="modal-georeferenced"
      IS_SUBSECTION={true}
      bind:EXPANDED={sectionVis['georeferenced']}
    >
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
          bind:layersToUpdate
          {layerToLayerSetLookup}
          downloadEnabled={!MAP.hidden}
        />
      {/each}
    </div>
   </ExpandableSection>
   <ExpandableSection
      TITLE={`Skipped (${MAP.item_lookup.skipped.length})`}
      DISABLED={MAP.item_lookup.skipped.length == 0}
      INFO_MODAL_ID="modal-skipped"
      IS_SUBSECTION={true}
      bind:EXPANDED={sectionVis['skipped']}
    >
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
   </ExpandableSection>
   <ExpandableSection
      TITLE={`Non-Map Content (${MAP.item_lookup.nonmaps.length})`}
      DISABLED={MAP.item_lookup.nonmaps.length == 0}
      INFO_MODAL_ID="modal-non-map"
      IS_SUBSECTION={true}
      bind:EXPANDED={sectionVis['nonmaps']}
    >
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
   </ExpandableSection>
</main>

<style>

  a.no-link {
    color: unset;
    text-decoration: unset;
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

  .documents-column {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 20px;
    padding-bottom: 15px;
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
