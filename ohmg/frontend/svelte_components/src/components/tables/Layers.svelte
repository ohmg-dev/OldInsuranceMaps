<script>
  import Faders from 'phosphor-svelte/lib/Faders';

  import Link from '../base/Link.svelte';

  import PaginationButtons from './widgets/PaginationButtons.svelte';
  import FacetFilterSelect from './widgets/FacetFilterSelect.svelte';
  import RefreshButton from './widgets/RefreshButton.svelte';

  import FilterRow from './layouts/FilterRow.svelte';
  import TableContainer from './layouts/TableContainer.svelte';
  import TableHeader from './layouts/TableHeader.svelte';
  import TableCell from './layouts/TableCell.svelte';

  import { getFromAPI } from '../../lib/requests';
  import SearchBox from './widgets/SearchBox.svelte';
    import ShowFiltersButton from './widgets/ShowFiltersButton.svelte';

  export let CONTEXT;
  export let limit = '25';
  export let showUser = true;
  export let userFilter = null;
  export let showCategory = true;
  export let categoryFilter = null;
  export let transformationFilter = null;
  export let showMap = true;
  export let mapFilter = null;
  export let sortParam = 'id';
  export let sortDir = 'des';
  export let showFilters = false;
  export let searchTerm = null;
  export let searchField = "title";

  export let includeSearch = true;
  export let includeFilters = true;

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
    if (searchTerm) {
      fetchUrl += `&search=${searchTerm}&field=${searchField}`
    }
    getFromAPI(fetchUrl, CONTEXT.ohmg_api_headers, (result) => {
      items = result.items;
      total = result.count;
      userFilterItems = result.filter_items.users;
      mapFilterItems = result.filter_items.maps;
      categoryFilterItems = result.filter_items.categories;
      transformationFilterItems = result.filter_items.transformations;
      loading = false;
    });
  }
  console.log(CONTEXT)
</script>

<section class="table-section">
  <div class="top-row">
    <div class="top-row-left">
      {#if includeSearch}
        <SearchBox bind:searchTerm />
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
    {#if showUser}
      <FacetFilterSelect items={userFilterItems} bind:value={userFilter} placeholder="Set user..." />
    {/if}
    {#if showCategory}
      <FacetFilterSelect items={categoryFilterItems} bind:value={categoryFilter} placeholder="Set category..." />
    {/if}
    <FacetFilterSelect items={transformationFilterItems} bind:value={transformationFilter} placeholder="Set transformation..." />
  </FilterRow>
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
  .thumb-container {
    width: 65px;
    display: inline-block;
    text-align: center;
  }
  .thumb-container > img {
    max-height: 50px;
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
