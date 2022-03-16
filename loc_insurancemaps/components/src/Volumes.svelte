<script>
import {TableSort} from 'svelte-tablesort'

export let STARTED_VOLUMES;

</script>

<main>
	<h1>Volumes in progress</h1>
	<p>The following volumes have been loaded, and are in the process of being georeferenced. As more people use the system, this list will grow.</p>
	<div style="overflow-x:auto;">
		{#if STARTED_VOLUMES.length == 0}
		<p><em>No volumes have been started yet.</em></p>
		{:else}
		<TableSort items={STARTED_VOLUMES}>
			<tr slot="thead">
				<th data-sort="title" style="max-width:300px;">Community</th>
				<th data-sort="year_vol">Year</th>
				<th data-sort="sheet_ct" style="width:55px; text-align:center;">Sheets</th>
				<th data-sort="loaded_by_name" style="text-align:center;">Loaded by</th>
				<th data-sort="unprepared_ct" style="width:25px; text-align:center; border-left: 1px solid gray;">U</th>
				<th data-sort="prepared_ct" style="width:25px; text-align:center;">P</th>
				<th data-sort="georeferenced_ct" style="width:25px; text-align:center;">G</th>
			</tr>
			<tr slot="tbody" let:item={v}>
				<td>
					<a href={v.urls.summary} alt="{v.title}" title="{v.title}">{v.city}, {v.county_equivalent}</a>
				</td>
				<td>{v.year_vol}</td>
				<td style="text-align:center;">{v.sheet_ct}</td>
				<td style="text-align:center;"><a href={v.loaded_by_profile}>{v.loaded_by_name}</a></td>
				<td style="text-align:center; border-left:1px solid gray;">{v.unprepared_ct}</td>
				<td style="text-align:center;">{v.prepared_ct}</td>
				<td style="text-align:center;">{v.georeferenced_ct}</td>
			</tr>
		</TableSort>
		{/if}
	</div>
</main>

<style>

main { 
	margin-bottom: 10px;
}

@media (min-width: 640px) {
	main {
		max-width: none;
	}
}

</style>