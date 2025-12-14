<script>
  import { slide } from 'svelte/transition';
  import Select from 'svelte-select';
  import { format } from 'date-fns';

  import ArrowsClockwise from 'phosphor-svelte/lib/ArrowsClockwise';
  import Faders from 'phosphor-svelte/lib/Faders';

  import Link from '../common/Link.svelte';
  import SessionListModal from '../modals/SessionListModal.svelte';

  import PaginationButtons from './widgets/PaginationButtons.svelte';

  import { getFromAPI } from '../../lib/requests';
  import InfoModalButton from '../buttons/InfoModalButton.svelte';
  import LimitSelect from './widgets/LimitSelect.svelte';
  import SortableHeader from './widgets/SortableHeader.svelte';
  import RefreshButton from './widgets/RefreshButton.svelte';

  export let CONTEXT;
  export let limit = '50';
  export let paginate = true;
  export let allowRefresh = true;
  export let sortParam = 'username';
  export let sortDir = 'asc';
  export let showMapsLoaded = true;

  let loading = false;

  let items = [];

  let offset = 0;
  let total = 0;

  let currentLimit = limit;
  $: useLimit = typeof currentLimit == 'string' ? currentLimit : currentLimit.value;

  $: {
    loading = true;
    let fetchUrl = `/api/beta2/profiles/?offset=${offset}`;
    if (limit != 0 && useLimit) {
      fetchUrl = `${fetchUrl}&limit=${useLimit}`;
    }
    if (sortParam) {
      fetchUrl += `&sortby=${sortParam}&sort=${sortDir}`;
    }
    getFromAPI(fetchUrl, CONTEXT.ohmg_api_headers, (result) => {
      items = result.items;
      total = result.count;
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
      <div class="filter-level level-right">
        <LimitSelect bind:value={currentLimit} />
      </div>
    </div>
  {/if}
  <div style="height: 100%; overflow-y:auto; border:1px solid #ddd; border-radius:4px; background:white;">
    {#if items.length > 0}
      <table>
        <thead>
          <tr>
            <th><SortableHeader title="Username" bind:sortDir bind:sortParam bind:offset value={'username'} /></th>
            <th><SortableHeader title="Date joined" bind:sortDir bind:sortParam value={'date_joined'} /></th>
            {#if showMapsLoaded}
              <th class="num-col new-col"
                ><SortableHeader title="Loaded" bind:sortDir bind:sortParam value={'load_ct'} />
              </th>{/if}
            <th class="num-col{showMapsLoaded ? '' : ' new-col'}"
              ><SortableHeader
                title="Prep"
                alt="Number of preparation sessions"
                value={'psesh_ct'}
                bind:sortDir
                bind:sortParam
              />
            </th><th class="num-col"
              ><SortableHeader
                title="Georef"
                alt="Number of georeferencing sessions"
                value={'gsesh_ct'}
                bind:sortDir
                bind:sortParam
              />
            </th><th class="num-col"
              ><SortableHeader
                title="GCPs"
                alt="Number of georeferenced layers"
                value={'gcp_ct'}
                bind:sortDir
                bind:sortParam
              />
            </th></tr
          >
        </thead>
        <tbody>
          {#each items as s}
            <tr style="height:38px; vertical-align:center;">
              <td
                ><img src={s.image_url} alt={s.username} /><Link href={`/profile/${s.username}`}>{s.username}</Link></td
              >
              <td>
                {s.date_joined}
              </td>
              {#if showMapsLoaded}
                <td class="num-col new-col">{s.load_ct}</td>
              {/if}
              <td class="num-col">{s.psesh_ct}</td>
              <td class="num-col">{s.gsesh_ct}</td>
              <td class="num-col">{s.gcp_ct}</td>
            </tr>
          {/each}
        </tbody>
      </table>
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
  td {
    white-space: nowrap;
    padding-left: 0.5em;
    vertical-align: middle;
  }
  td img {
    margin-right: 0.5em;
    height: 30px;
    width: 30px;
    border-radius: 5px;
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
