<script>
  import Select from 'svelte-select';

  export let value = null;
  export let items = [];
  export let placeholder = 'Choose a filter...';
  export let containerStyles = 'width:300px;';
  export let offset = 0;
</script>

<Select
  {items}
  bind:value
  {placeholder}
  listAutoWidth={false}
  class="filter-input"
  {containerStyles}
  on:change={() => {
    offset = 0;
  }}
/>
