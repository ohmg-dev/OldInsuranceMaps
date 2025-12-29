<script>
  import Select from 'svelte-select';

  export let value = 10;
  export let limitOptions = [10, 25, 50, 100];
</script>

<Select
  items={limitOptions}
  bind:value
  class="filter-input"
  searchable={false}
  clearable={false}
  listAutoWidth={false}
/>
