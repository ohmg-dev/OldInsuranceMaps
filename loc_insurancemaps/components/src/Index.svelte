<script>
export let STATE_CHOICES;
export let CITY_QUERY_URL;
export let USER_TYPE;
export let CITY_LIST;

const cityDefault = "Select a community";

let currentState = "louisiana";

let cityOptions = CITY_LIST;
let currentCity;
let currentCountyEq;
let volumes = [];

let loadingCities = false;
let loadingVolumes = false;

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
			if ( result.length > 0) {
				currentCountyEq = result[0]["county_eq"]
			}
			volumes = result;
			loadingVolumes = false;
		});
	} else {
		volumes = [];
	}
}
$: updateVolumeList(currentCity);

function updateFilteredList(filterText) {
	if (filterText && filterText.length > 0) {
		cityOptions = [];
		CITY_LIST.forEach( function(city) {
			const cityName = city[0].toUpperCase();
			const filterBy = filterText.toUpperCase();
			if (cityName.indexOf(filterBy) > -1) {
				cityOptions.push(city);
			}
		});
	} else {
		cityOptions = CITY_LIST;
	}
}
let filterInput;
$: updateFilteredList(filterInput)

</script>

<main>
	<div style="display:flex; flex-direction:row;">
		<div class="pane">
			<h1>Welcome</h1>
			<p>
				This is an open platform for georeferencing and viewing old insurance maps in
				the Library of Congress <a href="https://www.loc.gov/collections/sanborn-maps/about-this-collection/">Sanborn Maps Collection</a>.
			</p>	
		</div>
		<div class="pane">
			<h2>How to Use This Site</h2>
			<ul>
				<li>If a volume has been started, you'll be able to view it status page.</li>
				<li>If you have an account, you can start a new volume.</li>
				<li>If a volume is greyed out <span style="color: grey">(like this)</span> then it
					is not available for this project. <a href="/about#included-volumes" target="_blank">learn why <i class="fa fa-external-link"></i></a></li>
			</ul>		
		</div>
	</div>
	<hr>
	<div style="display:flex; flex-direction:row;">
		<div class="pane">
			<input type="text" id="filterInput" placeholder="Filter by name.." bind:value={filterInput}>
			<div id="city-list" style="max-height: 350px; overflow-y:auto;">
				{#each cityOptions as city}
				<label for={city[0]}>
					<input type="radio" id={city[0]} bind:group={currentCity} value={city[0]}>
					{city[0]} - {city[1]} volume{#if city[1] != 1}s{/if}
				</label>
				{/each}
			</div>
		</div>
		<div class="pane">
			{#if volumes.length > 0 }
			<h3 style="margin-top: 10px;">{currentCity}, {currentCountyEq}:</h3>
				<ul class="volume-list">
				{#each volumes as volume}
					<li>
					{#if volume.include == false}
						<span style="color:grey;">{volume.title}</span>
					{:else}
						<a href="{volume.url}">{volume.title}</a> ({volume.status})
					{/if}
					</li>
				{/each}
				</ul>
			{:else}
			<h3 style="margin-top: 10px;">&larr; Select a Community</h3>
			<div class={loadingVolumes || loadingCities ? 'lds-ellipsis': ''} ><div></div><div></div><div></div><div></div></div>
			{/if}
		</div>
	</div>
</main>

<style>

#filterInput {
  width: 100%; /* Full-width */
  font-size: 16px; /* Increase font-size */
  padding: 12px;
  text-align: center;
  border: 1px solid #ddd; /* Add a grey border */
}

#city-list label {
  border: 1px solid #ddd; /* Add a border to all links */
  margin-top: -1px; /* Prevent double borders */
  background-color: #f6f6f6; /* Grey background color */
  padding: 12px; /* Add some padding */
  text-decoration: none; /* Remove default text underline */
  font-size: 18px; /* Increase the font-size */
  color: black; /* Add a black text color */
  display: block; /* Make it into a block element to fill the whole list */
  margin-bottom: 0px;
}

#city-list label:hover:not(.header) {
  background-color: #eee; /* Add a hover effect to all links, except for headers */
}

	main {
		display: flex;
		flex-direction: column;
		color: black;
		font-size: 1.25em;
		padding: 1em;
		/* max-width: 240px; */
		margin: 0 auto;
		/* background: #2c689c;
		background: #ffd78b; */

	}

	main a {
		color: #1647a4;
		color: #ff8f31;
		color: #ff3e00;
		color: #007363;
		color: #812525;
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
		/* font-size: 4em;*/
		font-weight: 400; 
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
		/* font-weight: 700; */
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
		background: #000;
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