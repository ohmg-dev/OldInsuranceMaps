<script>
  import LoadingEllipsis from '../common/LoadingEllipsis.svelte';

  import MapItem from '../cards/MapItem.svelte';

  import { getFromAPI } from '../../lib/requests';

  export let CONTEXT;

  let loadingItems = false;
  let latestItems = [];

  function getInitialResults() {
    loadingItems = true;
    getFromAPI(
      '/api/beta2/maps2/?limit=5&sort=desc&sortby=load_date&loaded=true',
      CONTEXT.ohmg_api_headers,
      (result) => {
        latestItems = result.items;
        loadingItems = false;
      },
    );
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
