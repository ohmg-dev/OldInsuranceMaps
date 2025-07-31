<script>
  import SortAscending from 'phosphor-svelte/lib/SortAscending';
  import SortDescending from 'phosphor-svelte/lib/SortDescending';
  export let title = '';
  export let value = '';
  export let sortParam = null;
  export let sortDir = 'des';
</script>

<button
  title={`Sort by ${value}`}
  on:click={() => {
    sortParam = value;
    sortDir = sortDir == 'des' ? 'asc' : 'des';
  }}
>
  <span style={value != sortParam ? 'margin-right: 1em;' : ''}>{title}</span>
  {#if value == sortParam}
    {#if sortDir == 'des'}
      <SortAscending />
    {:else}
      <SortDescending />
    {/if}
  {/if}
</button>

<style>
  button {
    display: flex;
    padding-left: 0.5em;
  }
  button:hover {
    background: #f7f1e1;
    color: #333;
    box-shadow: gray 0px 0px 5px;
  }
</style>
