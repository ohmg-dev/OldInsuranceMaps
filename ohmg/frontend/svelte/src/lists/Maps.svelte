<script>
import {TableSort} from 'svelte-tablesort';
import Link from '@/base/Link.svelte';
    import LoadingEllipsis from '../base/LoadingEllipsis.svelte';
	import { getFromAPI } from '@/lib/requests';

export let CONTEXT;
export let PLACE_SLUG = "";
export let PLACE_INCLUSIVE = false;

let fullList = [];
let items = [];
let loading = true

let showAll = false;
$: url = PLACE_SLUG ?
	`/api/beta2/maps/?locale=${PLACE_SLUG}&locale_inclusive=${PLACE_INCLUSIVE}&loaded=${!showAll}`
	: `/api/beta2/maps/?loaded=${!showAll}`

function handleFetch(url) {
	getFromAPI(
		url,
		CONTEXT.ohmg_api_headers,
		(result) => {
			const flattened = []
			result.forEach( function(item) {
				item.load_date = item.loaded_by ? item.load_date : "---";
				item.loaded_by_name = item.loaded_by ? item.loaded_by.username : "---";
				item.loaded_by_profile = item.loaded_by ? item.loaded_by.profile_url : "";
				item.unprepared_ct = item.stats.unprepared_ct;
				item.prepared_ct = item.stats.prepared_ct;
				item.georeferenced_ct = item.stats.georeferenced_ct;
				item.skipped_ct = item.stats.skipped_ct;
				item.percent = item.stats.percent;
				item.mm_ct = item.stats.mm_todo;
				item.mm_display = item.stats.mm_display;
				item.mm_percent = item.stats.mm_percent;
				flattened.push(item)
			})
			items = flattened;
			loading = false
		}
	)
}
$: handleFetch(url)

function updateFilteredList(filterText) {
	if (filterText && filterText.length > 0) {
		items = [];
		fullList.forEach( function(vol) {
			const volumeName = vol.title.toUpperCase();
			const filterBy = filterText.toUpperCase();
			if (volumeName.indexOf(filterBy) > -1) {
				items.push(vol);
			}
		});
	} else {
		items = fullList;
	}
}
let filterInput;
$: updateFilteredList(filterInput)

</script>
<div class="filter-container">
	<input style="flex-grow: 1;" type="text" id="filterInput" placeholder="Filter by title..." bind:value={filterInput}>
	<label title="Show maps that haven't yet been loaded." style="margin-left:5px;">show all<input type="checkbox" bind:checked={showAll} /></label>
</div>
<div style="overflow-x:auto;">
	{#if loading}
	<div style="text-align:center;">
		<LoadingEllipsis />
	</div>
	{:else if items.length == 0}
	<div style="text-align:center;">
		<p><em>No maps found...</em></p>
	</div>
	{:else}
	<TableSort {items}>
		<tr slot="thead">
			<th data-sort="title" style="max-width:300px;" title="Title">Title</th>
			<th data-sort="year_vol" title="Year of publication">Year</th>
			<th data-sort="sheet_ct" style="width:55px; text-align:center;" title="Number of documents in publication">Sheets</th>
			<th data-sort="loaded_by_name" style="text-align:center;" title="Volume originally loaded by this user">Loaded by</th>
			<th data-sort="load_date" style="text-align:center;" title="Date this item was loaded">Load date</th>
			<th data-sort="unprepared_ct" style="width:25px; text-align:center; border-left: 1px solid gray;" title="Number of unprepared documents">U</th>
			<th data-sort="prepared_ct" style="width:25px; text-align:center;" title="Number of prepared documents">P</th>
			<th data-sort="georeferenced_ct" style="width:25px; text-align:center;" title="Number of georeferenced documents">G</th>
			<th data-sort="skipped_ct" style="width:25px; text-align:center;" title="Number of skipped pieces">S</th>
			<th data-sort="percent" style="width:25px; text-align:center; border-left:1px solid gray;" title="Percent complete - G/(U+P+G)">%</th>
			<th data-sort="mm_percent" style="width:25px; text-align:center; border-left:1px solid gray;" title="Layers included in multimask">MM</th>
			<th data-sort="mj_exists" style="width:25px; text-align:center; border-left:1px solid gray;" title="MosaicJSON prepared for this volume?">MJ</th>
			<th data-sort="gt_exists" style="width:25px; text-align:center;" title="GeoTIFF mosaic has been prepared for this volume">GT</th>
		</tr>
		<tr slot="tbody" let:item={v} style="height:38px;">
			<td>
				<Link href={v.urls.summary} title="Go to summary">{v.title}</Link>
			</td>
			<td>{v.year_vol}</td>
			<td style="text-align:center;">{v.sheet_ct}</td>
			<td style="text-align:center;">
				{#if v.loaded_by_name != "---" }
				<Link href={v.loaded_by_profile}>{v.loaded_by_name}</Link>
				{:else}
				{v.loaded_by_name}
				{/if}
			</td>
			<td style="text-align:center;">{v.load_date}</td>
			<td style="text-align:center; border-left:1px solid gray;">{v.unprepared_ct}</td>
			<td style="text-align:center;">{v.prepared_ct}</td>
			<td style="text-align:center;">{v.georeferenced_ct}</td>
			<td style="text-align:center;">{v.skipped_ct}</td>
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
	display: flex;
	margin-bottom: 5px;
	align-items: center;
}

/* Credit to this SO answer: https://stackoverflow.com/a/52205730/3873885 */
/* Could be revisited with other portion of that answer to add animation */
.box {
  --v:calc( ((18/5) * var(--p) - 90)*1deg);
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
