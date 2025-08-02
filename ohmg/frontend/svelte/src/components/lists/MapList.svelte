<script>
  import { slide } from 'svelte/transition';
  import Select from 'svelte-select';
  import { format } from 'date-fns';

  import ArrowsClockwise from 'phosphor-svelte/lib/ArrowsClockwise';
  import Faders from 'phosphor-svelte/lib/Faders';

  import Link from '../common/Link.svelte';
  import SessionListModal from '../modals/SessionListModal.svelte';

  import PaginationButtons from '../buttons/PaginationButtons.svelte';

  import { getFromAPI } from '../../lib/requests';
  import InfoModalButton from '../buttons/InfoModalButton.svelte';
  import SortButton from '../buttons/SortButton.svelte';

  export let CONTEXT;
  export let limit = '50';
  export let paginate = true;
  export let allowRefresh = true;
  export let showPlace = true;
  export let placeFilter = null;
  export let placeInclusive = false;
  export let sortParam = 'title';
  export let sortDir = 'asc';

  let placeFilterItems = [];

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
    if (placeInclusive) {
      fetchUrl += `&place_inclusive=true`;
    }
    if (sortParam) {
      fetchUrl += `&sortby=${sortParam}&sort=${sortDir}`;
    }
    getFromAPI(fetchUrl, CONTEXT.ohmg_api_headers, (result) => {
      items = result.items;
      total = result.count;
      placeFilterItems = result.filter_items.places;
      loading = false;
    });
  }

  let showFilters = false;
  let limitOptions = [10, 25, 50, 100];
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
        <button
          class="is-icon-link"
          title={loading ? 'Loading...' : 'Refresh'}
          disabled={loading}
          on:click={() => {
            offset = 1000;
            offset = 0;
          }}
        >
          <div style="height:28px" class={loading ? 'rotating' : ''}>
            <ArrowsClockwise />
          </div>
        </button>
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
        {#if showPlace}
          <Select
            items={placeFilterItems}
            bind:value={placeFilter}
            placeholder="Filter by place..."
            listAutoWidth={false}
            class="filter-input"
            containerStyles="width:300px;"
            on:change={() => {
              offset = 0;
            }}
          />
        {/if}
      </div>
      <div class="filter-level level-right">
        <Select
          items={limitOptions}
          bind:value={currentLimit}
          class="filter-input"
          searchable={false}
          clearable={false}
          listAutoWidth={false}
        />
      </div>
    </div>
  {/if}
  <div style="height: 100%; overflow-y:auto; border:1px solid #ddd; border-radius:4px; background:white;">
    {#if items.length > 0}
      <table>
        <thead>
          <tr>
            <th><SortButton title="Title" bind:sortDir bind:sortParam bind:offset value={'title'} /></th>
            <th><SortButton title="Year" bind:sortDir bind:sortParam value={'year'} /></th>
            <th
              ><SortButton
                title="Docs"
                alt="Sort by number of documents"
                bind:sortDir
                bind:sortParam
                value={'document_ct'}
              /></th
            >
            {#if showPlace}
              <th title="Place" style="font-weight:400">Place</th>
            {/if}
            <th title="Loaded by" style="font-weight:400">Loaded by</th>
            <th><SortButton title="Date" bind:sortDir bind:sortParam value={'load_date'} /></th>
            <th class="number-col new-col">
              <SortButton title="U" bind:sortDir bind:sortParam value={'unprepared_ct'} />
            </th>
            <th class="number-col"
              ><SortButton
                title="P"
                alt="Number of prepared regions"
                bind:sortDir
                bind:sortParam
                value={'prepared_ct'}
              /></th
            >
            <th class="number-col"
              ><SortButton
                title="G"
                alt="Number of georeferenced layers"
                bind:sortDir
                bind:sortParam
                value={'layer_ct'}
              /></th
            >
            <th class="number-col"
              ><SortButton title="S" alt="Number of skipped pieces" bind:sortDir bind:sortParam value={'skip_ct'} /></th
            >
            <th class="number-col"
              ><SortButton
                title="N"
                alt="Number of non-map pieces"
                bind:sortDir
                bind:sortParam
                value={'nonmap_ct'}
              /></th
            >
            <th class="number-col new-col"
              ><SortButton
                title="%"
                alt="Percent complete - G/(U+P+G)"
                bind:sortDir
                bind:sortParam
                value={'completion_pct'}
              /></th
            >
            <th class="number-col new-col" title="Layers included in multimask"
              ><SortButton
                title="MM"
                alt="Main content layers included in multimask"
                bind:sortDir
                bind:sortParam
                value={'multimask_rank'}
              /></th
            >
            <th
              class="number-col new-col"
              title="A geotiff has been created for this map's main content"
              style="font-weight:400;">GT</th
            >
          </tr>
        </thead>
        <tbody>
          {#each items as s}
            <tr style="height:38px; vertical-align:center;">
              <td><Link href={`/map/${s.identifier}`}>{s.title}</Link></td>
              <td>{s.year}</td>
              <td>{s.document_ct}</td>
              {#if showPlace}
                <td
                  ><Link href={`/${s.locale.slug}`} title={`View all ${s.locale.display_name} maps`}
                    >{s.locale.display_name}</Link
                  ></td
                >
              {/if}
              <td>
                {#if s.loaded_by}
                  <Link href={s.loaded_by.profile_url} title="View profile">{s.loaded_by.username}</Link>
                {:else}
                  --
                {/if}
              </td>
              <td>
                {#if s.load_date}
                  {s.load_date}
                {:else}
                  --
                {/if}
              </td>
              <td class="number-col new-col">{s.unprepared_ct}</td>
              <td class="number-col">{s.prepared_ct}</td>
              <td class="number-col">{s.layer_ct}</td>
              <td class="number-col">{s.skip_ct}</td>
              <td class="number-col">{s.nonmap_ct}</td>
              <td class="number-col new-col"><div class="box" style="--p:{s.completion_pct};"></div></td>
              <td class="number-col new-col">{s.multimask_ct}/{s.layer_ct}</td>
              <td class="number-col new-col"
                >{#if s.gt_exists}
                  <span style="color:green">✓</span>
                {:else}
                  <span style="color:red">x</span>
                {/if}</td
              >
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
  .number-col {
    padding: 0;
    width: 25px;
    text-align: center;
  }
  .new-col {
    border-left: 1px solid gray;
  }
  @media screen and (max-width: 768px) {
    .filter-level,
    :global(.filter-input),
    :global(.date-filter),
    :global(button.date-field) {
      min-width: 100% !important;
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
  .rotating {
    -webkit-animation: rotating 2s linear infinite;
    -moz-animation: rotating 2s linear infinite;
    -ms-animation: rotating 2s linear infinite;
    -o-animation: rotating 2s linear infinite;
    animation: rotating 2s linear infinite;
  }
</style>
