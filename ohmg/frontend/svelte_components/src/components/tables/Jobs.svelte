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
  import RefreshButton from './widgets/RefreshButton.svelte';
  
  import { getFromAPI, submitPostRequest } from '../../lib/requests';
  import InfoModalButton from '../shared/buttons/InfoModalButton.svelte';
  import ModalConfirm from '../base/ModalConfirm.svelte';
  import { openModal } from '../base/Modal.svelte';

  import TableHeader from './layouts/TableHeader.svelte';
  import TableContainer from './layouts/TableContainer.svelte';
  import TableCell from './layouts/TableCell.svelte';
  import FilterRow from './layouts/FilterRow.svelte';
    import ShowFiltersButton from './widgets/ShowFiltersButton.svelte';

  export let CONTEXT;
  export let limit = '10';
  export let paginate = true;
  export let operationFilter = null;
  export let stageFilter = null;

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
      // items = [];
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
  yesButtonEnabled={CONTEXT.user.perms.includes("core.queue_mosaic_cog") || CONTEXT.user.perms.includes("core.queue_mosaic_xyz")}
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
  <div class="top-row">
    <div class="top-row-left">
      <ShowFiltersButton bind:showFilters/>
    </div>
    <div class="top-row-right">
      {#if paginate}
        <PaginationButtons bind:currentOffset={offset} bind:total bind:currentLimit />
      {/if}
      <RefreshButton
        onClick={triggerRefresh}
        bind:loading
      />
    </div>
  </div>
  <FilterRow {showFilters} bind:currentLimit >
    <FacetFilterSelect items={operationFilterItems} bind:value={operationFilter} placeholder="Set operation..." />
    <FacetFilterSelect items={stageFilterItems} bind:value={stageFilter} placeholder="Set stage..." />
  </FilterRow>
  <TableContainer bind:items bind:loading>
    <svelte:fragment slot="header-row">
      <TableHeader title="Id" />
      <TableHeader title="Target" />
      <TableHeader title="Operation" />
      <TableHeader title="Stage" />
      <TableHeader title="Queued" />
      <TableHeader title="Started" />
      <TableHeader title="Duration" />
    </svelte:fragment>
    <svelte:fragment slot="data-row" let:item>
      <TableCell numCol={true}>
        <button class="is-text-link" on:click={() => {
            jobDetails = item;
            openModal('modal-job-details')
          }}>
            {item.id}
        </button>
      </TableCell>
      <TableCell><Link href={item.target.url}>{item.target.name}</Link></TableCell>
      <TableCell><span class="tag is-small is-info is-light">{item.operation}</span></TableCell>
      <TableCell><span class="tag is-small {stageClass[item.stage]}">{item.stage}</span></TableCell>
      <TableCell tsCol={true} title={timestampToFullString(item.date_queued)}>{timestampToShortString(item.date_queued)}</TableCell>
      <TableCell tsCol={true} title={timestampToFullString(item.date_started)}>{timestampToShortString(item.date_started)}</TableCell>
      <TableCell tsCol={true}>{secondsToHHMMSS(item.run_duration)}</TableCell>
    </svelte:fragment>
  </TableContainer>
</div>

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
</style>
