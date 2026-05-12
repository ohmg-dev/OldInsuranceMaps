<script>
  import ArrowSquareOut from 'phosphor-svelte/lib/ArrowSquareOut';
  import ArrowRight from 'phosphor-svelte/lib/ArrowRight';
  import DownloadSimple from 'phosphor-svelte/lib/DownloadSimple';

  export let href;
  export let external = false;
  export let rightArrow = false;
  export let download = false;
  export let title = '';
  export let classes = [];

  const classStr = classes.join(' ');
</script>

{#if external || rightArrow || download}
  {#if download }
  <a {href} class={classStr} target={external ? '_blank' : null} {title} download>
    <slot></slot>
    <DownloadSimple />
  </a>
  {:else}
  <a {href} class={classStr} target={external ? '_blank' : null} {title}>
    <slot></slot>
    {#if external}
      <ArrowSquareOut />
    {:else if rightArrow}
      <ArrowRight />
    {/if}
  </a>
  {/if}
{:else}
  <a {href} class={classStr} {title}>
    <slot></slot>
  </a>
{/if}
