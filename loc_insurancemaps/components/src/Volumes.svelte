<script>
export let STARTED_VOLUMES;
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
				currentCountyEq = result[0]["county_equivalent"]
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
	<h1>Volumes</h1>
	<div>
		{#if STARTED_VOLUMES.length == 0}
		<p>No volumes have been started yet.</p>
		{:else}
		<ul class="started-volume-list">
		{#each STARTED_VOLUMES as v}
		<li>
			<a href={v.urls.summary} alt={v.title} title="View summary of {v.title}">
				{v.title}
			</a>
			| {v.sheet_ct} sheet{#if v.sheet_ct!=1}s{/if}
			| started by <a href={v.loaded_by.profile}>{v.loaded_by.name}</a>
		</li>
		{/each}
		</ul>
		{/if}
	</div>
	<hr>
	<h3>Find a new volume to start...</h3>
	<div style="display:flex; flex-direction:row;">
		<div class="pane" style="height:299px">
			<input type="text" id="filterInput" placeholder="Filter by name..." bind:value={filterInput}>
			<div id="city-list" style="height:250px; overflow-y:auto;">
				{#each cityOptions as city}
				<label for={city[0]}>
					<input type="radio" id={city[0]} bind:group={currentCity} value={city[0]}>
					{city[0]} - {city[1]} volume{#if city[1] != 1}s{/if}
				</label>
				{/each}
			</div>
		</div>
		<div class="pane" style="height:299px; overflow-y:auto;">
			{#if volumes.length > 0 }
			<h3 style="margin-top: 10px;">{currentCity}, {currentCountyEq}:</h3>
				<ul class="volume-list">
				{#each volumes as volume}
					<li>
					{#if volume.include == false}
						<span style="color:grey;">{volume.title}</span>
					{:else}
						<a href="{volume.urls.summary}">{volume.title}</a> ({volume.status})
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

hr {
	border-top-color:rgb(149, 149, 149);
}

.started-volume-list {
	/* list-style: none; */
	/* padding-left: 0px; */
}

.started-volume-list li {
	/* display: inline-block; */
}

.faq-content {
	padding: 10px;
	border: 1px solid grey;
	background: lightgrey;
	border-radius: 4px;
}

.faq-content p {
	margin: 0;
}

.toggler div button {
    background: unset;
    border: unset;
    box-shadow: unset;
	color: #812525;
}

.toggler div button i {
	font-size: .75em;
}

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

	/* main {
		display: flex;
		flex-direction: column;
		color: black;
		font-size: 1.25em;
		padding: 1em;
		margin: 0 auto;
	} */
	main { 
	margin-bottom: 10px;
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

	h1 {
		font-size: 2.5em;
		font-weight: 100;
		text-shadow: 2px 2px 2px rgba(0, 0, 0, 0.4);
	}

	h2, h3 {
		text-shadow: 1px 1px 1px rgba(0, 0, 0, 0.4);
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