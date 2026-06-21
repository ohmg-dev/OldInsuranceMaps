<script>
  import { slide } from 'svelte/transition';
  import ArrowRight from 'phosphor-svelte/lib/ArrowRight';
  import DotsThree from 'phosphor-svelte/lib/DotsThree';

  import { onMobile } from '../../lib/utils';

  import Link from '../base/Link.svelte';

  export let LOCALE;
  export let MAP;

  let currentIdentifier = MAP.identifier;
  function goToItem() {
    window.location = '/map/' + currentIdentifier;
  }
  let currentDoc = '---';
  function goToDocument() {
    window.location = '/document/' + currentDoc;
  }

  let expandLocale = !onMobile();
</script>

<section>
  <div style="min-height:2em;">
    <button style="display:flex; align-content: center;"
      on:click={() => {expandLocale = !expandLocale}}>
      <i class="fancy fancy-xs i-pin" style="margin-top: -5px;"></i>
    </button>
    {#if expandLocale}
    <div transition:slide={{axis: "y", duration:200}} style="display:flex; flex-wrap:wrap;">
      {#each LOCALE.breadcrumbs as bc, n}
        <Link href="/{bc.slug}">{bc.name}</Link>
        {#if n != LOCALE.breadcrumbs.length - 1}
          <span class="arrow">
            <ArrowRight size={12} />
          </span>
        {/if}
      {/each}
    </div>
    {:else}
    <div in:slide={{delay:200, duration:0}}>
      <button on:click={() => {expandLocale = !expandLocale}}><DotsThree /></button>
    </div>
    {/if}
    <span class="arrow hideable">
      <ArrowRight size={12} />
    </span>
  </div>
  <div>
    <i class="fancy fancy-xs i-volume"></i>
    <select bind:value={currentIdentifier} on:change={goToItem}>
      {#each LOCALE.maps as m}
        <option value={m.identifier}>{m.title}</option>
      {/each}
    </select>
    <span class="arrow hideable">
      <ArrowRight size={12} />
    </span>
  </div>
  <div>
    <i class="fancy fancy-xs i-document"></i>
    <select bind:value={currentDoc} on:change={goToDocument}>
      <option value="---">document</option>
      {#each MAP.documents as d}
        <option value={d.id}>{d.nickname}</option>
      {/each}
    </select>
  </div>
</section>

<style>
  section {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    padding: 5px 0px;
    font-size: 0.95em;
    border-bottom: none;
  }

  section > div {
    display: flex;
    align-items: center;
  }

  select {
    margin-right: 3px;
    color: #2c689c;
    cursor: pointer;
    padding: 5px 0px 4px 5px;
  }

  span.arrow {
    margin: 0px 2px;
  }

  i {
    background-color: #2c689c;
    margin-right: 2px;
  }

  @media (max-width: 768px) {
    select {
      margin-bottom: 2px;
    }
    .hideable {
      display: none;
    }
  }
</style>
