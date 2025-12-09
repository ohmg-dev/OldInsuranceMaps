<script>
  import { slide } from 'svelte/transition';
  import { format } from 'date-fns';

  import ArrowsClockwise from 'phosphor-svelte/lib/ArrowsClockwise';
  import Faders from 'phosphor-svelte/lib/Faders';

  import Link from '../common/Link.svelte';
  import SessionListModal from '../modals/SessionListModal.svelte';

  import DatePicker from './widgets/DatePicker.svelte';
  import PaginationButtons from './widgets/PaginationButtons.svelte';
  import FacetFilterSelect from './widgets/FacetFilterSelect.svelte';
  import LimitSelect from './widgets/LimitSelect.svelte';
  import SortableHeader from './widgets/SortableHeader.svelte';
  import RefreshButton from './widgets/RefreshButton.svelte';

  import { getFromAPI } from '../../lib/requests';
  import InfoModalButton from '../buttons/InfoModalButton.svelte';

  export let CONTEXT;
  export let FILTER_PARAM = '';
  export let limit = '10';
  export let showThumbs = false;
  export let showUser = true;
  export let userFilter = null;
  export let showResource = true;
  export let paginate = true;
  export let allowRefresh = true;
  export let showTypeFilter = true;
  export let typeFilter = null;
  export let showMap = true;
  export let mapFilter = null;
  export let sortParam = 'id';
  export let sortDir = 'des';
  export let tableHeight = '100%';

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
      {#if paginate}
        <div class="level-item">
          <PaginationButtons bind:currentOffset={offset} bind:total bind:currentLimit />
        </div>
      {/if}
    </div>
  </div>
  {#if showFilters}
    <div transition:slide class="level" style="margin:.5em 0;">
      <div id="" class="filter-level level-left">
        {#if showTypeFilter}
          <FacetFilterSelect items={typeFilterItems} bind:value={typeFilter} placeholder="Filter by type..." />
        {/if}
        {#if showUser}
          <FacetFilterSelect items={userFilterItems} bind:value={userFilter} placeholder="Filter by user..." />
        {/if}
        {#if showMap}
          <FacetFilterSelect items={mapFilterItems} bind:value={mapFilter} placeholder="Filter by map..." />
        {/if}
        <DatePicker bind:startDate bind:endDate />
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
              <th><SortableHeader title="Type" value={'type'} bind:sortDir bind:sortParam bind:offset /></th>
              {#if showUser}
                <th><SortableHeader title="User" value={'user'} bind:sortDir bind:sortParam bind:offset /></th>
              {/if}
              {#if showMap}
                <th><SortableHeader title="Map" /></th>
              {/if}
              {#if showResource}
                <th title="Document, Region, or Layer for this work">
                  <div>
                    <span style="font-weight:400; margin-right:.5em;">Resource</span><input
                      type="checkbox"
                      bind:checked={showThumbs}
                      title="Show thumbnails"
                    />
                  </div>
                </th>
              {/if}
              <th><SortableHeader title="Stage" value={'stage'} bind:sortDir bind:sortParam bind:offset /></th>
              <th><SortableHeader title="Result" value={'note'} bind:sortDir bind:sortParam bind:offset /></th>
              <th><SortableHeader title="Duration" value={'duration'} bind:sortDir bind:sortParam bind:offset /></th>
              <th><SortableHeader title="Date" value={'date_created'} bind:sortDir bind:sortParam bind:offset /></th>
            </tr>
          </thead>
          <tbody>
            {#each items as s}
              <tr style="height:38px; vertical-align:center;">
                <td>{s.id}</td>
                <td>
                  {#if s.type === 'p'}
                    <span title="Preparation">Prep</span>
                  {:else if s.type === 'g'}
                    <span title="Georeference">Georef</span>
                  {:else if s.type === 't'}
                    <span title="Trim">Trim</span>
                  {/if}
                </td>
                {#if showUser}
                  <td>
                    <Link href={s.user.profile_url} title="View profile">{s.user.username}</Link>
                  </td>
                {/if}
                {#if showMap}
                  <td>
                    {#if s.map}
                      <Link href={`/map/${s.map.identifier}`} title={s.map.title}>{s.map.title}</Link>
                    {:else}
                      Error: no map
                    {/if}
                  </td>
                {/if}
                {#if showResource}
                  <td>
                    {#if s.type === 'p'}
                      {#if s.doc2}
                        {#if showThumbs}
                          <div class="thumb-container">
                            <img style="max-height:50px;" src={s.doc2.urls.thumbnail} alt={s.doc2.nickname} />
                          </div>
                        {/if}
                        <Link href={s.doc2.urls.resource} title={s.doc2.nickname}>
                          {s.doc2.nickname}
                        </Link>
                      {:else}
                        Error: no document
                      {/if}
                    {:else if s.type === 'g' || s.type === 't'}
                      {#if s.lyr2}
                        {#if showThumbs}
                          <div class="thumb-container">
                            <img style="max-height:50px;" src={s.lyr2.urls.thumbnail} alt={s.reg2.nickname} />
                          </div>
                        {/if}
                        <Link href={s.lyr2.urls.resource} title={s.lyr2.nickname}>
                          {s.lyr2.nickname}
                        </Link>
                      {:else}
                        Error: no layer
                      {/if}
                    {/if}
                  </td>
                {/if}
                <td>{s.stage}</td>
                <td>{s.note}</td>
                <td title={`${s.duration.seconds} seconds`}>
                  {#if s.duration}
                    {s.duration.humanized}
                  {:else}
                    Error: not recorded
                  {/if}
                </td>
                <td title={s.date_created.date}>{s.date_created.relative}</td>
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
  th > * {
    display: flex;
  }
  td {
    white-space: nowrap;
    padding: 2px 0.5em 2px 0;
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
  @media screen and (max-width: 768px) {
    .filter-level,
    :global(.filter-input),
    :global(.date-filter),
    :global(button.date-field) {
      min-width: 100% !important;
    }
  }
</style>
