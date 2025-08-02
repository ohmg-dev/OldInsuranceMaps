<script>
  import CaretDoubleLeft from 'phosphor-svelte/lib/CaretDoubleLeft';
  import CaretDoubleRight from 'phosphor-svelte/lib/CaretDoubleRight';

  export let loading = false;
  export let currentOffset = 0;
  export let currentLimit = 100;
  export let total = 0;

  const locale = document.documentElement.lang || 'en';
  $: formattedTotal = total.toLocaleString(locale);

  // this weirdness is necessary because the Select element seems to convert basic value into objects after it's
  // been initialized :/
  $: useLimit = typeof currentLimit == 'string' ? currentLimit : currentLimit.value;
  $: limitInt = parseInt(useLimit);
</script>

<div class="btn-container">
  <button
    class="is-icon-link"
    title="Go to previous page"
    disabled={currentOffset < limitInt || loading}
    on:click={() => {
      currentOffset = currentOffset - limitInt;
    }}
  >
    <CaretDoubleLeft />
  </button>
  <div>{currentOffset} - {currentOffset + limitInt < total ? currentOffset + limitInt : total} ({formattedTotal})</div>
  <button
    class="is-icon-link"
    title="Go to next page"
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
