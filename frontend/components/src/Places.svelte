<script>
import {TableSort} from 'svelte-tablesort'

export let PLACES_API_URL;
export let OHMG_API_KEY;

let all_places = [];
let filtered_places = []
let loading = true

const apiHeaders = {
	'X-API-Key': OHMG_API_KEY,
}

fetch(PLACES_API_URL, { headers: apiHeaders })
	.then(response => response.json())
    .then(result => {
		all_places = result;
		filtered_places = result;
		loading = false;
	});

function updateFilteredList(filterText) {
	if (filterText && filterText.length > 0) {
		filtered_places = [];
		all_places.forEach( function(place) {
			const placeName = place.name.toUpperCase();
			const filterBy = filterText.toUpperCase();
			if (placeName.indexOf(filterBy) > -1) {
				filtered_places.push(place);
			}
		});
	} else {
		filtered_places = all_places;
	}
}
let filterInput;
$: updateFilteredList(filterInput)

</script>

<div class="filter-container">
	<input type="text" id="filterInput" placeholder="Filter by place name..." bind:value={filterInput}>
</div>
<div style="overflow-x:auto;">
	{#if loading}
	<div style="text-align:center;">
		<div class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
	</div>
	{:else if filtered_places.length === 0}
	<p><em>No places found...</em></p>
	{:else}
	<TableSort items={filtered_places}>
		<tr slot="thead">
			<th data-sort="name" style="max-width:300px;" title="Name of mapped location">Place</th>
			<th data-sort="sort_years" style="max-width:300px;" title="Volumes available">Volumes available</th>
		</tr>
		<tr slot="tbody" let:item={p} style="height:38px;">
			<td><a title="View all {p.name} mosaics in viewer" href="{p.url}">{p.name}</a></td>
			<td>{#each p.items as v, i}<a href="{v.url}">{v.year}</a>{#if i < p.items.length-1}, {/if}{/each}</td>
		</tr>
	</TableSort>
	{/if}
</div>

<style>

.filter-container {
	padding: 0px 10px 10px 10px;
}

.filter-container > input {
	width: 100%;
}

</style>
