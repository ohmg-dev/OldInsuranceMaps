<script>
	import TitleBar from '@components/layout/TitleBar.svelte';
	import Items from '@components/lists/Items.svelte';

	import IconContext from 'phosphor-svelte/lib/IconContext';
	import ArrowRight from "phosphor-svelte/lib/ArrowRight";
	import { iconProps } from "@helpers/utils"


export let PLACE;
export let ITEM_API_URL;
export let OHMG_API_KEY;


let reinitList = [{}]

let showAllSublocales = false;
$: subLocales = PLACE.descendants
$: subLocalesWithMaps = PLACE.descendants.filter(function (i) {return i.volume_count_inclusive != 0})
$: localeList = showAllSublocales ? subLocales : subLocalesWithMaps

function update(place_slug) {
	// take a --- selection to mean clear that category, so re-fetch the parent
	if (place_slug === "---") {
		for (let [key, value] of Object.entries(PLACE.select_lists)) {
			if (value.selected === "---") {break}
			place_slug = value.selected;
		}
	}
	fetch(`/${place_slug}?f=json`, {
	}).then(response => response.json())
		.then(result => {
			PLACE = result.PLACE;
			history.pushState({slug:PLACE.slug}, PLACE.display_name, `/${PLACE.slug}`);
			document.title = PLACE.display_name;
			reinitList = [{}];
	})
}

$: sideLinks = PLACE.volumes.length > 0 ? [
		{
			display: "Open in main viewer",
			url: `/viewer/${PLACE.slug}/`,
			external: true,
		},
	] : [];

$: VIEWER_LINK = PLACE.volumes.length > 0 ? `/viewer/${PLACE.slug}/` : '';

</script>

<IconContext values={iconProps} >
<div class="breadcrumbs-select-row">
	<select bind:value={PLACE.select_lists[1].selected} on:change={() => {update(PLACE.select_lists[1].selected)}}>
		{#each PLACE.select_lists[1].options as i}
		<option value={i.slug}>{i.display_name} {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option>
		{/each}
	</select>
	<ArrowRight size={12} />
	<select bind:value={PLACE.select_lists[2].selected} on:change={() => {update(PLACE.select_lists[2].selected)}}>
		<option value="---">---</option>
		{#each PLACE.select_lists[2].options as i}
		<option value={i.slug}>{i.display_name} {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option>
		{/each}
	</select>
	<ArrowRight size={12} />
	<select bind:value={PLACE.select_lists[3].selected} disabled={PLACE.select_lists[2].selected === "---"} on:change={() => {update(PLACE.select_lists[3].selected)}}>
		<option value="---">---</option>
		{#each PLACE.select_lists[3].options as i}
		<option value={i.slug}>{i.display_name} {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option>
		{/each}
	</select>
	<ArrowRight size={12} />
	<select bind:value={PLACE.select_lists[4].selected} disabled={PLACE.select_lists[2].selected === "---"} on:change={() => {update(PLACE.select_lists[4].selected)}}>
		<option value="---">---</option>
		{#each PLACE.select_lists[4].options as i}
		<option value={i.slug}>{i.display_name} {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option>
		{/each}
	</select>
</div>
<TitleBar TITLE={PLACE.display_name} {VIEWER_LINK}/>
<div style="display:flex;">
	<div id="sub-locale-panel" style="margin-right:15px; min-width:250px;">
		{#if PLACE.parents.length > 0}
		<h4>Super-locale</h4>
		<ul class="sub-list">
			{#each PLACE.parents as d}
			<li>
				<button on:click={() => {update(d.slug)}}>
				{d.display_name}
				</button>
			</li>
			{/each}
		</ul>
		{/if}
		{#if PLACE.descendants.length > 0}
		<h4>Sub-locales</h4>
		<div style="display:flex; justify-content:end;">
			<label title="Show all sub-locales, even those without maps">show all sub-locales<input type='checkbox' bind:checked={showAllSublocales} /></label>
		</div>
		{#if localeList.length > 0}
		<ul class="sub-list">
			{#each localeList as d}
			<li>
				<button on:click={() => {update(d.slug)}} style="{d.volume_count_inclusive == 0 ? 'color:#333333;' : ''}">
				{d.display_name}{#if d.volume_count_inclusive > 0}&nbsp;({d.volume_count_inclusive}){/if}
				</button>
			</li>
			{/each}
		</ul>
		{:else}
		<p><em>---</em></p>
		{/if}
		{/if}
	</div>
	<div id="items-panel" style="flex-grow:1; overflow-x:auto;">
		<h3>Maps</h3>
		{#each reinitList as key (key)}
		<Items ITEM_API_URL={ITEM_API_URL} OHMG_API_KEY={OHMG_API_KEY} ALL_ITEMS={[]} PLACE_SLUG={PLACE.slug} PLACE_INCLUSIVE={true} />
		{/each}
	</div>
</div>
</IconContext>

<style>
button {
	border: none;
	background: none;
	color: #2c689c;
}
button:hover {
	color: #1b4060;
	text-decoration: underline;
}
button:disabled {
	color:#555;
	text-decoration: none;
}
.breadcrumbs-select-row {
	display:flex;
	flex-direction:row;
	flex-wrap: wrap;
	align-items: center;
	padding: 10px 0px;
	font-size: .95em;
}
.breadcrumbs-select-row select {
	color: #2c689c;
	cursor: pointer;
}
.breadcrumbs-select-row select:disabled {
	cursor: default;
}
:global(.breadcrumbs-select-row svg) {
	margin: 0px 2px;
}
.sub-list {
	padding: 0;
	margin: 0;
	list-style: none;
	max-height: calc(100vh - 435px);
	overflow-y: scroll;
	background: #e9e9ed;
	border: 1px solid #8f8f9d;
  	border-radius: 4px;
}
.sub-list li {
	padding: 5px;
}
.sub-list li:nth-child(2n) {
  background-color: #f6f6f6;
}
.sub-list li:nth-child(2n+1) {
  background-color: #ffffff;
}

@media (max-width: 768px) {
	#sub-locale-panel {
	  display: none;
	}
	#items-panel {
		width: 100%;
	}
	.breadcrumbs-select-row {
		flex-direction: column;
	}
	.breadcrumbs-select-row select {
		margin-bottom: 2px;
		width: 100%;
	}
	:global(.breadcrumbs-select-row svg) {
		display: none;
	}
  }
</style>
