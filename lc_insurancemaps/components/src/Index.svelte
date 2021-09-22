<script>
export let STATE_CHOICES;
export let CITY_QUERY_URL;

const cityDefault = "Select a City";

let currentState = "louisiana";

let cityOptions = [cityDefault];
let currentCity;
let volumes = [];



function updateCityList(state) {
	let cityUrl = `${CITY_QUERY_URL}?t=cities&s=${state}`;
	console.log("getting cities");
	fetch(cityUrl, {
		method: 'GET',
	})
	.then(response => response.json())
	.then(result => {

		cityOptions = result;
		currentCity = cityDefault;
	});
}
$: updateCityList(currentState);

function updateVolumeList(city) {
	let volumeUrl = `${CITY_QUERY_URL}?t=volumes&s=${currentState}&c=${city}`;
	if (city != cityDefault && city != undefined)	{
		fetch(volumeUrl, {
			method: 'GET',
		})
		.then(response => response.json())
		.then(result => {
			volumes = result;
			console.log(volumes)
		});
	} else {
		volumes = [];
	}
}
$: updateVolumeList(currentCity);

</script>

<main>
	<h1>Hello!</h1>
	<p>Visit the <a href="https://svelte.dev/tutorial">Svelte tutorial</a> to learn how to build Svelte apps.</p>
	<select bind:value={currentState}>
	{#each STATE_CHOICES as state}
		<!-- <option value={state[0]} disabled={state[0] != "louisiana" or state[0] != "wisconsin"}>{state[1]}</option> -->
		<option value={state[0]}>{state[1]}</option>
	{/each}
	</select>

	<select class="gcp-select" bind:value={currentCity}>
		<option value={cityDefault} disabled>{cityDefault}</option>
	{#each cityOptions as city}
		<option value={city[0]}>{city[0]} - {city[1]} volume{#if city[1] != 1}s{/if}</option>
	{/each}
	</select>

	<ul>
	{#each volumes as volume}
		<li>{volume.fields.city}, {volume.fields.county_equivalent} | {volume.fields.year} - {volume.fields.sheet_ct} sheet{#if volume.fields.sheet_ct != 1}s{/if}</li>
	{/each}
	</ul>
</main>

<style>
	main {
		text-align: center;
		padding: 1em;
		max-width: 240px;
		margin: 0 auto;
	}

	h1 {
		color: #ff3e00;
		text-transform: uppercase;
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
		margin: 10px; 
	}
</style>