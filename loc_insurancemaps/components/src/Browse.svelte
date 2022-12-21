<script>
import Volumes from './Volumes.svelte';
import Places from './Places.svelte';
import MapBrowse from './MapBrowse.svelte';

export let PLACES_GEOJSON;
export let STARTED_VOLUMES;
export let PLACES;

let currentTab = "map";

</script>

<main>
	<div class="tab-row">
		<div class="{currentTab == 'map' ? 'active' : ''}" on:click={() => {currentTab = "map"}}>
			<h2>Browse by map</h2>
		</div>
		<div class="{currentTab == 'places' ? 'active' : ''}" on:click={() => {currentTab = "places"}}>
			<h2>Browse by place ({PLACES.length})</h2>
		</div>
		<div class="{currentTab == 'volumes' ? 'active' : ''}" on:click={() => {currentTab = "volumes"}}>
			<h2>Browse by volume ({STARTED_VOLUMES.length})</h2>
		</div>
	</div>
	<div>
	{#if currentTab == "map"}
	<MapBrowse PLACES_GEOJSON={PLACES_GEOJSON}/>
	{:else if currentTab == "volumes"}
	<Volumes STARTED_VOLUMES={STARTED_VOLUMES}/>
	{:else if currentTab == "places"}
	<Places PLACES={PLACES}/>
	{/if}
	</div>
</main>

<style>

main {
	display: flex;
	flex-direction: column;
}

.tab-row {
	display:flex;

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

@media (min-width: 640px) {
	main {
		max-width: none;
	}
}

</style>
