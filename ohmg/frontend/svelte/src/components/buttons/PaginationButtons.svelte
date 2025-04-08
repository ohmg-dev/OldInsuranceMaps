<script>
  import Select from 'svelte-select';
  import CaretDoubleLeft from 'phosphor-svelte/lib/CaretDoubleLeft';
  import CaretDoubleRight from 'phosphor-svelte/lib/CaretDoubleRight';

  export let loading = false;
  export let currentOffset = 0;
  export let currentLimit = 100;
  export let total = 0;

  const locale = document.documentElement.lang || 'en';
  $: formattedTotal = total.toLocaleString(locale);

  let limitOptions = [10, 25, 50, 100];
  // this weirdness is necessary because the Select element seems to convert basic value into objects after it's
  // been initialized :/
  $: useLimit = typeof currentLimit == 'string' ? currentLimit : currentLimit.value;
  $: limitInt = parseInt(useLimit);
</script>

<div class="btn-container">
  <button
    class="is-icon-link"
    disabled={currentOffset < limitInt || loading}
    on:click={() => {
      currentOffset = currentOffset - limitInt;
    }}
  >
    <CaretDoubleLeft />
  </button>
  <div>{currentOffset} - {currentOffset + limitInt < total ? currentOffset + limitInt : total} ({formattedTotal})</div>
  {#if currentLimit != 0}
    <div style="display:flex; flex-direction:row; align-items:center; margin-left:10px;">
      <span>show</span>
      <Select
        items={limitOptions}
        bind:value={currentLimit}
        searchable={false}
        clearable={false}
        containerStyles="background:none; border:none; margin-left:6px; padding:0; width:45px; cursor:pointer;"
        listAutoWidth={false}
      />
    </div>
  {/if}
  <button
    class="is-icon-link"
    disabled={currentOffset + limitInt >= total || loading}
    on:click={() => {
      currentOffset = currentOffset + limitInt;
    }}
  >
    <CaretDoubleRight />
  </button>
</div>

<style>
  button {
    display: flex;
    align-items: center;
  }
  .btn-container {
    display: flex;
    align-items: center;
  }
</style>
