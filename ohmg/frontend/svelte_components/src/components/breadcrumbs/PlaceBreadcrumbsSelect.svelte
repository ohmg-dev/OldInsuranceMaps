<script>
  import ArrowRight from 'phosphor-svelte/lib/ArrowRight';

  export let PLACE;
  export let update;
</script>

<section>
  <div>
    <select
      bind:value={PLACE.select_lists[1].selected}
      on:change={() => {
        update(PLACE.select_lists[1].selected);
      }}
    >
      {#each PLACE.select_lists[1].options as i}
        <option value={i.slug}
          >{i.display_name}
          {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option
        >
      {/each}
    </select>
    <span class="arrow hideable">
      <ArrowRight size={12} />
    </span>
  </div>
  <div>
    <select
      bind:value={PLACE.select_lists[2].selected}
      on:change={() => {
        update(PLACE.select_lists[2].selected);
      }}
    >
      <option value="---">---</option>
      {#each PLACE.select_lists[2].options as i}
        <option value={i.slug}
          >{i.display_name}
          {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option
        >
      {/each}
    </select>
    <span class="arrow hideable">
      <ArrowRight size={12} />
    </span>
  </div>
  <div>
    <select
      bind:value={PLACE.select_lists[3].selected}
      disabled={PLACE.select_lists[2].selected === '---'}
      on:change={() => {
        update(PLACE.select_lists[3].selected);
      }}
    >
      <option value="---">---</option>
      {#each PLACE.select_lists[3].options as i}
        <option value={i.slug}
          >{i.display_name}
          {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option
        >
      {/each}
    </select>
    <span class="arrow hideable">
      <ArrowRight size={12} />
    </span>
  </div>
  <div>
    <select
      bind:value={PLACE.select_lists[4].selected}
      disabled={PLACE.select_lists[2].selected === '---'}
      on:change={() => {
        update(PLACE.select_lists[4].selected);
      }}
    >
      <option value="---">---</option>
      {#each PLACE.select_lists[4].options as i}
        <option value={i.slug}
          >{i.display_name}
          {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option
        >
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

  @media (max-width: 768px) {
    section {
      flex-direction: column;
    }
    select {
      margin-bottom: 2px;
      width: 100%;
    }
    section > div {
      width: 100%;
    }
    .hideable {
      display: none;
    }
  }
</style>
