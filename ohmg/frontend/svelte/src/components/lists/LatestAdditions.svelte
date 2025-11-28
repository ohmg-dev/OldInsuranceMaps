<script>
  import LoadingEllipsis from '../common/LoadingEllipsis.svelte';

  import MapItem from '../cards/MapItem.svelte';

  import { getFromAPI } from '../../lib/requests';

  export let CONTEXT;

  let loadingItems = false;
  let latestItems = [];

  function getInitialResults() {
    loadingItems = true;
    getFromAPI('/api/beta2/maps/?limit=5&sort=load_date', CONTEXT.ohmg_api_headers, (result) => {
      latestItems = result;
      loadingItems = false;
    });
  }
  getInitialResults();
</script>

<div>
  {#if loadingItems}
    <LoadingEllipsis />
  {:else}
    {#each latestItems as MAP}
      <MapItem {MAP} />
    {/each}
  {/if}
</div>
