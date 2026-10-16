<script>
  import { getFromAPI } from '../../lib/requests';

  import Link from '../base/Link.svelte';

  import TableContainer from './layouts/TableContainer.svelte';
  import TableHeader from './layouts/TableHeader.svelte';
  import TableCell from './layouts/TableCell.svelte';
  import FilterRow from './layouts/FilterRow.svelte';

  import PaginationButtons from './widgets/PaginationButtons.svelte';
  import FacetFilterSelect from './widgets/FacetFilterSelect.svelte';
  import RefreshButton from './widgets/RefreshButton.svelte';
  import ShowFiltersButton from './widgets/ShowFiltersButton.svelte';
  import SearchBox from './widgets/SearchBox.svelte';

  export let CONTEXT;
  export let limit = '25';
  export let paginate = true;
  export let showUsers = true;
  export let userFilter = null;
  export let showPlace = true;
  export let placeFilter = null;
  export let placeInclusive = false;
  export let sortParam = 'title';
  export let sortDir = 'asc';
  export let searchTerm = null;
  export let includeSearch = true;
  export let includeFilters = true;
  export let useTitle = null;

  let placeFilterItems = [];
  let userFilterItems = [];

  let loading = false;

  let items = [];

  let offset = 0;
  let total = 0;

  let currentLimit = limit;
  $: useLimit = typeof currentLimit == 'string' ? currentLimit : currentLimit.value;

  $: {
    loading = true;
    let fetchUrl = `/api/beta2/maps2/?offset=${offset}`;
    if (limit != 0 && useLimit) {
      fetchUrl = `${fetchUrl}&limit=${useLimit}`;
    }
    if (placeFilter) {
      fetchUrl += `&place=${placeFilter.id}`;
    }
    if (userFilter) {
      fetchUrl += `&loaded_by=${userFilter.id}`;
    }
    if (placeInclusive) {
      fetchUrl += `&place_inclusive=true`;
    }
    if (sortParam) {
      fetchUrl += `&sortby=${sortParam}&sort=${sortDir}`;
    }
    if (searchTerm) {
      fetchUrl += `&search=${searchTerm}`;
    }
    getFromAPI(fetchUrl, CONTEXT.ohmg_api_headers, (result) => {
      items = result.items;
      total = result.count;
      placeFilterItems = result.filter_items.places;
      userFilterItems = result.filter_items.users;
      loading = false;
    });
  }

  let showFilters = false;
</script>

<section class="table-section">
  <div class="top-row">
    <div class="top-row-left">
      {#if useTitle}
        <h4 style="margin: .2em 0;">{useTitle}</h4>
      {/if}
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
      {#if paginate}
        <PaginationButtons bind:currentOffset={offset} bind:total bind:currentLimit />
      {/if}
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
  <FilterRow {showFilters} bind:currentLimit>
    {#if showPlace}
      <FacetFilterSelect
        items={placeFilterItems}
        bind:value={placeFilter}
        placeholder="Set place..."
        bind:offset
      />
    {/if}
    {#if showUsers}
      <FacetFilterSelect
        items={userFilterItems}
        bind:value={userFilter}
        placeholder="Set user..."
        bind:offset
      />
    {/if}
  </FilterRow>
  <TableContainer bind:items bind:loading>
    <svelte:fragment slot="header-row">
      <TableHeader title="Title" value={'title'} bind:sortDir bind:sortParam bind:offset />
      <TableHeader title="Year" value={'year'} bind:sortDir bind:sortParam bind:offset />
      <TableHeader title="Docs" bind:sortDir bind:sortParam value={'document_ct'} bind:offset />
      {#if showPlace}
        <TableHeader title="Place" />
      {/if}
      <TableHeader title="Loaded by" />
      <TableHeader title="Date" value={'load_date'} bind:sortDir bind:sortParam bind:offset />
      <TableHeader
          title="U"
          value={'unprepared_ct'}
          alt="Number of unprepared documents"
          newCol={true}
          bind:sortDir
          bind:sortParam
          bind:offset
        />
      <TableHeader
          title="P"
          value={'prepared_ct'}
          alt="Number of prepared regions"
          bind:sortDir
          bind:sortParam
          bind:offset
        />
      <TableHeader
          title="G"
          value={'layer_ct'}
          alt="Number of georeferenced layers"
          bind:sortDir
          bind:sortParam
          bind:offset
        />
      <TableHeader
          title="S"
          alt="Number of skipped pieces"
          value={'skip_ct'}
          bind:sortDir
          bind:sortParam
          bind:offset
        />
      <TableHeader
          title="N"
          alt="Number of non-map pieces"
          value={'nonmap_ct'}
          bind:sortDir
          bind:sortParam
          bind:offset
        />
      <TableHeader
          title="%"
          alt="Percent complete - G/(U+P+G)"
          value={'completion_pct'}
          newCol={true}
          bind:sortDir
          bind:sortParam
          bind:offset
        />
      <TableHeader
          title="MM"
          alt="Main content layers included in multimask"
          value={'multimask_rank'}
          newCol={true}
          bind:sortDir
          bind:sortParam
          bind:offset
        />
      <TableHeader title="GT" alt="A geotiff has been created for this map's main content" newCol={true}/>
      <TableHeader title="XYZ" alt="An XYZ tileset has been created for this map'item main content" />
    </svelte:fragment>
    <svelte:fragment slot="data-row" let:item>
      <TableCell><Link href={`/map/${item.identifier}`}>{item.title}</Link></TableCell>
      <TableCell>{item.year}</TableCell>
      <TableCell>{item.document_ct}</TableCell>
      {#if showPlace}
        <TableCell>
          {#if item.locale}
            <Link href={`/${item.locale.slug}`} title={`View all ${item.locale.display_name} maps`}
              >{item.locale.display_name}</Link
            >
          {:else}
            Error: no locale
          {/if}
        </TableCell>
      {/if}
      <TableCell>
        {#if item.loaded_by}
          <Link href={item.loaded_by.profile_url} title="View profile">{item.loaded_by.username}</Link>
        {:else}
          --
        {/if}
      </TableCell>
      <TableCell>
        {#if item.load_date}
          {item.load_date}
        {:else}
          --
        {/if}
      </TableCell>
      <TableCell numCol={true} newCol={true}>{item.unprepared_ct}</TableCell>
      <TableCell numCol={true}>{item.prepared_ct}</TableCell>
      <TableCell numCol={true}>{item.layer_ct}</TableCell>
      <TableCell numCol={true}>{item.skip_ct}</TableCell>
      <TableCell numCol={true}>{item.nonmap_ct}</TableCell>
      <TableCell numCol={true} newCol={true}><div class="box" style="--p:{item.completion_pct};"></div></TableCell>
      <TableCell numCol={true} newCol={true}>{item.multimask_ct}/{item.main_layer_ct}</TableCell>
      <TableCell numCol={true} newCol={true}>
        {#if item.gt_exists}
          <span style="color:green">✓</span>
        {:else}
          <span style="color:red">x</span>
        {/if}
      </TableCell>
      <TableCell numCol={true}>
        {#if item.xyz_tiles_exists}
          <span style="color:green">✓</span>
        {:else}
          <span style="color:red">x</span>
        {/if}
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

  @media screen and (max-width: 768px) {
    .top-row {
      flex-direction: column;
      gap: .5em;
    }
    .top-row-right {
      justify-content: center;
    }
  }
  /* Credit to this SO answer: https://stackoverflow.com/a/52205730/3873885 */
  /* Could be revisited with other portion of that answer to add animation */
  .box {
    --v: calc(((18 / 5) * var(--p) - 90) * 1deg);
    display: inline-block;
    border-radius: 50%;
    padding: 10px;
    background:
    /* linear-gradient(#ccc,#ccc) content-box, */
      linear-gradient(var(--v), #e6e6e6 50%, transparent 0) 0 / min(100%, (50 - var(--p)) * 100%),
      linear-gradient(var(--v), transparent 50%, #123b4f 0) 0 / min(100%, (var(--p) - 50) * 100%),
      linear-gradient(to right, #e6e6e6 50%, #123b4f 0);
  }

  @-webkit-keyframes rotating /* Safari and Chrome */ {
    from {
      -webkit-transform: rotate(0deg);
      -o-transform: rotate(0deg);
      transform: rotate(0deg);
    }
    to {
      -webkit-transform: rotate(360deg);
      -o-transform: rotate(360deg);
      transform: rotate(360deg);
    }
  }
  @keyframes rotating {
    from {
      -ms-transform: rotate(0deg);
      -moz-transform: rotate(0deg);
      -webkit-transform: rotate(0deg);
      -o-transform: rotate(0deg);
      transform: rotate(0deg);
    }
    to {
      -ms-transform: rotate(360deg);
      -moz-transform: rotate(360deg);
      -webkit-transform: rotate(360deg);
      -o-transform: rotate(360deg);
      transform: rotate(360deg);
    }
  }
</style>
