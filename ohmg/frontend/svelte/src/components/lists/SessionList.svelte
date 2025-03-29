<script>
	import {TableSort} from 'svelte-tablesort';
	import Select from 'svelte-select';
	import { format } from 'date-fns';

	import ArrowsClockwise from 'phosphor-svelte/lib/ArrowsClockwise'
	import Question from 'phosphor-svelte/lib/Question'

	import Link from '../common/Link.svelte';
	import SessionListModal from '../modals/SessionListModal.svelte';
    import { getModal } from '../modals/BaseModal.svelte';
	import DatePicker from '../buttons/DatePicker.svelte';
    import PaginationButtons from '../buttons/PaginationButtons.svelte';

	import { getFromAPI } from "../../lib/requests";

	export let CONTEXT;
	export let FILTER_PARAM = '';
	export let limit = "10";
	export let showThumbs = false;
	export let showUser = true;
	export let userFilterItems;
	export let userFilter;
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

	let startDate;
	let endDate;

	let offset = 0;
	let total = 0;

	let currentLimit = limit;
	$: useLimit = typeof currentLimit == "string" ? currentLimit : currentLimit.value

	let dateFormat = 'yyyy-MM-dd';
	const formatDate = (dateString) => dateString && format(new Date(dateString), dateFormat) || '';

	$: formattedStartDate = formatDate(startDate);
	$: formattedEndDate = formatDate(endDate);

	$: dqParam = formattedStartDate && formattedEndDate ?`&date_range=${formattedStartDate},${formattedEndDate}` : ""

	$: {
		loading = true;
		let fetchUrl = `/api/beta2/sessions/?offset=${offset}`
		if (limit != 0 && useLimit) {
			fetchUrl = `${fetchUrl}&limit=${useLimit}`
		}
		// ultimately should deprecate this and move its functionality into this component
		if (FILTER_PARAM) {
			fetchUrl += `&${FILTER_PARAM}`
		}
		if (typeFilter) {
			fetchUrl += `&type=${typeFilter.id}`
		}
		if (mapFilter) {
			fetchUrl += `&map=${mapFilter.id}`
		}
		if (dqParam) {
			fetchUrl += dqParam
		}
		if (userFilter) {
			fetchUrl += `&username=${userFilter.id}`
		}
		getFromAPI(
			fetchUrl,
			CONTEXT.ohmg_api_headers,
			(result) => {
				items = result.items;
				total = result.count;
				loading = false;
			}
		)
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
			<DatePicker bind:startDate bind:endDate />
			{#if userFilterItems}
			<Select items={userFilterItems} bind:value={userFilter}
				id="id"
				label="title"
				placeholder="Filter by user..."
				containerStyles="width:150px;"
				on:change={() => {offset = 0}}
			/>
			{/if}
		</div>
		<div class="level-right">
			{#if paginate}
			<div class="level-item">
				<PaginationButtons bind:currentOffset={offset} bind:total bind:currentLimit />
			</div>
			{/if}
			{#if allowRefresh}
			<button class="is-icon-link" disabled={loading} on:click={() => {offset = 1000; offset=0}}>
				<div style="height:28px" class={loading ? "rotating" : ""}>
					<ArrowsClockwise />
				</div>
			</button>
			{/if}
		</div>
	</div>
	<div style="height: 100%; overflow-y:auto; border:1px solid #ddd; border-radius:4px; background:white;">
		{#if items.length > 0}
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
		{:else}
		<div class="level">
			<div class="level-item" style="margin:5px 0;">
				<em>{loading ? "loading..." : "no results"}</em>
			</div>
		</div>
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

	@-webkit-keyframes rotating /* Safari and Chrome */ {
	from {
		-webkit-transform: rotate(0deg);
		-o-transform: rotate(0deg);
		transform: rotate(0deg);
	}
	to {
		-webkit-transform: rotate(360deg);
		-o-transform: rotate(360deg);
		transform: rotate(360deg);
	}
	}
	@keyframes rotating {
	from {
		-ms-transform: rotate(0deg);
		-moz-transform: rotate(0deg);
		-webkit-transform: rotate(0deg);
		-o-transform: rotate(0deg);
		transform: rotate(0deg);
	}
	to {
		-ms-transform: rotate(360deg);
		-moz-transform: rotate(360deg);
		-webkit-transform: rotate(360deg);
		-o-transform: rotate(360deg);
		transform: rotate(360deg);
	}
	}
	.rotating {
		-webkit-animation: rotating 2s linear infinite;
		-moz-animation: rotating 2s linear infinite;
		-ms-animation: rotating 2s linear infinite;
		-o-animation: rotating 2s linear infinite;
		animation: rotating 2s linear infinite;
	}
</style>
