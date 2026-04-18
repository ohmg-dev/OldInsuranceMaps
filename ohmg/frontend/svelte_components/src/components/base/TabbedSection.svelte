<script>

    export let tabs;
    export let activeTab;
</script>

<section>
  <div class="section-tabs">
    <ul>
        {#each tabs as tab}
        <li class={activeTab == tab.id ? 'active' : ''}>
            <button
            on:click={() => {
                activeTab = tab.id;
            }}>{tab.title}</button>
        </li>
        {/each}
    </ul>
  </div>
  <div style="padding-top:10px;">
    <slot></slot>
  </div>
</section>

<style>

  div.section-tabs > ul > li {
    display: inline-block;
    margin-right: 1em;
  }

  div.section-tabs > ul > li > button {
    font-size: 1.4em;
  }

  div.section-tabs > ul > li.active {
    color: var(--theme-highlight-color);
    border-bottom: 1px solid var(--theme-highlight-color);
  }

  div.section-tabs > ul > li:hover {
    color: var(--theme-highlight-color);
    border-bottom: 1px solid var(--theme-highlight-color);
  }
</style>