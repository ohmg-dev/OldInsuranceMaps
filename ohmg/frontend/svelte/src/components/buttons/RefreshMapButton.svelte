<script>
  import LoadingEllipsis from '../common/LoadingEllipsis.svelte';

  export let handleRefresh;
  export let label = 'click to refresh content';
  export let delayRefresh = true;

  let enableRefresh = false;
  $: {
    if (delayRefresh) {
      setTimeout(() => {
        enableRefresh = true;
      }, 3000);
    } else {
      enableRefresh = true;
    }
  }
</script>

<div style="display:flex; align-items:end; z-index:10000; height:2em; margin-right:auto; margin-left:auto;">
  <button on:click={handleRefresh} disabled={!enableRefresh} class="button" style="height:1.5em; border-radius:2px; background:#123b4f; color:white; display:flex; align-items:center; padding: 5px;">
    {#if enableRefresh}
      {label}
    {:else}
      <LoadingEllipsis color="white" />
    {/if}
  </button>
</div>
