<script>
  import { getFromAPI } from '../../lib/requests';

  import Link from '../base/Link.svelte';
  import SessionListModal from '../shared/modals/SessionListModal.svelte';

  import RefreshButton from './widgets/RefreshButton.svelte';

  import TableContainer from './layouts/TableContainer.svelte';
  import TableHeader from './layouts/TableHeader.svelte';
  import TableCell from './layouts/TableCell.svelte';

  export let CONTEXT;
  export let mapId;
  export let sortParam = 'username';
  export let sortDir = 'asc';

  let loading = false;

  let items = [];

  let total = 0;

  $: {
    loading = true;
    let fetchUrl = `/map/${mapId}/contributors?`;
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
      <RefreshButton
        onClick={() => {
          const oldSort = sortParam;
          sortParam = null;
          sortParam = oldSort;
        }}
        bind:loading
      />
    </div>
    <div class="level-right"></div>
  </div>
  <TableContainer bind:items bind:loading>
    <svelte:fragment slot="header-row">
      <TableHeader title="User" bind:sortDir bind:sortParam value={'username'} />
      <TableHeader
          title="Prep"
          alt="Number of preparation sessions"
          value={'psesh_ct'}
          newCol={true}
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
          alt="Number of ground control points created"
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
      <TableCell numCol={true} newCol={true}>{item.psesh_ct}</TableCell>
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
