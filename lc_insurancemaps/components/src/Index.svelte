<script>
import { set_attributes } from "svelte/internal";
import Split from "../../../georeference/components/src/Split.svelte";

export let STATE_CHOICES;
export let CITY_QUERY_URL;

const cityDefault = "Select a city";

let currentState = "louisiana";

let cityOptions = [cityDefault];
let currentCity;
let volumes = [];

let loadingCities = false;
let loadingVolumes = false;

function updateCityList(state) {
	loadingCities = true;
	volumes = [];
	let cityUrl = `${CITY_QUERY_URL}?t=cities&s=${state}`;
	fetch(cityUrl, {
		method: 'GET',
	})
	.then(response => response.json())
	.then(result => {

		cityOptions = result;
		currentCity = cityDefault;
		loadingCities = false;
	});
}
$: updateCityList(currentState);

function updateVolumeList(city) {
	let volumeUrl = `${CITY_QUERY_URL}?t=volumes&s=${currentState}&c=${city}`;
	if (city != cityDefault && city != undefined)	{
		volumes = [];
		loadingVolumes = true;
		fetch(volumeUrl, {
			method: 'GET',
		})
		.then(response => response.json())
		.then(result => {
			volumes = result;
			loadingVolumes = false;
			console.log(volumes);
		});
	} else {
		volumes = [];
	}
}
$: updateVolumeList(currentCity);

</script>

<main>
	<div class="pane" style="test-align: left;">
		<h1>Welcome</h1>
		<p>This is an open platform for creating and viewing web map mosaics of historical fire insuance maps.</p>
		<p>All of the maps are pulled directly from the Library of Congress <a href="https://www.loc.gov/collections/sanborn-maps/about-this-collection/">Sanborn Maps Collection</a>.</p>
		<p>The base of this platform is <a href="https://geonode.org">GeoNode</a>, an open source geospatial content management system.</p>
		<p>Two distinct custom components have been added:</p>
		<ol>
			<li>An interface and database configuration tailored specifically to the structure of this map series.</li>
			<li>A suite of tools that allows users to split, trim, and georeference the maps.</li>
		</ol>
	</div>
	<div class="pane" style="text-align: center;">
		<div class="select-menus">
			<div class="select-item">
				<h3>Select a state</h3>
				<em>only Louisiana avaiable in beta</em>
				<select bind:value={currentState}>
				{#each STATE_CHOICES as state}
					<!-- <option value={state[0]} disabled={state[0] != "louisiana" or state[0] != "wisconsin"}>{state[1]}</option> -->
					<option value={state[0]}>{state[1]}</option>
				{/each}
				</select>
			</div>
			<div class="select-item">
				<h3>Which city are you interested in?</h3>
				<select bind:value={currentCity} disabled={loadingCities}>
					<option value={cityDefault} disabled>{cityDefault}</option>
				{#each cityOptions as city}
					<option value={city[0]}>{city[0]} - {city[1]} volume{#if city[1] != 1}s{/if}</option>
				{/each}
				</select>
			</div>
			<div class="select-item">
				{#if volumes.length > 0 }
				<h3>Volumes available for {currentCity}:</h3>
					<ul>
					{#each volumes as volume}
						<li>{volume.fields.year} {#if volume.fields.volume_no}(vol. {volume.fields.volume_no}){/if} | {volume.fields.city}, {volume.fields.county_equivalent} | {volume.fields.sheet_ct} sheet{#if volume.fields.sheet_ct != 1}s{/if}</li>
					{/each}
					</ul>
				{:else}
				<div class={loadingVolumes || loadingCities ? 'lds-ellipsis': ''} ><div></div><div></div><div></div><div></div></div>
				{/if}
			</div>
		</div>
	</div>
</main>

<style>
	main {
		display: flex;
		flex-direction: row;
		color: black;
		font-size: 1.25em;
		padding: 1em;
		max-width: 240px;
		margin: 0 auto;
		/* background: #2c689c;
		background: #ffd78b; */

	}

	main a {
		color: #ff8f31;
	}

	.pane {
		flex-grow: 1;
		width: 50%;
	}

	.pane + .pane {
		margin-left: 2%;
	}

	.select-menus {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.select-item {
		width: 100%;
		margin-bottom: 20px;
	}

	h1, h2, h3 {
		text-shadow: 2px 2px 2px rgba(0, 0, 0, 0.4);
		color: #ff3e00;
	}

	h1 {
		font-size: 4em;
		font-weight: 100;
	}

	@media (min-width: 640px) {
		main {
			max-width: none;
		}
	}

	select {
		color: rgb(59, 57, 57);
		width: 100%;
		height: 2em;
		font-size: 1.25em;
		font-weight: 700;
	}

	select:disabled {
		color: #acacac;
	}

	/* pure css loading bar */
	/* from https://loading.io/css/ */
	.lds-ellipsis {
		display: inline-block;
		position: relative;
		width: 80px;
		height: 80px;
	}
	.lds-ellipsis div {
		position: absolute;
		top: 33px;
		width: 13px;
		height: 13px;
		border-radius: 50%;
		background: #fff;
		animation-timing-function: cubic-bezier(0, 1, 1, 0);
	}
	.lds-ellipsis div:nth-child(1) {
		left: 8px;
		animation: lds-ellipsis1 0.6s infinite;
	}
	.lds-ellipsis div:nth-child(2) {
		left: 8px;
		animation: lds-ellipsis2 0.6s infinite;
	}
	.lds-ellipsis div:nth-child(3) {
		left: 32px;
		animation: lds-ellipsis2 0.6s infinite;
	}
	.lds-ellipsis div:nth-child(4) {
		left: 56px;
		animation: lds-ellipsis3 0.6s infinite;
	}
	@keyframes lds-ellipsis1 {
		0% {
			transform: scale(0);
		}
		100% {
			transform: scale(1);
		}
	}
	@keyframes lds-ellipsis3 {
		0% {
			transform: scale(1);
		}
		100% {
			transform: scale(0);
		}
		}
		@keyframes lds-ellipsis2 {
		0% {
			transform: translate(0, 0);
		}
		100% {
			transform: translate(24px, 0);
		}
	}
</style>