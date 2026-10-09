<script>
  import { format } from 'date-fns';

  import Link from '../base/Link.svelte';
  import SessionListModal from '../shared/modals/SessionListModal.svelte';

  import DatePicker from './widgets/DatePicker.svelte';
  import PaginationButtons from './widgets/PaginationButtons.svelte';
  import FacetFilterSelect from './widgets/FacetFilterSelect.svelte';
  import RefreshButton from './widgets/RefreshButton.svelte';

  import FilterRow from './layouts/FilterRow.svelte';
  import TableContainer from './layouts/TableContainer.svelte';
  import TableHeader from './layouts/TableHeader.svelte';
  import TableCell from './layouts/TableCell.svelte';

  import { getFromAPI } from '../../lib/requests';
  import InfoModalButton from '../shared/buttons/InfoModalButton.svelte';
  import ShowFiltersButton from './widgets/ShowFiltersButton.svelte';

  export let CONTEXT;
  export let FILTER_PARAM = '';
  export let limit = '25';
  export let showThumbs = false;
  export let showUser = true;
  export let userFilter = null;
  export let showResource = true;
  export let paginate = true;
  export let showTypeFilter = true;
  export let typeFilter = null;
  export let showMap = true;
  export let mapFilter = null;
  export let sortParam = 'id';
  export let sortDir = 'des';

  export let includeFilters = true;

  let userFilterItems = [];
  let mapFilterItems = [];
  let typeFilterItems = [];

  let loading = false;

  let items = [];

  let startDate;
  let endDate;

  let offset = 0;
  let total = 0;

  let currentLimit = limit;
  $: useLimit = typeof currentLimit == 'string' ? currentLimit : currentLimit.value;

  let dateFormat = 'yyyy-MM-dd';
  const formatDate = (dateString) => (dateString && format(new Date(dateString), dateFormat)) || '';

  $: formattedStartDate = formatDate(startDate);
  $: formattedEndDate = formatDate(endDate);

  $: dqParam = formattedStartDate && formattedEndDate ? `&date_range=${formattedStartDate},${formattedEndDate}` : '';

  $: {
    loading = true;
    let fetchUrl = `/api/beta2/sessions/?offset=${offset}`;
    if (limit != 0 && useLimit) {
      fetchUrl = `${fetchUrl}&limit=${useLimit}`;
    }
    // ultimately should deprecate this and move its functionality into this component
    if (FILTER_PARAM) {
      fetchUrl += `&${FILTER_PARAM}`;
    }
    if (typeFilter) {
      fetchUrl += `&type=${typeFilter.id}`;
    }
    if (mapFilter) {
      fetchUrl += `&map=${mapFilter.id}`;
    }
    if (dqParam) {
      fetchUrl += dqParam;
    }
    if (userFilter) {
      fetchUrl += `&username=${userFilter.id}`;
    }
    if (sortParam) {
      fetchUrl += `&sortby=${sortParam}&sort=${sortDir}`;
    }
    getFromAPI(fetchUrl, CONTEXT.ohmg_api_headers, (result) => {
      items = result.items;
      total = result.count;
      typeFilterItems = result.filter_items.types;
      userFilterItems = result.filter_items.users;
      mapFilterItems = result.filter_items.maps;
      loading = false;
    });
  }

  let showFilters = false;
</script>

<SessionListModal id={'modal-session-list'} />
<section class="table-section">
  <div class="top-row">
    <div class="top-row-left">
      {#if includeFilters}
        <ShowFiltersButton bind:showFilters />
      {/if}
    </div>
    <div class="top-row-right">
      {#if paginate}
        <PaginationButtons bind:currentOffset={offset} bind:total bind:currentLimit />
      {/if}
      <InfoModalButton modalId="modal-session-list" />
      <RefreshButton
        onClick={() => {
          offset = 1000;
          offset = 0;
        }}
        bind:loading
      />
    </div>
  </div>
  {#if includeFilters}
    <FilterRow {showFilters} bind:currentLimit>
      {#if showTypeFilter}
        <FacetFilterSelect items={typeFilterItems} bind:value={typeFilter} placeholder="Set type..." />
      {/if}
      {#if showUser}
        <FacetFilterSelect items={userFilterItems} bind:value={userFilter} placeholder="Set user..." />
      {/if}
      {#if showMap}
        <FacetFilterSelect items={mapFilterItems} bind:value={mapFilter} placeholder="Set map..." />
      {/if}
      <DatePicker bind:startDate bind:endDate />
    </FilterRow>
  {/if}
  <TableContainer bind:items bind:loading>
    <svelte:fragment slot="header-row">
      <TableHeader title="Id" value={'id'} bind:sortDir bind:sortParam bind:offset />
      <TableHeader title="Type" value={'type'} bind:sortDir bind:sortParam bind:offset />
      {#if showUser}
        <TableHeader title="User" value={'user'} bind:sortDir bind:sortParam bind:offset />
      {/if}
      {#if showMap}
        <TableHeader title="Map" />
      {/if}
      {#if showResource}
        <TableHeader title="Resource" alt="Document, Region, or Layer for this work" bind:toggleVar={showThumbs}/>
      {/if}
      <TableHeader title="Stage" value={'stage'} bind:sortDir bind:sortParam bind:offset />
      <TableHeader title="Result" value={'note'} bind:sortDir bind:sortParam bind:offset />
      <TableHeader title="Duration" value={'duration'} bind:sortDir bind:sortParam bind:offset />
      <TableHeader title="Date" value={'date_created'} bind:sortDir bind:sortParam bind:offset />
    </svelte:fragment>
    <svelte:fragment slot="data-row" let:item>
      <TableCell>{item.id}</TableCell>
      <TableCell>
        {#if item.type === 'p'}
          <span title="Preparation">Prep</span>
        {:else if item.type === 'g'}
          <span title="Georeference">Georef</span>
        {:else if item.type === 't'}
          <span title="Trim">Trim</span>
        {/if}
      </TableCell>
      {#if showUser}
        <TableCell>
          <Link href={item.user.profile_url} title="View profile">{item.user.username}</Link>
        </TableCell>
      {/if}
      {#if showMap}
        <TableCell>
          {#if item.map}
            <Link href={`/map/${item.map.identifier}`} title={item.map.title}>{item.map.title}</Link>
          {:else}
            Error: no map
          {/if}
        </TableCell>
      {/if}
      {#if showResource}
        <TableCell>
          {#if item.type === 'p'}
            {#if item.doc2}
              {#if showThumbs}
                <div class="thumb-container">
                  <img src={item.doc2.urls.thumbnail} alt={item.doc2.nickname} />
                </div>
              {/if}
              <Link href={item.doc2.urls.resource} title={item.doc2.nickname}>
                {item.doc2.nickname}
              </Link>
            {:else}
              Error: no document
            {/if}
          {:else if item.type === 'g' || item.type === 't'}
            {#if item.lyr2}
              {#if showThumbs}
                <div class="thumb-container">
                  <img src={item.lyr2.urls.thumbnail} alt={item.reg2.nickname} />
                </div>
              {/if}
              <Link href={item.lyr2.urls.resource} title={item.lyr2.nickname}>
                {item.lyr2.nickname}
              </Link>
            {:else}
              Error: no layer
            {/if}
          {/if}
        </TableCell>
      {/if}
      <TableCell>{item.stage}</TableCell>
      <TableCell>{item.note}</TableCell>
      <TableCell title={`${item.duration.seconds} seconds`}>
        {#if item.duration}
          {item.duration.humanized}
        {:else}
          Error: not recorded
        {/if}
      </TableCell>
      <TableCell title={item.date_created.date}>{item.date_created.relative}</TableCell>
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
</style>
