<script>
import Volumes from './Volumes.svelte';
import Places from './Places.svelte';
import MapBrowse from './MapBrowse.svelte';

export let PLACES_GEOJSON_URL;
export let PLACES_CT;
export let PLACES_API_URL;
export let ITEM_CT;
export let ITEM_API_URL;
export let OHMG_API_KEY;

let reinitMap = [{}]

// Use the hash to set the browse view, force to "map" if incoming hash is empty or invalid
let currentTab = window.location.hash.substr(1) != "" ? window.location.hash.substr(1) : "map";
if (["map", "place", "items"].indexOf(currentTab) === -1) {currentTab = 'map'};
$: { history.replaceState(null, document.title, `#${currentTab}`); }

</script>

<main>
	<div class="tab-row">
		<div class="{currentTab == 'map' ? 'active' : ''}" on:click={() => {currentTab = "map"; reinitMap = [{}];}}>
			<h2>Map Finder</h2>
		</div>
		<div class="{currentTab == 'places' ? 'active' : ''}" on:click={() => {currentTab = "places"}}>
			<h2>Browse Places ({PLACES_CT})</h2>
		</div>
		<div class="{currentTab == 'items' ? 'active' : ''}" on:click={() => {currentTab = "items"}}>
			<!-- <h2>Browse by volume ({STARTED_VOLUMES.length})</h2> -->
			<h2>Browse Items ({ITEM_CT})</h2>
		</div>
	</div>
	<div>
		<div style="display: {currentTab === 'map' ? 'block' : 'none'}">
			{#each reinitMap as key (key)}
			<MapBrowse PLACES_GEOJSON_URL={PLACES_GEOJSON_URL} OHMG_API_KEY={OHMG_API_KEY}/>
			{/each}
		</div>
		<div style="display: {currentTab === 'places' ? 'block' : 'none'}">
			<Places PLACES_API_URL={PLACES_API_URL} OHMG_API_KEY={OHMG_API_KEY}/>
		</div>
		<div style="display: {currentTab === 'items' ? 'block' : 'none'}">
			<Volumes ITEM_API_URL={ITEM_API_URL} OHMG_API_KEY={OHMG_API_KEY}/>
		</div>
	</div>
</main>

<style>

main {
	display: flex;
	flex-direction: column;
}

.tab-row {
	display:flex;
	flex-direction: row;
}
.tab-row div {
	color: white;
	width: 50%;
	cursor: pointer;
	background-color: #123B4F;
	margin: 10px;
	border-radius: 10px;
	font-size: 1em;
	text-align: center;
}
.tab-row div h2 {
	font-size: 1.5em;
	margin: 10px 0px;
}
.tab-row div.active {
	background-color: #2c689c;
}
.tab-row div:hover {
	background-color: #2c689c;
}

@media (max-width: 640px) {
	/* main {
		max-width: none;
	} */
	.tab-row {
		flex-direction: column;
	}
	.tab-row div {
		width: 100%;
	}
}


</style>
