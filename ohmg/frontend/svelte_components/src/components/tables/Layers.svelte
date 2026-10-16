<script>
  import { slide } from 'svelte/transition';

  import Faders from 'phosphor-svelte/lib/Faders';

  import Link from '../base/Link.svelte';
  import SessionListModal from '../shared/modals/SessionListModal.svelte';

  import PaginationButtons from './widgets/PaginationButtons.svelte';
  import FacetFilterSelect from './widgets/FacetFilterSelect.svelte';
  import LimitSelect from './widgets/LimitSelect.svelte';
  import RefreshButton from './widgets/RefreshButton.svelte';

  import TableContainer from './layouts/TableContainer.svelte';
  import TableHeader from './layouts/TableHeader.svelte';
  import TableCell from './layouts/TableCell.svelte';

  import { getFromAPI } from '../../lib/requests';
  import InfoModalButton from '../shared/buttons/InfoModalButton.svelte';

  export let CONTEXT;
  export let limit = '25';
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
  <TableContainer bind:items bind:loading>
    <svelte:fragment slot="header-row">
      <TableHeader title="Id" value={'id'} bind:sortDir bind:sortParam bind:offset />
      {#if showMap}
        <TableHeader title="Map" value={'map'} bind:sortDir bind:sortParam bind:offset />
      {/if}
      <TableHeader title="Layer" value={'nickname'} bind:sortDir bind:sortParam bind:offset />
      <TableHeader title="Category" />
      <TableHeader title="Masked?" />
      <TableHeader title="Georeferenced by" value={'created_by'} newCol={true} bind:sortDir bind:sortParam bind:offset />
      <TableHeader title="Updated by" value={'last_updated_by'} bind:sortDir bind:sortParam bind:offset />
      {#if CONTEXT.user.is_staff}
      <TableHeader title="RMSE" value={'rmse'} alt="Sort by average error across all GCPs" newCol={true} bind:sortDir bind:sortParam bind:offset />
      <TableHeader title="Skew" value={'skew_norm'} alt="Sort by skew (degrees)" bind:sortDir bind:sortParam bind:offset />
      <TableHeader title="Stretch" value={'anisotropy_norm'} alt="Sort by amount of x/y scale distortion (anisotropy)" bind:sortDir bind:sortParam bind:offset />
      {/if}
      <TableHeader title="GCPs" value={'gcp_count'} alt="Sort by number of GCPs" bind:sortDir bind:sortParam bind:offset />
      <TableHeader title="Transformation" value={'transformation'} bind:sortDir bind:sortParam bind:offset />
    </svelte:fragment>
    <svelte:fragment slot="data-row" let:item>
      <TableCell numCol={true}>{item.id}</TableCell>
      {#if showMap}
      <TableCell>
        <Link href={`/map/${item.map.identifier}`} title={item.map.title}>{item.map.title}</Link>
      </TableCell>
      {/if}
      <TableCell>
        <Link href={`/layer/${item.id}`} title={item.nickname}>
        <div class="thumb-container">
          <img src={item.urls.thumbnail} alt={item.nickname} />
        </div>
          {item.nickname}</Link>
      </TableCell>
      <TableCell>{item.category}</TableCell>
      <TableCell numCol={true}>
        {#if item.mask}
          <span style="color:green">✓</span>
        {:else}
          <span style="color:red">x</span>
        {/if}
      </TableCell>
      <TableCell newCol={true}>
        <Link href={`/layers/${item.created_by}`} title="View profile">{item.created_by}</Link>
      </TableCell>
      <TableCell>
        <Link href={`/layers/${item.last_updated_by}`} title="View profile">{item.last_updated_by}</Link>
      </TableCell>
      {#if CONTEXT.user.is_staff}
      <TableCell numCol={true} newCol={true}>{item.rmse}</TableCell>
      <TableCell numCol={true}>{item.skew_norm}</TableCell>
      <TableCell numCol={true}>{item.anisotropy_norm}</TableCell>
      {/if}
      <TableCell numCol={true}>{item.gcp_count}</TableCell>
      <TableCell numCol={true}>{item.transformation}</TableCell>
    </svelte:fragment>
  </TableContainer>
</div>

<style>
  .level.is-mobile > .level-left {
    flex-direction: row;
  }
  .thumb-container {
    width: 65px;
    display: inline-block;
    text-align: center;
  }
  .thumb-container > img {
    max-height: 50px;
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
</style>
