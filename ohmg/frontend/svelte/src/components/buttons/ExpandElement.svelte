<script>
  import ToolUIButton from './ToolUIButton.svelte';

  import ArrowsInSimple from 'phosphor-svelte/lib/ArrowsInSimple';
  import ArrowsOutSimple from 'phosphor-svelte/lib/ArrowsOutSimple';

  export let elementId;

  let ffs = false;
  function handleFfs(elementId) {
    ffs = !ffs;
    document.getElementById(elementId).classList.toggle('ffs');
    document.getElementById('main-container').classList.toggle('ffs-container');
  }

  function handleKeydown(e) {
    if (document.activeElement.id == '') {
      switch (e.key) {
        case 'Escape':
          handleFfs(elementId);
          break;
      }
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />
<ToolUIButton
  title={ffs ? 'Reduce' : 'Expand'}
  action={() => {
    handleFfs(elementId);
  }}
>
  {#if ffs}
    <ArrowsInSimple />
  {:else}
    <ArrowsOutSimple />
  {/if}
</ToolUIButton>
