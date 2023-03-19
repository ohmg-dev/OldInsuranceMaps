<script>
import {TableSort} from 'svelte-tablesort'

export let STARTED_VOLUMES;

let volumes = STARTED_VOLUMES;

function updateFilteredList(filterText) {
	if (filterText && filterText.length > 0) {
		volumes = [];
		STARTED_VOLUMES.forEach( function(vol) {
			const volumeName = vol.title.toUpperCase();
			const filterBy = filterText.toUpperCase();
			if (volumeName.indexOf(filterBy) > -1) {
				volumes.push(vol);
			}
		});
	} else {
		volumes = STARTED_VOLUMES;
	}
}
let filterInput;
$: updateFilteredList(filterInput)

</script>

<input type="text" id="filterInput" placeholder="Filter by place name..." bind:value={filterInput}>
<div style="overflow-x:auto;">
	{#if volumes.length == 0}
	<p><em>No volumes have been started yet.</em></p>
	{:else}
	<TableSort items={volumes}>
		<tr slot="thead">
			<th data-sort="place_name" style="max-width:300px;" title="Name of mapped location">Place</th>
			<th data-sort="year_vol" title="Year of publication">Year</th>
			<th data-sort="sheet_ct" style="width:55px; text-align:center;" title="Number of sheets in publication">Sheets</th>
			<th data-sort="loaded_by_name" style="text-align:center;" title="Volume originally loaded by this user">Loaded by</th>
			<th data-sort="unprepared_ct" style="width:25px; text-align:center; border-left: 1px solid gray;" title="Number of unprepared sheets">U</th>
			<th data-sort="prepared_ct" style="width:25px; text-align:center;" title="Number of prepared documents">P</th>
			<th data-sort="georeferenced_ct" style="width:25px; text-align:center;" title="Number of georeferenced documents">G</th>
			<th data-sort="percent" style="width:25px; text-align:center; border-left:1px solid gray;" title="Percent complete - G/(U+P+G)">%</th>
			<th data-sort="mm_percent" style="width:25px; text-align:center; border-left:1px solid gray;" title="Layers included in multimask">MM</th>
			<th data-sort="mj_exists" style="width:25px; text-align:center; border-left:1px solid gray;" title="MosaicJSON prepared for this volume?">MJ</th>
			<!-- <th data-sort="gt_exists" style="width:25px; text-align:center;" title="GeoTIFF mosaic has been prepared for this volume">GT</th> -->
		</tr>
		<tr slot="tbody" let:item={v} style="height:38px;">
			<td>
				<a href={v.urls.summary} alt="Go to {v.place_name}" title="Go to {v.place_name}">{v.place_name}</a>
			</td>
			<td>{v.year_vol}</td>
			<td style="text-align:center;">{v.sheet_ct}</td>
			<td style="text-align:center;"><a href={v.loaded_by_profile}>{v.loaded_by_name}</a></td>
			<td style="text-align:center; border-left:1px solid gray;">{v.unprepared_ct}</td>
			<td style="text-align:center;">{v.prepared_ct}</td>
			<td style="text-align:center;">{v.georeferenced_ct}</td>
			<td style="text-align:center; border-left:1px solid gray;"><div class="box" style="--p:{v.percent};"></div></td>
			<td style="text-align:center; border-left:1px solid gray;">{v.mm_display}</td>
			<td style="text-align:center; border-left:1px solid gray;">
				{#if v.mj_exists}
				<span style="color:green">✓</span>
				{:else}
				<span style="color:red">x</span>
				{/if}
			</td>
			<!-- <td style="text-align:center;">{v.gt_exists}</td> -->
		</tr>
	</TableSort>
	{/if}
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
