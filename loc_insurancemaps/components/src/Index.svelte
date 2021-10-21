<script>
export let STATE_CHOICES;
export let CITY_QUERY_URL;
export let USER_TYPE;

const cityDefault = "Select a community";

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
		console.log("getting volumes")
		volumes = [];
		loadingVolumes = true;
		fetch(volumeUrl, {
			method: 'GET',
		})
		.then(response => response.json())
		.then(result => {
			volumes = result;
			loadingVolumes = false;
		});
	} else {
		volumes = [];
	}
}
$: updateVolumeList(currentCity);

</script>

<main>
	<div class="pane">
		<h1>Welcome</h1>
		<p>This is an open platform for georeferencing and viewing Louisiana maps from
			the Library of Congress <a href="https://www.loc.gov/collections/sanborn-maps/about-this-collection/">Sanborn Maps Collection</a>.</p>
		<p>Currently, only maps made through 1910 are available, with two exceptions:</p>
		<ul>
			<li>If only one volume was published for a community, it will be included regardless of the year</li>
			<li>Because if the city's disproportionate size, only the earliest year for New Orleans is included (1885)</li>
		</ul>
		<h3>To get started...</h3>
		<p>Select a community at right &rarr;</p>
	</div>
	<div class="pane">
		<div class="select-menus">
			<div class="select-item">
				<h3>Select a state</h3>
				<select bind:value={currentState}>
				{#each STATE_CHOICES as state}
					<option value={state[0]} disabled={state[0] != "louisiana"}>{state[1]}</option>
					<!-- <option value={state[0]}>{state[1]}</option> -->
				{/each}
				</select>
			</div>
			<div class="select-item">
				<h3>Which community are you interested in?</h3>
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
					<ul class="volume-list">
					{#each volumes as volume}
						
						<li>
							{#if parseInt(volume.year) > 1910}
								<span style="color:grey;">{volume.title}</span>
							{:else}
								{volume.title}
								{#if volume.started}
									<a href="{volume.docs_search_url}">view documents</a>
								{:else if USER_TYPE == "superuser"}
									<a href="{volume.url}">import</a>
								{:else if USER_TYPE == "participant"}
									<a href="{volume.docs_search_url}">view</a>
								{:else}
									<a href="{volume.docs_search_url}">view documents</a>
								{/if}
							{/if}
						</li>
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
		color: #1647a4;
		color: #ff8f31;
		color: #ff3e00;
		color: #007363;
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

	/* h1, h2, h3 {
		color: #ff3e00;
		color: #136f6f;
		color: #373737;
		color: #028BAF;
	} */

	h1 {
		/* font-size: 4em;
		font-weight: 100; */
		text-shadow: 2px 2px 2px rgba(0, 0, 0, 0.4);
	}

	h2, h3 {
		/* text-shadow: 1px 1px 1px rgba(0, 0, 0, 0.4); */
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

	.volume-list {
		list-style: none;
		text-align: left;
		padding: 0;
	}

	.volume-list li {
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