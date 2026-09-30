<script>
  import { slide } from 'svelte/transition';

  import Faders from 'phosphor-svelte/lib/Faders';

  import Link from '../base/Link.svelte';
  import SessionListModal from '../shared/modals/SessionListModal.svelte';

  import PaginationButtons from './widgets/PaginationButtons.svelte';
  import FacetFilterSelect from './widgets/FacetFilterSelect.svelte';
  import LimitSelect from './widgets/LimitSelect.svelte';
  import SortableHeader from './widgets/SortableHeader.svelte';
  import RefreshButton from './widgets/RefreshButton.svelte';

  import { getFromAPI } from '../../lib/requests';
  import InfoModalButton from '../shared/buttons/InfoModalButton.svelte';

  export let CONTEXT;
  export let limit = '10';
  export let showUser = true;
  export let userFilter = null;
  export let showCategory = true;
  export let categoryFilter = null;
  export let transformationFilter = null;
  export let allowRefresh = true;
  export let showMap = true;
  export let mapFilter = null;
  export let sortParam = 'id';
  export let sortDir = 'des';
  export let tableHeight = '100%';
  export let showFilters = true;

  let userFilterItems = [];
  let mapFilterItems = [];
  let categoryFilterItems = [];
  let transformationFilterItems = [];

  let loading = false;

  let items = [];

  let offset = 0;
  let total = 0;

  let currentLimit = limit;
  $: useLimit = typeof currentLimit == 'string' ? currentLimit : currentLimit.value;

  $: {
    loading = true;
    let fetchUrl = `/api/beta2/layers2/?offset=${offset}`;
    if (limit != 0 && useLimit) {
      fetchUrl = `${fetchUrl}&limit=${useLimit}`;
    }
    if (mapFilter) {
      fetchUrl += `&map=${mapFilter.id}`;
    }
    if (userFilter) {
      fetchUrl += `&username=${userFilter.id}`;
    }
    if (categoryFilter) {
      fetchUrl += `&category=${categoryFilter.id}`;
    }
    if (transformationFilter) {
      fetchUrl += `&transformation=${transformationFilter.id}`;
    }
    if (sortParam) {
      fetchUrl += `&sortby=${sortParam}&sort=${sortDir}`;
    }
    getFromAPI(fetchUrl, CONTEXT.ohmg_api_headers, (result) => {
      console.log(result)
      items = result.items;
      total = result.count;
      userFilterItems = result.filter_items.users;
      mapFilterItems = result.filter_items.maps;
      categoryFilterItems = result.filter_items.categories;
      transformationFilterItems = result.filter_items.transformations;
      loading = false;
    });
  }
</script>

<SessionListModal id={'modal-session-list'} />
<div>
  <div class="level is-mobile" style="margin:.5em 0;">
    <div class="level-left">
      <InfoModalButton modalId="modal-session-list" />
      <button
        class="is-icon-link"
        title={showFilters ? 'Hide filters' : 'Show filters'}
        on:click={() => {
          showFilters = !showFilters;
        }}
        ><Faders size={'1em'} />
      </button>
      {#if allowRefresh}
        <RefreshButton
          onClick={() => {
            offset = 1000;
            offset = 0;
          }}
          bind:loading
        />
      {/if}
    </div>
    <div class="level-right">
      <div class="level-item">
        <PaginationButtons bind:currentOffset={offset} bind:total bind:currentLimit />
      </div>
    </div>
  </div>
  {#if showFilters}
    <div transition:slide class="level" style="margin:.5em 0;">
      <div class="filter-level level-left">
        {#if showMap}
          <FacetFilterSelect items={mapFilterItems} bind:value={mapFilter} placeholder="Filter by map..." />
        {/if}
        {#if showUser}
          <FacetFilterSelect items={userFilterItems} bind:value={userFilter} placeholder="Filter by user..." />
        {/if}
        {#if showCategory}
          <FacetFilterSelect items={categoryFilterItems} bind:value={categoryFilter} placeholder="Filter by category..." />
        {/if}
        <FacetFilterSelect items={transformationFilterItems} bind:value={transformationFilter} placeholder="Filter by transformation..." />
      </div>
      <div class="filter-level level-right">
        <LimitSelect bind:value={currentLimit} />
      </div>
    </div>
  {/if}
  <div style="height: 100%; overflow-y:auto; border:1px solid #ddd; border-radius:4px; background:white;">
    {#if items.length > 0}
      <div class="table-container" style={`height: ${tableHeight};`}>
        <table>
          <thead>
            <tr>
              <th><SortableHeader title="Id" value={'id'} bind:sortDir bind:sortParam bind:offset /></th>
              {#if showMap}
                <th><SortableHeader title="Map" value={'map'} bind:sortDir bind:sortParam bind:offset /></th>
              {/if}
              <th><SortableHeader title="Layer" value={'nickname'} bind:sortDir bind:sortParam bind:offset /></th>
              <th><SortableHeader title="Category" /></th>
              <th><SortableHeader title="Masked?" /></th>
              <th class="new-col"><SortableHeader title="Georeferenced by" value={'created_by'} bind:sortDir bind:sortParam bind:offset /></th>
              <th><SortableHeader title="Updated by" value={'last_updated_by'} bind:sortDir bind:sortParam bind:offset /></th>
              <th class="new-col"><SortableHeader title="RMSE" value={'rmse'} alt="Sort by average error across all GCPs" bind:sortDir bind:sortParam bind:offset /></th>
              <th><SortableHeader title="Skew" value={'skew_norm'} alt="Sort by skew (degrees)" bind:sortDir bind:sortParam bind:offset /></th>
              <th><SortableHeader title="Stretch" value={'anisotropy_norm'} alt="Sort by amount of x/y scale distortion (anisotropy)" bind:sortDir bind:sortParam bind:offset /></th>
              <th><SortableHeader title="GCPs" value={'gcp_count'} alt="Sort by number of GCPs" bind:sortDir bind:sortParam bind:offset /></th>
              <th><SortableHeader title="Transformation" value={'transformation'} bind:sortDir bind:sortParam bind:offset /></th>
            </tr>
          </thead>
          <tbody>
            {#each items as lyr}
              <tr style="height:38px; vertical-align:center;">
                <td class="num-col">{lyr.id}</td>
                {#if showMap}
                <td>
                  <Link href={`/map/${lyr.map.identifier}`} title={lyr.map.title}>{lyr.map.title}</Link>
                </td>
                {/if}
                <td>
                  <Link href={`/layer/${lyr.id}`} title={lyr.nickname}>
                  <div class="thumb-container">
                    <img style="width:100%; height:auto;" src={lyr.urls.thumbnail} alt={lyr.nickname} />
                  </div>
                    {lyr.nickname}</Link>
                </td>
                <td>{lyr.category}</td>
                <td class="num-col">
                  {#if lyr.mask}
                    <span style="color:green">✓</span>
                  {:else}
                    <span style="color:red">x</span>
                  {/if}
                </td>
                <td class="new-col">
                  <Link href={`/layers/${lyr.created_by}`} title="View profile">{lyr.created_by}</Link>
                </td>
                <td>
                  <Link href={`/layers/${lyr.last_updated_by}`} title="View profile">{lyr.last_updated_by}</Link>
                </td>
                <td class="num-col new-col">{lyr.rmse}</td>
                <td class="num-col">{lyr.skew_norm}</td>
                <td class="num-col">{lyr.anisotropy_norm}</td>
                <td class="num-col">{lyr.gcp_count}</td>
                <td class="num-col">{lyr.transformation}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {:else}
      <div class="level">
        <div class="level-item" style="margin:5px 0;">
          <em>{loading ? 'loading...' : 'no results'}</em>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .level.is-mobile > .level-left {
    flex-direction: row;
  }
  table {
    text-align: left;
    position: relative;
  }
  th {
    position: sticky;
    top: 0;
  }
  td {
    white-space: nowrap;
    padding: 2px 0.5em;
    vertical-align: middle;
  }
  .table-container {
    overflow-y: auto;
  }
  .thumb-container {
    width: 65px;
    display: inline-block;
    text-align: center;
  }
  .filter-level {
    max-width: calc(100% - 75px);
  }
  @media screen and (max-width: 768px) {
    .filter-level,
    :global(.filter-input),
    :global(.date-filter),
    :global(button.date-field) {
      min-width: 100% !important;
    }
  }

  .num-col {
    padding: 0;
    width: 25px;
    text-align: center;
  }
  .new-col {
    border-left: 1px solid gray;
  }

</style>
