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

let faq1Hidden = true;
let faq2Hidden = true;
let faq3Hidden = true;
let faq4Hidden = true;
</script>

<main>
	<div class="toggler">
		<div>
			<button on:click={() => faq1Hidden = !faq1Hidden}>
				What are volumes?
				<i class="fa {faq1Hidden ? 'fa-chevron-right' : 'fa-chevron-down'}"></i>
			</button>
			<div class="faq-content" hidden={faq1Hidden}>
				<p>In the Library of Congress 
				<a href="https://www.loc.gov/collections/sanborn-maps/about-this-collection/">digital Sanborn Maps collection</a>,
				each item is typically a full edition&mdash;the complete survey of a city in a given year. However, in
				large cities like New Orleans, multiple volumes were created for an edition, each one stored 
				as separate items. Thus, we have chosen <strong>volume</strong> as used as the highest level 
				of grouping for content in this project. Each volume has one or more <strong>sheets</strong>.
				</p>
			</div>
		</div>
		<div>
			<button on:click={() => faq2Hidden = !faq2Hidden}>
				What does started/not started mean?
				<i class="fa {faq2Hidden ? 'fa-chevron-right' : 'fa-chevron-down'}"></i>
			</button>
			<div class="faq-content" hidden={faq2Hidden}>
				<p>
					If you are signed in you can "start" a volume by loading its sheets. Once or more sheets are loaded,
					you can begin transforming them from scanned images to geopatial layers through the
					georeferencing process.
				</p>
			</div>
		</div>
		<div>
			<button on:click={() => faq3Hidden = !faq3Hidden}>
				Why isn't my city listed?
				<i class="fa {faq3Hidden ? 'fa-chevron-right' : 'fa-chevron-down'}"></i>
			</button>
			<div class="faq-content" hidden={faq3Hidden}>
				<p>
					Unfortunately, if a city does not appear in the list, that means there is no item 
					in the collection for it. However, do check for old names of your city, or the 
					names of adjacent communinities that may have combined with yours over the years.
				</p>
			</div>
		</div>
		<div>
			<button on:click={() => faq4Hidden = !faq4Hidden}>
				Why are some volumes <span style="color: grey">greyed out?</span>
				<i class="fa {faq4Hidden ? 'fa-chevron-right' : 'fa-chevron-down'}"></i>
			</button>
			<div class="faq-content" hidden={faq4Hidden}>
				<p>
					This means the volume exists in the Library of Congress collection, but is not
					available in this project. This is because while we want to provide wide geographic and temporal coverage
					throughout Louisiana, we also need to make disk space manageable.
					We devised the following criteria to determine avialability:
				</p>
				<ul>
					<li>Include the earliest edition for every community, regardless of date.</li>
					<li>For New Orleans, <em>only</em> include the earliest edition (1885, in two volumes).</li>
					<li>For all other communities, exclude editions published after 1910.</li>
				</ul>
				<p>
					These criteria produce 266 volumes covering 138 communities, containing 1499 sheets.
					If you are very interested in georeferencing a volume that is greyed out, please get in touch!  
				</p>
				<p>
					<em>
						If you are very interested in georeferencing a volume that is greyed out, please get in touch!  
					</em>
				</p>
			</div>
		</div>
	</div>
	<h3>Find a Volume</h3>
	<div style="display:flex; flex-direction:row;">
		<div class="pane" style="height:299px">
			<input type="text" id="filterInput" placeholder="Filter by name.." bind:value={filterInput}>
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
	<h3>Started Volumes</h3>
	<div>
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
	</div>
</main>

<style>

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