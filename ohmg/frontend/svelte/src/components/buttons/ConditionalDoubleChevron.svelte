<script>
  import CaretDoubleDown from 'phosphor-svelte/lib/CaretDoubleDown';
  import CaretDoubleRight from 'phosphor-svelte/lib/CaretDoubleRight';

  export let down;
</script>

{#if down}
  <CaretDoubleDown />
{:else}
  <CaretDoubleRight />
{/if}
