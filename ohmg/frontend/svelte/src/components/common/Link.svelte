<script>
  import ArrowSquareOut from 'phosphor-svelte/lib/ArrowSquareOut';
  import ArrowRight from 'phosphor-svelte/lib/ArrowRight';
  import DownloadSimple from 'phosphor-svelte/lib/DownloadSimple';

  export let href;
  export let external = false;
  export let rightArrow = false;
  export let download = null;
  export let title = '';
  export let classes = [];

  const classStr = classes.join(' ');
</script>

<a {href} class={classStr} target={external ? '_blank' : null} {title} {download}>
  <slot></slot>
  {#if external}
    <ArrowSquareOut />
  {:else if rightArrow}
    <ArrowRight />
  {:else if download}
    <DownloadSimple />
  {/if}
  <!-- </span> -->
</a>
