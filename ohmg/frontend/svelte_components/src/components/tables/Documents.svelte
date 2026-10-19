<script>
  import Link from '../base/Link.svelte';

  import Modal, { openModal } from '../base/Modal.svelte';

  import PaginationButtons from './widgets/PaginationButtons.svelte';
  import FacetFilterSelect from './widgets/FacetFilterSelect.svelte';
  import RefreshButton from './widgets/RefreshButton.svelte';

  import BasicDocViewer from '../interfaces/BasicDocViewer.svelte';

  import FilterRow from './layouts/FilterRow.svelte';
  import TableContainer from './layouts/TableContainer.svelte';
  import TableHeader from './layouts/TableHeader.svelte';
  import TableCell from './layouts/TableCell.svelte';

  import { getFromAPI } from '../../lib/requests';
  import SearchBox from './widgets/SearchBox.svelte';
    import ShowFiltersButton from './widgets/ShowFiltersButton.svelte';

  export let CONTEXT;
  export let limit = '25';
  export let showMap = true;
  export let mapFilter = null;
  export let prepFilter = null;
  export let sortParam = null;
  export let sortDir = 'des';
  export let showFilters = false;
  export let searchTerm = null;
  export let searchField = "title";

  export let includeSearch = true;
  export let includeFilters = true;

  let mapFilterItems = [];
  let preparedFilterItems = [{"id": true, label: "Yes"}, {id: false, label: "No"}];

  let loading = false;
  let searching = false;

  let items = [];

  let modalLyrUrl = '';
  let modalExtent = [];
  let reinitModalMap = [{}];

  let offset = 0;
  let total = 0;

  let currentLimit = limit;
  $: useLimit = typeof currentLimit == 'string' ? currentLimit : currentLimit.value;

  $: {
    loading = true;
    let fetchUrl = `/api/beta2/documents?offset=${offset}`;
    if (limit != 0 && useLimit) {
      fetchUrl = `${fetchUrl}&limit=${useLimit}`;
    }
    if (mapFilter) {
      fetchUrl += `&map=${mapFilter.id}`;
    }
    if (prepFilter) {
      fetchUrl += `&prepared=${prepFilter.id}`;
    }
    if (sortParam) {
      fetchUrl += `&sortby=${sortParam}&sort=${sortDir}`;
    }
    if (searchTerm) {
      searching = true;
      fetchUrl += `&search=${searchTerm}&field=${searchField}`
    }
    getFromAPI(fetchUrl, CONTEXT.ohmg_api_headers, (result) => {
      items = result.items;
      total = result.count;
      mapFilterItems = result.filter_items.maps;
      loading = false;
      searching = false;
    });
  }
</script>

<Modal id={'modal-simple-viewer2'} full={true}>
  {#each reinitModalMap as key (key)}
    <BasicDocViewer LAYER_URL={modalLyrUrl} EXTENT={modalExtent} elementId="doc-viewer2"/>
  {/each}
</Modal>
<section class="table-section">
  <div class="top-row">
    <div class="top-row-left">
      {#if includeSearch}
        <SearchBox bind:searchTerm bind:searching />
      {/if}
      {#if includeFilters}
        <ShowFiltersButton bind:showFilters />
      {/if}
      {#if CONTEXT.on_mobile}
      <RefreshButton
        onClick={() => {
          offset = 1000;
          offset = 0;
        }}
        bind:loading
      />
      {/if}
    </div>
    <div class="top-row-right">
      <PaginationButtons bind:currentOffset={offset} bind:total bind:currentLimit />
      {#if !CONTEXT.on_mobile}
      <RefreshButton
        onClick={() => {
          offset = 1000;
          offset = 0;
        }}
        bind:loading
      />
      {/if}
    </div>
  </div>
  {#if includeFilters}
  <FilterRow {showFilters} bind:currentLimit>
    {#if showMap}
      <FacetFilterSelect items={mapFilterItems} bind:value={mapFilter} placeholder="Set map..." />
    {/if}
    <FacetFilterSelect items={preparedFilterItems} bind:value={prepFilter} placeholder="Set prepared..." />
  </FilterRow>
  {/if}
  <TableContainer bind:items bind:loading>
    <svelte:fragment slot="header-row">
      <TableHeader title="Id" value={'id'} bind:sortDir bind:sortParam bind:offset />
      {#if showMap}
        <TableHeader title="Map" value={'map'} bind:sortDir bind:sortParam bind:offset />
      {/if}
      <TableHeader title="Document" value={'nickname'} bind:sortDir bind:sortParam bind:offset />
      <TableHeader title="Prepared?" newCol={true} />
      <TableHeader title="Result" />
    </svelte:fragment>
    <svelte:fragment slot="data-row" let:item>
      <TableCell numCol={true}>{item.id}</TableCell>
      {#if showMap}
      <TableCell>
        <Link href={`/map/${item.map.identifier}`} title={item.map.title}>{item.map.title}</Link>
      </TableCell>
      {/if}
      <TableCell>
        <button
          title="Open layer preview"
          class="thumbnail-btn"
          on:click={() => {
            modalLyrUrl = item.urls.image;
            modalExtent = [0, -item.image_size[1], item.image_size[0], 0];
            openModal('modal-simple-viewer2');
            reinitModalMap = [{}];
          }}
        >
          <img style="cursor:zoom-in" src={item.urls.thumbnail} alt={item.nickname} />
        </button>
        <Link href={`/document/${item.id}`} title={item.nickname}>
          {item.nickname}</Link>
      </TableCell>
      <TableCell numCol={true} newCol={true}>
        {#if item.prepared}
          <span style="color:green">✓</span>
        {:else}
          <span style="color:red">x</span>
        {/if}
      </TableCell>
      <TableCell>
        <div style="display:flex; gap:.5em;">
          {#if item.regions.length == 0}
            ---
          {:else if item.regions.length == 1}
            no split
          {:else}
            {#each item.regions as region}
              <button
                title="Open layer preview"
                class="thumbnail-btn"
                on:click={() => {
                  modalLyrUrl = region.urls.image;
                  modalExtent = [0, -region.image_size[1], region.image_size[0], 0];
                  openModal('modal-simple-viewer2');
                  reinitModalMap = [{}];
                }}
              >
                <img style="cursor:zoom-in" src={region.urls.thumbnail} alt={region.nickname} />
              </button>
            {/each}
          {/if}
        </div>
      </TableCell>
    </svelte:fragment>
  </TableContainer>
</section>

<style>
  .top-row {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    margin:.5em 0;
  }
  .top-row-left {
    display: flex;
    gap: .5em;
    align-items: center;
  }
  .top-row-right {
    display: flex;
    align-items: center;
    gap: .25em;
  }
  button.thumbnail-btn > img {
    max-height: 50px;
    cursor: zoom-in;
  }

  @media screen and (max-width: 768px) {
    .top-row {
      flex-direction: column;
      gap: .5em;
    }
    .top-row-right {
      justify-content: center;
    }
  }
</style>
