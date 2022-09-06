<script>
import {TableSort} from 'svelte-tablesort'

export let PLACES;

let places = PLACES;

function updateFilteredList(filterText) {
	if (filterText && filterText.length > 0) {
		volumes = [];
		PLACES.forEach( function(place) {
			const volumeName = place.title.toUpperCase();
			const filterBy = filterText.toUpperCase();
			if (volumeName.indexOf(filterBy) > -1) {
				volumes.push(place);
			}
		});
	} else {
		places = PLACES;
	}
}
let filterInput;
$: updateFilteredList(filterInput)

</script>

<input type="text" id="filterInput" placeholder="Filter by place name..." bind:value={filterInput}>
<div style="overflow-x:auto;">
	<TableSort items={places}>
		<tr slot="thead">
			<th data-sort="name" style="max-width:300px;" title="Name of mapped location">Place</th>
			<th data-sort="sort_years" style="max-width:300px;" title="Mosaics available">Mosaics available</th>
		</tr>
		<tr slot="tbody" let:item={p} style="height:38px;">
			<td><a title="View all {p.name} mosaics" href="{p.url}">{p.name}</a></td>
			<td>{#each p.volumes as v}<a href="{v.viewer_url}">{v.display_val}</a> {/each}</td>
		</tr>
	</TableSort>
</div>

<style>

/* Credit to this SO answer: https://stackoverflow.com/a/52205730/3873885 */
/* Could be revisited with other portion of that answer to add animation */
.box {
  --v:calc( ((18/5) * var(--p) - 90)*1deg);
  width:20px;
  height:20px;
  display:inline-block;
  border-radius:50%;
  padding:10px;
  background:
    /* linear-gradient(#ccc,#ccc) content-box, */
    linear-gradient(var(--v), #e6e6e6     50%,transparent 0) 0/min(100%,(50 - var(--p))*100%),
    linear-gradient(var(--v), transparent 50%, #123b4f        0) 0/min(100%,(var(--p) - 50)*100%),
    linear-gradient(to right, #e6e6e6 50%,#123b4f 0);
}

main { 
	margin-bottom: 10px;
}

@media (min-width: 640px) {
	main {
		max-width: none;
	}
}

</style>
