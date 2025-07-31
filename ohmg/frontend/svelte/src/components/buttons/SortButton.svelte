<script>
  import SortAscending from 'phosphor-svelte/lib/SortAscending';
  import SortDescending from 'phosphor-svelte/lib/SortDescending';
  export let title = '';
  export let value = '';
  export let sortParam = null;
  export let sortDir = 'asc';

  $: active = sortParam == value;
</script>

<button
  title={`Sort by ${value}`}
  on:click={() => {
    sortDir = !active ? 'asc' : sortDir == 'asc' ? 'des' : 'asc';
    sortParam = value;
  }}
>
  <span style="margin-right: .5em;">{title}</span>
  {#if active}
    {#if sortDir == 'asc'}
      <SortAscending />
    {:else}
      <SortDescending />
    {/if}
  {:else}
    <SortAscending style="color:grey;" />
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
