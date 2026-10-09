<script>
  import Link from '../base/Link.svelte';
  import SessionListModal from '../shared/modals/SessionListModal.svelte';

  import PaginationButtons from './widgets/PaginationButtons.svelte';

  import { getFromAPI } from '../../lib/requests';
  import InfoModalButton from '../shared/buttons/InfoModalButton.svelte';
  import RefreshButton from './widgets/RefreshButton.svelte';

  import TableContainer from './layouts/TableContainer.svelte';
  import TableHeader from './layouts/TableHeader.svelte';
  import TableCell from './layouts/TableCell.svelte';

  export let CONTEXT;
  export let limit = '50';
  export let paginate = true;
  export let sortParam = 'username';
  export let sortDir = 'asc';

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

</script>

<SessionListModal id={'modal-session-list'} />
<div>
  <div class="level is-mobile" style="margin:.5em 0;">
    <div class="level-left">
      <InfoModalButton modalId="modal-session-list" />
      <RefreshButton
        onClick={() => {
          offset = 1000;
          offset = 0;
        }}
        bind:loading
      />
    </div>
    <div class="level-right">
      {#if paginate}
        <div class="level-item">
          <PaginationButtons bind:currentOffset={offset} bind:total bind:currentLimit />
        </div>
      {/if}
    </div>
  </div>
  <TableContainer bind:items bind:loading>
    <svelte:fragment slot="header-row">
      <TableHeader title="Username" bind:sortDir bind:sortParam bind:offset value={'username'} />
      <TableHeader title="Date joined" bind:sortDir bind:sortParam value={'date_joined'} />
      <TableHeader title="Loaded" newCol={true} bind:sortDir bind:sortParam value={'load_ct'} />
      <TableHeader
          title="Prep"
          alt="Number of preparation sessions"
          value={'psesh_ct'}
          bind:sortDir
          bind:sortParam
        />
      <TableHeader
          title="Georef"
          alt="Number of georeferencing sessions"
          value={'gsesh_ct'}
          bind:sortDir
          bind:sortParam
        />
      <TableHeader
          title="GCPs"
          alt="Number of georeferenced layers"
          value={'gcp_ct'}
          bind:sortDir
          bind:sortParam
        />
    </svelte:fragment>
    <svelte:fragment slot="data-row" let:item>
      <TableCell>
        <img src={item.image_url} alt={item.username} />
        <Link href={`/profile/${item.username}`}>{item.username}</Link>
      </TableCell>
      <TableCell>
        {item.date_joined}
      </TableCell>
      <TableCell numCol={true} newCol={true}>{item.load_ct}</TableCell>
      <TableCell numCol={true}>{item.psesh_ct}</TableCell>
      <TableCell numCol={true}>{item.gsesh_ct}</TableCell>
      <TableCell numCol={true}>{item.gcp_ct}</TableCell>
    </svelte:fragment>
  </TableContainer>
</div>

<style>
  .level.is-mobile > .level-left {
    flex-direction: row;
  }
  img {
    margin-right: 0.5em;
    height: 30px;
    width: 30px;
    border-radius: 5px;
  }
</style>
