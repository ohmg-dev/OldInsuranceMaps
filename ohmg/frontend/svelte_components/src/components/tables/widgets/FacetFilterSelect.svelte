<script>
  import Select from 'svelte-select';

  export let value = null;
  export let items = [];
  export let placeholder = 'Choose a filter...';
  export let offset = 0;
</script>

<Select
  {items}
  bind:value
  {placeholder}
  listAutoWidth={false}
  class={'facet-filter-input'}
  on:change={() => {
    offset = 0;
  }}
/>

<style>
  :global(.facet-filter-input) {
    width: 200px !important;
  }
  @media screen and (max-width: 768px) {
      :global(.facet-filter-input) {
          width: calc(50% - .25em);
      }
  }
</style>