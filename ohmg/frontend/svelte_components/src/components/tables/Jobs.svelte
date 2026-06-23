<script>
  import { slide } from 'svelte/transition';
  import { format } from 'date-fns';

  import Faders from 'phosphor-svelte/lib/Faders';

  import Link from '../base/Link.svelte';
  import SessionListModal from '../shared/modals/SessionListModal.svelte';

  import DatePicker from './widgets/DatePicker.svelte';
  import PaginationButtons from './widgets/PaginationButtons.svelte';
  import FacetFilterSelect from './widgets/FacetFilterSelect.svelte';
  import LimitSelect from './widgets/LimitSelect.svelte';
  import SortableHeader from './widgets/SortableHeader.svelte';
  import RefreshButton from './widgets/RefreshButton.svelte';

  import { getFromAPI, submitPostRequest } from '../../lib/requests';
  import InfoModalButton from '../shared/buttons/InfoModalButton.svelte';
    import ModalConfirm from '../base/ModalConfirm.svelte';
    import { openModal } from '../base/Modal.svelte';

  export let CONTEXT;
  export let limit = '10';
  export let paginate = true;
  export let allowRefresh = true;
  export let operationFilter = null;
  export let stageFilter = null;
  export let tableHeight = '100%';

  let operationFilterItems = [
    {"id":"layerset_to_cog", "label":"layerset_to_cog"},
    {"id":"layerset_to_xyz", "label":"layerset_to_xyz"},
  ];
  let stageFilterItems = [
    {"id":"queued", "label":"queued"},
    {"id":"running", "label":"running"},
    {"id":"completed", "label":"completed"},
    {"id":"errored", "label":"errored"},
  ];

  let loading = false;

  let items = [];

  let offset = 0;
  let total = 0;

  let currentLimit = limit;
  $: useLimit = typeof currentLimit == 'string' ? currentLimit : currentLimit.value;

  $: {
    loading = true;
    let fetchUrl = `/api/beta2/jobs/?offset=${offset}`;
    if (limit != 0 && useLimit) {
      fetchUrl = `${fetchUrl}&limit=${useLimit}`;
    }
    if (operationFilter) {
      fetchUrl += `&operation=${operationFilter.id}`;
    }
    if (stageFilter) {
      fetchUrl += `&stage=${stageFilter.id}`;
    }
    getFromAPI(fetchUrl, CONTEXT.ohmg_api_headers, (result) => {
      items = result.items;
      total = result.count;
      loading = false;
    });
  }

  let showFilters = false;

  function timestampToFullString(timestamp) {
    return timestamp ? new Date(timestamp * 1000).toLocaleString() : "--"
  }
  function timestampToShortString(timestamp) {
    if (!timestamp) { return "---"}
    const timestampMilli = timestamp * 1000
    if (Date.now() - 86400000 < timestampMilli) {
      return new Date(timestampMilli).toLocaleTimeString()
    } else {
      return new Date(timestampMilli).toLocaleDateString()
    }
  }

  function secondsToHHMMSS(seconds) {
    if (!seconds) {return "---"}
      return new Date(seconds * 1000).toISOString().substring(11, 19)
  }

  const stageClass = {
    "queued": "is-info",
    "running": "is-warning",
    "completed": "is-success",
    "errored": "is-danger",
  }

  let jobDetails

  function triggerRefresh(response) {
    offset = 1000;
    offset = 0;
  }

  function submitJobToQueue() {
    console.log(jobDetails.id)
    submitPostRequest(
      `/job/${jobDetails.id}/`,
      CONTEXT.ohmg_post_headers,
      'queue',
      {},
      triggerRefresh,
    );
  }
</script>

<ModalConfirm id="modal-job-details"
  yesAction={submitJobToQueue}
  yesButtonText="Re-queue job"
  noButtonText="Close"
>
  <dl>
    {#if jobDetails}
    <dt>id</dt>
    <dd>{jobDetails.id}</dd>
    <dt>operation</dt>
    <dd>{jobDetails.operation}</dd>
    <dt>stage</dt>
    <dd>{jobDetails.stage}</dd>
    <dt>message</dt>
    <dd>{jobDetails.message}</dd>
    <dt>target</dt>
    <dd>{jobDetails.target.name}</dd>
    <dt>date_created</dt>
    <dd>{timestampToFullString(jobDetails.date_created)}</dd>
    <dt>date_queued</dt>
    <dd>{timestampToFullString(jobDetails.date_queued)}</dd>
    <dt>date_started</dt>
    <dd>{timestampToFullString(jobDetails.date_started)}</dd>
    <dt>date_ended</dt>
    <dd>{timestampToFullString(jobDetails.date_ended)}</dd>
    <dt>run_duration (seconds)</dt>
    <dd>{jobDetails.run_duration}</dd>
    {/if}
  </dl>

</ModalConfirm>
<div>
  <div class="level is-mobile" style="margin:.5em 0;">
    <div class="level-left">
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
          onClick={triggerRefresh}
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
        <FacetFilterSelect items={operationFilterItems} bind:value={operationFilter} placeholder="Filter by operation..." />
        <FacetFilterSelect items={stageFilterItems} bind:value={stageFilter} placeholder="Filter by stage..." />
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
              <th>Id</th>
              <th>Target</th>
              <th>Operation</th>
              <th>Stage</th>
              <th>Queued</th>
              <th>Started</th>
              <th>Duration</th>
            </tr>
          </thead>
          <tbody>
            {#each items as s}
              <tr style="height:38px; vertical-align:center;">
                <td><button class="is-text-link" on:click={() => {
                  jobDetails = s;
                  openModal('modal-job-details')
                }}>
                  {s.id}
              </button></td>
                <td><Link href={s.target.url}>{s.target.name}</Link></td>
                <td><span class="tag is-small is-info is-light">{s.operation}</span></td>
                <td><span class="tag is-small {stageClass[s.stage]}">{s.stage}</span></td>
                <td class="ts-col" title={timestampToFullString(s.date_queued)}>{timestampToShortString(s.date_queued)}</td>
                <td class="ts-col" title={timestampToFullString(s.date_started)}>{timestampToShortString(s.date_started)}</td>
                <td class="ts-col" >{secondsToHHMMSS(s.run_duration)}</td>
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
  td.ts-col {
    font-size: .85em;
    text-align: center;
  }
  .table-container {
    overflow-y: auto;
  }
  .thumb-container {
    width: 65px;
    display: inline-block;
    text-align: center;
  }
  dl {
      background-color: #ffffff;
  }
  dt, dd {
      padding-top: .25em;
      padding-bottom: .25em;
  }
  dt {
      font-weight: 700;
      font-size: .85em;
      background-color: #f6f6f6;
      padding-left: .5em;
  }
  dd {
      padding-left: 1em;
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
