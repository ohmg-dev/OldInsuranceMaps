<script>
import {TableSort} from 'svelte-tablesort';

import CaretDoubleLeft from 'phosphor-svelte/lib/CaretDoubleLeft'
import CaretDoubleRight from 'phosphor-svelte/lib/CaretDoubleRight'
import ArrowsClockwise from 'phosphor-svelte/lib/ArrowsClockwise'
import Question from 'phosphor-svelte/lib/Question'

import Link from '@components/base/Link.svelte';
import SessionListModal from './modals/SessionListModal.svelte';
    import { getModal } from '../base/Modal.svelte';
	import LoadingEllipsis from '../base/LoadingEllipsis.svelte';

export let CONTEXT;
export let FILTER_PARAM = '';
export let limit = "10";
export let showThumbs = false;
export let showUser = true;
export let showResource = true;
export let paginate = true;


let loading = false;
let items = [];

let offset = 0;
let total = 0
$: limitInt = parseInt(limit)

$: {
	loading = true;
	let fetchUrl = `${CONTEXT.urls.get_sessions}?offset=${offset}`
	if (limitInt > 0) {
		fetchUrl = `${fetchUrl}&limit=${limitInt}`
	}
	if (FILTER_PARAM) {
		fetchUrl += `&${FILTER_PARAM}`
	}
	fetch(fetchUrl, { headers: CONTEXT.ohmg_api_headers })
		.then(response => response.json())
		.then(result => {
			items = result.items;
			total = result.count;
			loading = false;   
		});
	// console.log(items)
}

</script>
<SessionListModal id={"modal-session-list"} />
<div>
	<div class="btn-row">
		{#if paginate}
		<div class="btn-container">
			<button class="is-icon-link is-sm" disabled={offset < limitInt || loading || offset == 0} on:click={() => {offset = offset - limitInt}}><CaretDoubleLeft /></button>
			<span>{offset} - {offset + limitInt < total ? offset + limitInt : total} ({total})</span>
			<button class="is-icon-link is-sm" disabled={offset + limitInt >= total || loading} on:click={() => {offset = offset + limitInt}}><CaretDoubleRight /></button>
		</div>
		{:else}
		<div></div>
		{/if}
		<div class="btn-container">
			{#if showResource}
			<div>
				<input type='checkbox' bind:checked={showThumbs} title="Show thumbnails"/>
			</div>
			{/if}
			{#if limitInt != 0}
			<div>
				<!-- <label for="limit-select">Show:</label> -->
				<select id="limit-select" type='radio' bind:value={limit} title="Number of results per page">
					<option value="10">10</option>
					<option value="25">25</option>
					<option value="50">50</option>
					<option value="100">100</option>
				</select>
			</div>
			{/if}
			<button class="is-icon-link is-sm" disabled={loading} on:click={() => {offset = 1000; offset=0}}><ArrowsClockwise /></button>
			<button class="is-icon-link is-sm" style="font-size:1.25em" on:click={() => {getModal('modal-session-list').open()}}><Question /></button>
			</div>
		</div>
	<div style="height: 100%; overflow-y:auto; border:1px solid #ddd; border-radius:4px; background:white;">
		{#if loading}
		<div style="display:flex;">
			<LoadingEllipsis />
		</div>
		{:else}
		<TableSort {items}>
			<tr slot="thead">
				<!-- <th data-sort="username" style="max-width:300px;" title="Name of mapped location"></th> -->
				<th title="Session Id">Session Id</th>
				<th title="Session Type">Action</th>
				{#if showUser}
				<th title="Username">User</th>
				{/if}
				{#if showResource}
				<th>Resource</th>
				{/if}
				<th>Stage</th>
				<!-- <th data-sort="psesh_ct" style="width:25px; text-align:center; border-left: 1px solid gray;" title="Number of prep sessions">Prep Sessions</th> -->
				<!-- <th data-sort="gsesh_ct" style="width:25px; text-align:center;" title="Number of georeferencing sessions">Georef. Sessions</th> -->
				<!-- <th data-sort="total_ct" style="width:25px; text-align:center; border-left:1px solid gray;" title="Percent complete - G/(U+P+G)">Total Sessions</th> -->
				<th title="Session result note">Result</th>
				<!-- <th title="Ground control points created">Seconds</th> -->
				<th title="When the session was created">When</th>
			</tr>
			<tr slot="tbody" let:item={s} style="height:38px; vertical-align:center;">
				<td>{s.id}</td>
				<td>
					{#if s.type === "p"}
					<span title="Preparation">Prep</span>
					{:else if s.type === "g"}
					<span title="Georeference">Georef</span>
					{:else if s.type === "t"}
					<span title="Trim">Trim</span>
					{/if}
				</td>
				{#if showUser}
				<td>
					<Link href="{s.user.profile_url}" title="View profile">{s.user.username}</Link>
				</td>
				{/if}
				{#if showResource}
				<td>
					{#if s.type === "p"}
					{#if showThumbs}<img style="max-height:50px;" src={s.doc2.urls.thumbnail} alt="{s.doc2.title}"/>{/if}
					<Link href="{s.doc2.urls.resource}" title="{s.doc2.title}">
						{s.doc2.title}
					</Link>
					{:else if s.type === "g" || s.type === "t"}
						{#if s.lyr2}
						{#if showThumbs}<img style="max-height:50px;" src={s.lyr2.urls.thumbnail} alt="{s.reg2.title}"/>{/if}
						<Link href="{s.lyr2.urls.resource}" title="{s.lyr2.title}">
							{s.lyr2.title}
						</Link>
						{/if}
					{/if}
				</td>
				{/if}
				<td>{s.stage}</td>
				<td>{s.note}</td>
				<!-- <td>{s.user_input_duration}</td> -->
				<td title="{s.date_created.date}">{s.date_created.relative}</td>
			</tr>
		</TableSort>
		{/if}
	</div>
</div>
<style>
	.btn-row {
		display: flex;
		justify-content: space-between;
		padding: 10px 0px;
	}
    .btn-container {
        display:flex;
        align-items:center;
    }
	td {
		white-space: nowrap;
	}
</style>
