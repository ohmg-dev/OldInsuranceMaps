<script>
export let PLACE;
export let LISTS;

import TitleBar from './components/TitleBar.svelte';

function update(place_slug) {
	// take a --- selection to mean clear that category, so re-fetch the parent
	if (place_slug === "---") {
		for (let [key, value] of Object.entries(LISTS)) {
			if (value.selected === "---") {break}
			place_slug = value.selected;
		}
	}
	fetch(`/${place_slug}?f=json`, {
	}).then(response => response.json())
		.then(result => {
			PLACE = result.PLACE;
			LISTS = result.LISTS;
			history.replaceState({slug:PLACE.slug}, PLACE.display_name, `/${PLACE.slug}`);
			document.title = PLACE.display_name;
	})
}

$: sideLinks = PLACE.volumes.length > 0 ? [
		{
			display: "Open in main viewer",
			url: `/viewer/${PLACE.slug}/`,
			external: true,
		},
	] : [];

let lvl_1;
let lvl_2;
let lvl_3;
let lvl_4;
let lvl_5;

</script>
<TitleBar TITLE={PLACE.display_name} SIDE_LINKS={sideLinks} ICON_LINKS={[]}/>

<div class="breadcrumbs-select-row">
	<select bind:value={LISTS[1].selected} on:change={() => {update(LISTS[1].selected)}}>
		{#each LISTS[1].options as i}
		<option value={i.slug}>{i.display_name} {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option>
		{/each}
	</select>
	<select bind:value={LISTS[2].selected} on:change={() => {update(LISTS[2].selected)}}>
		<option value="---">---</option>
		{#each LISTS[2].options as i}
		<option value={i.slug}>{i.display_name} {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option>
		{/each}
	</select>
	<select bind:value={LISTS[3].selected} disabled={LISTS[2].selected === "---"} on:change={() => {update(LISTS[3].selected)}}>
		<option value="---">---</option>
		{#each LISTS[3].options as i}
		<option value={i.slug}>{i.display_name} {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option>
		{/each}
	</select>
	<select bind:value={LISTS[4].selected} disabled={LISTS[2].selected === "---"} on:change={() => {update(LISTS[4].selected)}}>
		<option value="---">---</option>
		{#each LISTS[4].options as i}
		<option value={i.slug}>{i.display_name} {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option>
		{/each}
	</select>
</div>

<div style="font-style:italic;">
	{#each PLACE.breadcrumbs as bc, n}
	<button on:click={() => {update(bc.slug)}}>{bc.name}</button>{#if n != PLACE.breadcrumbs.length-1}&nbsp;&rarr;&nbsp;{/if}
	{/each}
</div>
<div style="display:flex;">
	<div style="width:50%">
		<h2>Locales</h2>
		{#if PLACE.descendants.length > 0}
		<ul style="padding-left:20px">
			{#each PLACE.descendants as d}
			<li>
				<button on:click={() => {update(d.slug)}} style="{d.volume_count_inclusive == 0 ? 'color:#333333;' : ''}">
				{d.display_name} {#if d.volume_count_inclusive != 0}({d.volume_count_inclusive}){/if}
				</button>
			</li>
			{/each}
		</ul>
		{:else}
		<p><em>---</em></p>
		{/if}
	</div>
	<div style="width:50%">
		<h2>Maps</h2>
		{#if PLACE.volumes.length > 0}
		<ul style="padding-left:20px">
			{#each PLACE.volumes as v}
			<li><a href="/loc/{v.identifier}">{v.year}{#if v.volume_no} vol. {v.volume_no}{/if}</a></li>
			{/each}
		</ul>
		{:else}
		<p><em>---</em></p>
		{/if}
	</div>
</div>
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
	margin-top: 5px;
}
.breadcrumbs-select-row select {
	/* min-width: 35px; */
	margin-right: 3px;
	/* background: none; */
	/* border: none; */
	color: #2c689c;
	cursor: pointer;
}
</style>
