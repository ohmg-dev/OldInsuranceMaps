<script>
	import {TableSort} from 'svelte-tablesort';
	import Link from '@components/base/Link.svelte';
	import LoadingEllipsis from '../base/LoadingEllipsis.svelte';

	export let CONTEXT;

	let all_participants = [];
	let items = []

	fetch(CONTEXT.urls.get_users, { headers: CONTEXT.ohmg_api_headers })
		.then(response => response.json())
		.then(result => {
			all_participants = result;
			items = result;
		});

	function updateFilteredList(filterText) {
		if (filterText && filterText.length > 0) {
			items = [];
			all_participants.forEach( function(p) {
				const name = p.username.toUpperCase();
				const filterBy = filterText.toUpperCase();
				if (name.indexOf(filterBy) > -1) {
					items.push(p);
				}
			});
		} else {
			items = all_participants;
		}
	}
	let filterInput;
	$: updateFilteredList(filterInput)

	function toggleList(userId) {
		const listEl = document.getElementById(userId);
		listEl.style.display = listEl.style.display == "flex" ? "none" : "flex";
		const listBtnEl = document.getElementById(userId+"-btn");
		listBtnEl.innerText = listBtnEl.innerText == "show all" ? "hide all" : "show all";
	}
</script>

<input type="text" id="filterInput" placeholder="Filter by username..." bind:value={filterInput}>
<div style="overflow-x:auto;">
	<TableSort {items}>
		<tr slot="thead">
			<th data-sort="username" style="max-width:300px;"></th>
			<th data-sort="username" style="max-width:300px;" title="Name of mapped location">Username</th>
			<th data-sort="load_ct" title="Number of unprepared sheets">Loaded Volumes</th>
			<th data-sort="psesh_ct" style="width:25px; text-align:center; border-left: 1px solid gray;" title="Number of prep sessions">Prep Sessions</th>
			<th data-sort="gsesh_ct" style="width:25px; text-align:center;" title="Number of georeferencing sessions">Georef. Sessions</th>
			<th data-sort="total_ct" style="width:25px; text-align:center; border-left:1px solid gray;" title="Percent complete - G/(U+P+G)">Total Sessions</th>
			<th data-sort="gcp_ct" style="width:25px; text-align:center; border-left:1px solid gray;" title="Ground control points created">GCPs</th>
		</tr>
		<tr slot="tbody" let:item={p} style="height:38px;">
			<td>
				<img style="height:30px; width:30px; border-radius:5px;" src={p.image_url} alt={p.username} />
			</td>
			<td>
				<Link href={p.profile_url} title="Profile for {p.username}">
					{p.username}
				</Link>
			</td>
			<td style="">
				<div>
				{p.load_ct}{#if p.volumes.length > 0}&nbsp;&mdash;{/if}
				{#each p.volumes as v, n}
					{#if n <= 2}
					<Link href={v.url}>{v.title}</Link>{#if n != p.volumes.length - 1},&nbsp;{/if}
					{/if}
				{/each}
				{#if p.volumes.length > 3}
				<button id="{p.username}-btn" on:click={() => toggleList(p.username)}>show all</button>
				{/if}
				</div>
				{#if p.volumes.length > 3}
				<div id="{p.username}" class="full-volume-list">
					<ul>
					{#each p.volumes as v}
					<li><Link href={v.url}>{v.title}</Link></li>
					{/each}
					</ul>
				</div>
				{/if}
			</td>
			<td style="text-align:center; border-left:1px solid gray;">{p.psesh_ct}</td>
			<td style="text-align:center;">{p.gsesh_ct}</td>
			<td style="text-align:center; border-left:1px solid gray;">{p.total_ct}</td>
			<td style="text-align:center; border-left:1px solid gray;">{p.gcp_ct}</td>
		</tr>
	</TableSort>
	{#if all_participants.length === 0}
	<LoadingEllipsis />
	{/if}
</div>
<style>
	.full-volume-list {
		display: none;
	}

	tr th {
		vertical-align: top;
	}
	tr td {
		vertical-align: top;
	}
</style>