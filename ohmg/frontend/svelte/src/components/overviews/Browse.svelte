<script>
  import '../../css/shared.css';
  import Maps from '../lists/Maps.svelte';
  import Places from '../lists/Places.svelte';
  import MapBrowse from '../interfaces/MapBrowse.svelte';

  export let CONTEXT;
  export let PLACES_CT;
  export let MAP_CT;

  let reinitMap = [{}];

  // Use the hash to set the browse view, force to "map" if incoming hash is empty or invalid
  let currentTab = window.location.hash.substr(1) != '' ? window.location.hash.substr(1) : 'map';
  if (['map', 'place', 'items'].indexOf(currentTab) === -1) {
    currentTab = 'map';
  }
  $: {
    history.replaceState(null, document.title, `#${currentTab}`);
  }
</script>

<main>
  <div class="tab-row">
    <button
      class={currentTab == 'map' ? 'active' : ''}
      title="Browse by map"
      on:click={() => {
        currentTab = 'map';
        reinitMap = [{}];
      }}
    >
      Map Finder
    </button>
    <button
      class={currentTab == 'places' ? 'active' : ''}
      title="Browse by locale"
      on:click={() => {
        currentTab = 'places';
      }}
    >
      Browse Places ({PLACES_CT})
    </button>
    <button
      class={currentTab == 'items' ? 'active' : ''}
      title="Browse by content name"
      on:click={() => {
        currentTab = 'items';
      }}
    >
      Browse Items ({MAP_CT})
    </button>
  </div>
  <div>
    <div style="display: {currentTab === 'map' ? 'block' : 'none'}">
      {#each reinitMap as key (key)}
        <MapBrowse {CONTEXT} />
      {/each}
    </div>
    <div style="display: {currentTab === 'places' ? 'block' : 'none'}">
      <Places {CONTEXT} />
    </div>
    <div style="display: {currentTab === 'items' ? 'block' : 'none'}">
      <Maps {CONTEXT} />
    </div>
  </div>
</main>

<style>
  main {
    display: flex;
    flex-direction: column;
  }

  .tab-row {
    display: flex;
    flex-direction: row;
    justify-content: space-evenly;
  }
  .tab-row button {
    color: white;
    width: 30%;
    cursor: pointer;
    background-color: #123b4f;
    margin: 10px;
    border-radius: 10px;
    font-size: 1em;
    text-align: center;
  }
  .tab-row button {
    font-size: 1.5em;
    margin: 10px 0px;
  }
  .tab-row button.active {
    background-color: #2c689c;
  }
  .tab-row button:hover {
    background-color: #2c689c;
  }

  @media (max-width: 640px) {
    .tab-row {
      flex-direction: column;
    }
    .tab-row button {
      width: 100%;
    }
  }
</style>
