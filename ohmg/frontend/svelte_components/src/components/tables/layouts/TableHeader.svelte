<script>
  import SortAscending from 'phosphor-svelte/lib/SortAscending';
  import SortDescending from 'phosphor-svelte/lib/SortDescending';
  import List from 'phosphor-svelte/lib/List';

  export let title = '';
  export let alt = '';
  export let value = '';
  export let offset = 0;
  export let sortParam = null;
  export let sortDir = 'asc';
  export let toggleVar = null;
  export let newCol = false;

  let popup = alt ? alt : `Sort by ${value}`;

  $: active = sortParam == value;
</script>

<th class={`${newCol ? "new-col" : ""}`}>
  <div>
    <span style="margin-top:.25em; text-wrap: nowrap;">{title}</span>
    {#if sortParam}
      <button
        title={popup}
        style="margin-left:.25em; display:flex;"
        on:click={() => {
          sortDir = !active ? 'asc' : sortDir == 'asc' ? 'des' : 'asc';
          sortParam = value;
          offset = 0;
        }}
      >
        {#if active}
          {#if sortDir == 'asc'}
            <SortAscending />
          {:else}
            <SortDescending />
          {/if}
        {:else}
          <List style="color:gray;" />
        {/if}
      </button>
    {/if}
    {#if toggleVar != null}
    <input style="margin-left:.25em;" type="checkbox" bind:checked={toggleVar} />
    {/if}
  </div>
</th>

<style>
  button:hover {
    background: #f7f1e1;
    color: #333;
    box-shadow: gray 0px 0px 5px;
  }
</style>
