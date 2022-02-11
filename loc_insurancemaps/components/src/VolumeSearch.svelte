<script>
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
	<h3>Search for volumes</h3>
	<p>Access available volumes here to start working on a new one. <a href="https://docs.oldinsurancemaps.net/" target="_blank">Learn more about this <i class="fa fa-external-link"></i></a></p>
	{#if USER_TYPE == 'anonymodus' }
	<div class="signin-reminder">
	<p><em>
		<!-- svelte-ignore a11y-invalid-attribute -->
		<a href="#" data-toggle="modal" data-target="#SigninModal" role="button" >sign in</a> or
		<a href="/account/signup">sign up</a> to start new volumes
	</em></p>
	</div>
	{/if}
	<div class="find-volumes-section">
		<div class="pane" style="height:299px">
			<input type="text" id="filterInput" placeholder="Filter by name..." bind:value={filterInput}>
			<div id="city-list" style="height:250px; overflow-y:auto;">
				{#each cityOptions as city}
				<label for={city[0]}>
					<input type="radio" id={city[0]} bind:group={currentCity} value={city[0]}>
					{city[0]} ({city[1]})
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
  padding: 5px; /* Add some padding */
  text-decoration: none; /* Remove default text underline */
  color: black; /* Add a black text color */
  display: block; /* Make it into a block element to fill the whole list */
  margin-bottom: 0px;
}

#city-list label:hover:not(.header) {
  background-color: #eee; /* Add a hover effect to all links, except for headers */
}

main { 
	margin-bottom: 10px;
}

.pane {
	flex-grow: 1;
	width: 50%;
}

.pane + .pane {
	margin-left: 2%;
}

@media (min-width: 640px) {
	main {
		max-width: none;
	}
}

.volume-list {
	list-style: none;
	text-align: left;
	padding: 0;
}

.find-volumes-section {
  display: flex;
  flex-direction: row;
}

/* Responsive layout - makes a one column layout instead of a two-column layout */
@media (max-width: 800px) {
  .find-volumes-section {
    flex-direction: column;
  }
  .pane {
	  width: 100%
  }
}

</style>