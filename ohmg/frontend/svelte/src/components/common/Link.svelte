<script>
  import ArrowSquareOut from 'phosphor-svelte/lib/ArrowSquareOut';

  export let href;
  export let external = false;
  export let title = '';
  export let classes = [];
  export let download = null;
  export let filename = null;

  const classStr = classes.join(' ');
</script>

{#if external}
  <span>
    <a {href} class={classStr} target="_blank" {title} {download}>
      <slot></slot>
      <ArrowSquareOut />
    </a>
  </span>
{:else}
  <a {href} class={classStr} {title} {download} {filename}>
    <slot></slot>
  </a>
{/if}

<style>
  span {
    display: inline-flex;
  }
  span > a {
    margin-right: 2px;
  }
</style>
