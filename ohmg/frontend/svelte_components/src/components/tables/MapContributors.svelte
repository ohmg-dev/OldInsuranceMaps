<script>
  import Link from '../common/Link.svelte';
  import SessionListModal from '../modals/SessionListModal.svelte';

  import { getFromAPI } from '../../lib/requests';
  import SortableHeader from './widgets/SortableHeader.svelte';
  import RefreshButton from './widgets/RefreshButton.svelte';

  export let CONTEXT;
  export let mapId;
  export let allowRefresh = true;
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
      {#if allowRefresh}
        <RefreshButton
          onClick={() => {
            const oldSort = sortParam;
            sortParam = null;
            sortParam = oldSort;
          }}
          bind:loading
        />
      {/if}
    </div>
    <div class="level-right"></div>
  </div>
  <div style="height: 100%; overflow-y:auto; border:1px solid #ddd; border-radius:4px; background:white;">
    {#if items.length > 0}
      <table>
        <thead>
          <tr>
            <th><SortableHeader title="User" bind:sortDir bind:sortParam value={'username'} /></th>
            <th class="num-col new-col"
              ><SortableHeader
                title="Prep"
                alt="Number of preparation sessions"
                value={'psesh_ct'}
                bind:sortDir
                bind:sortParam
              /></th
            >
            <th class="num-col"
              ><SortableHeader
                title="Georef"
                alt="Number of georeferencing sessions"
                value={'gsesh_ct'}
                bind:sortDir
                bind:sortParam
              /></th
            >
            <th class="num-col"
              ><SortableHeader
                title="GCPs"
                alt="Number of ground control points created"
                value={'gcp_ct'}
                bind:sortDir
                bind:sortParam
              /></th
            >
          </tr>
        </thead>
        <tbody>
          {#each items as s}
            <tr style="height:38px; vertical-align:center;">
              <td
                ><img src={s.image_url} alt={s.username} /><Link href={`/profile/${s.username}`}>{s.username}</Link></td
              >
              <td class="num-col new-col">{s.psesh_ct}</td>
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
