<script>
import {TableSort} from 'svelte-tablesort'

export let STARTED_VOLUMES;

</script>

<main>
	<h1>Volumes in progress</h1>
	<p>The following volumes have been loaded, and are in the process of being georeferenced. As more people use the system, this list will grow.</p>
	<div>
		{#if STARTED_VOLUMES.length == 0}
		<p><em>No volumes have been started yet.</em></p>
		{:else}
		<TableSort items={STARTED_VOLUMES}>
			<tr slot="thead">
				<th data-sort="title" style="max-width:300px;">Community</th>
				<th data-sort="year" style="width:65px;">Year</th>
				<th data-sort="sheet_ct" style="width:65px;">Sheets</th>
				<th data-sort="loaded_by.name">Loaded by</th>
			</tr>
			<tr slot="tbody" let:item={v}>
				<td>
					<a href={v.urls.summary} alt={v.title} title={v.title}>{v.city}, {v.county_equivalent}</a>
				</td>
				<td>{v.year}</td>
				<td style="text-align:center;">{v.sheet_ct}</td>
				<td><a href={v.loaded_by.profile}>{v.loaded_by.name}</a></td>
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