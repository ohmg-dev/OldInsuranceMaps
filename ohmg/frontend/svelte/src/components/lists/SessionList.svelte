<script>
import {TableSort} from 'svelte-tablesort';
import Select from 'svelte-select';

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
export let allowRefresh = true;
export let showTypeFilter = true;
export let typeFilter;
export let showMap = true;
export let mapFilterItems;
export let mapFilter;

const typeFilterOptions = [
	{label: "Prep", id: "p"},
	{label: "Georef", id: "g"},
]

let loading = false;

let items = [];

let offset = 0;
let total = 0

let limitOptions = [10, 25, 50, 100]
let currentLimit = limit;
$: useLimit = typeof currentLimit == "string" ? currentLimit : currentLimit.value
$: limitInt = parseInt(useLimit)

$: {
	loading = true;
	let fetchUrl = `${CONTEXT.urls.get_sessions}?offset=${offset}`
	if (limit != 0 && useLimit) {
		fetchUrl = `${fetchUrl}&limit=${useLimit}`
	}
	if (FILTER_PARAM) {
		fetchUrl += `&${FILTER_PARAM}`
	}
	if (typeFilter) {
		fetchUrl += `&type=${typeFilter.id}`
	}
	if (mapFilter) {
		fetchUrl += `&map=${mapFilter.id}`
	}
	fetch(fetchUrl, { headers: CONTEXT.ohmg_api_headers })
		.then(response => response.json())
		.then(result => {
			items = result.items;
			total = result.count;
			loading = false;
		});
}

</script>
<SessionListModal id={"modal-session-list"} />
<div>
	<div class="level" style="margin:.5em 0;">
		<div class="level-left">
			<button class="is-icon-link" on:click={() => {getModal('modal-session-list').open()}}><Question /></button>
			{#if mapFilterItems}
			<Select items={mapFilterItems} bind:value={mapFilter}
				id="id"
				label="title"
				placeholder="Filter by map..."
				listAutoWidth={false}
				containerStyles="width:300px;"
				on:change={() => {offset = 0}}
			/>
			{/if}
			{#if showTypeFilter}
			<Select items={typeFilterOptions} bind:value={typeFilter}
				id="id"
				label="label"
				placeholder="Filter by type..."
				searchable={false}
				containerStyles="width:150px;"
				on:change={() => {offset = 0}}
			/>
			{/if}
		</div>
		<div class="level-right">
			{#if limit != 0}
			<div class="level-item">
				<Select items={limitOptions} bind:value={currentLimit}
					searchable={false}
					clearable={false}
					containerStyles="width:65px;"
				/>
			</div>
			{/if}
			{#if allowRefresh}
			<button class="is-icon-link" disabled={loading} on:click={() => {offset = 1000; offset=0}}><ArrowsClockwise /></button>
			{/if}
			{#if paginate}
			<div class="level-item">
				<button class="is-icon-link" disabled={offset < limitInt || loading || offset == 0} on:click={() => {offset = offset - limitInt}}><CaretDoubleLeft /></button>
				<span>{offset} - {offset + limit < total ? offset + limitInt : total} ({total})</span>
				<button class="is-icon-link" disabled={offset + limitInt >= total || loading} on:click={() => {offset = offset + limitInt}}><CaretDoubleRight /></button>
			</div>
			{/if}
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
				<th title="Session Id">Id</th>
				<th title="Session Type">Type</th>
				{#if showUser}
				<th title="Username">User</th>
				{/if}
				{#if showMap}
				<th title="Map">Map</th>
				{/if}
				{#if showResource}
				<th title="Document, Region or Layer proccessed">Resource <input type='checkbox' bind:checked={showThumbs} title="Show thumbnails"/></th>
				{/if}
				<th>Stage</th>
				<th title="Session result note">Result</th>
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
				{#if showMap}
				<td>
					<Link href={`/map/${s.map.identifier}`} title={s.map.title}>{s.map.title}</Link>
				</td>
				{/if}
				{#if showResource}
				<td>
					{#if s.type === "p"}
					{#if showThumbs}
					<div class="thumb-container">
						<img style="max-height:50px;" src={s.doc2.urls.thumbnail} alt="{s.doc2.nickname}"/>
					</div>
					{/if}
					<Link href="{s.doc2.urls.resource}" title="{s.doc2.nickname}">
						{s.doc2.nickname}
					</Link>
					{:else if s.type === "g" || s.type === "t"}
						{#if s.lyr2}
						{#if showThumbs}
						<div class="thumb-container">
							<img style="max-height:50px;" src={s.lyr2.urls.thumbnail} alt="{s.reg2.nickname}"/>
						</div>
						{/if}
						<Link href="{s.lyr2.urls.resource}" title="{s.lyr2.nickname}">
							{s.lyr2.nickname}
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
	td {
		white-space: nowrap;
	}
	.thumb-container {
		width: 65px;
		display: inline-block;
		text-align: center;
	}
</style>
