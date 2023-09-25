<script>
import {TableSort} from 'svelte-tablesort'

export let ITEM_API_URL;
export let OHMG_API_KEY;

let all_items = [];
let filtered_items = [];
let loading = true

const apiHeaders = {
	'X-API-Key': OHMG_API_KEY,
}

fetch(ITEM_API_URL, { headers: apiHeaders })
	.then(response => response.json())
	.then(result => {
		all_items = flatten_response(result);
		filtered_items = all_items;
	});

function flatten_response(items_json) {
	const flattened = []
	items_json.forEach( function(item) {
		item.loaded_by_name = item.loaded_by.username;
		item.loaded_by_profile = item.loaded_by.profile_url;
		item.unprepared_ct = item.stats.unprepared_ct;
		item.prepared_ct = item.stats.prepared_ct;
		item.georeferenced_ct = item.stats.georeferenced_ct;
		item.percent = item.stats.percent;
		item.mm_ct = item.stats.mm_todo;
		item.mm_display = item.stats.mm_display;
		item.mm_percent = item.stats.mm_percent;
		flattened.push(item)
	})
	loading = false
	return flattened
}

function updateFilteredList(filterText) {
	if (filterText && filterText.length > 0) {
		filtered_items = [];
		all_items.forEach( function(vol) {
			const volumeName = vol.title.toUpperCase();
			const filterBy = filterText.toUpperCase();
			if (volumeName.indexOf(filterBy) > -1) {
				filtered_items.push(vol);
			}
		});
	} else {
		filtered_items = all_items;
	}
}
let filterInput;
$: updateFilteredList(filterInput)

</script>
<div class="filter-container">
	<input type="text" id="filterInput" placeholder="Filter by title..." bind:value={filterInput}>
</div>
<div style="overflow-x:auto;">
	{#if loading}
	<div style="text-align:center;">
		<div class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
	</div>
	{:else if filtered_items.length == 0}
	<div style="text-align:center;">
		<p><em>No items found...</em></p>
	</div>
	{:else}
	<TableSort items={filtered_items}>
		<tr slot="thead">
			<th data-sort="title" style="max-width:300px;" title="Title">Item Title</th>
			<th data-sort="year_vol" title="Year of publication">Year</th>
			<th data-sort="sheet_ct" style="width:55px; text-align:center;" title="Number of sheets in publication">Sheets</th>
			<th data-sort="loaded_by_name" style="text-align:center;" title="Volume originally loaded by this user">Loaded by</th>
			<th data-sort="load_date" style="text-align:center;" title="Date this item was loaded">Load date</th>
			<th data-sort="unprepared_ct" style="width:25px; text-align:center; border-left: 1px solid gray;" title="Number of unprepared sheets">U</th>
			<th data-sort="prepared_ct" style="width:25px; text-align:center;" title="Number of prepared documents">P</th>
			<th data-sort="georeferenced_ct" style="width:25px; text-align:center;" title="Number of georeferenced documents">G</th>
			<th data-sort="percent" style="width:25px; text-align:center; border-left:1px solid gray;" title="Percent complete - G/(U+P+G)">%</th>
			<th data-sort="mm_percent" style="width:25px; text-align:center; border-left:1px solid gray;" title="Layers included in multimask">MM</th>
			<th data-sort="mj_exists" style="width:25px; text-align:center; border-left:1px solid gray;" title="MosaicJSON prepared for this volume?">MJ</th>
			<th data-sort="gt_exists" style="width:25px; text-align:center;" title="GeoTIFF mosaic has been prepared for this volume">GT</th>
		</tr>
		<tr slot="tbody" let:item={v} style="height:38px;">
			<td>
				<a href={v.urls.summary} alt="Go to item summary" title="Go to summary">{v.title}</a>
			</td>
			<td>{v.year_vol}</td>
			<td style="text-align:center;">{v.sheet_ct}</td>
			<td style="text-align:center;"><a href={v.loaded_by_profile}>{v.loaded_by_name}</a></td>
			<td style="text-align:center;">{v.load_date}</td>
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
			<td style="text-align:center; border-left:1px solid gray;">
				{#if v.gt_exists}
				<span style="color:green">✓</span>
				{:else}
				<span style="color:red">x</span>
				{/if}
			</td>
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


</style>
