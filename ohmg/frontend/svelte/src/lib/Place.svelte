<script>
export let PLACE;
console.log(PLACE)
import TitleBar from './components/TitleBar.svelte';

let onlySLMaps = true;
$: subLocales = PLACE.descendants
$: subLocalesWithMaps = PLACE.descendants.filter(function (i) {return i.volume_count_inclusive != 0})
$: localeList = onlySLMaps ? subLocalesWithMaps : subLocales

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
	})
}

$: sideLinks = PLACE.volumes.length > 0 ? [
		{
			display: "Open in main viewer",
			url: `/viewer/${PLACE.slug}/`,
			external: true,
		},
	] : [];

</script>

<div class="breadcrumbs-select-row">
	<select bind:value={PLACE.select_lists[1].selected} on:change={() => {update(PLACE.select_lists[1].selected)}}>
		{#each PLACE.select_lists[1].options as i}
		<option value={i.slug}>{i.display_name} {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option>
		{/each}
	</select>
	<select bind:value={PLACE.select_lists[2].selected} on:change={() => {update(PLACE.select_lists[2].selected)}}>
		<option value="---">---</option>
		{#each PLACE.select_lists[2].options as i}
		<option value={i.slug}>{i.display_name} {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option>
		{/each}
	</select>
	<select bind:value={PLACE.select_lists[3].selected} disabled={PLACE.select_lists[2].selected === "---"} on:change={() => {update(PLACE.select_lists[3].selected)}}>
		<option value="---">---</option>
		{#each PLACE.select_lists[3].options as i}
		<option value={i.slug}>{i.display_name} {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option>
		{/each}
	</select>
	<select bind:value={PLACE.select_lists[4].selected} disabled={PLACE.select_lists[2].selected === "---"} on:change={() => {update(PLACE.select_lists[4].selected)}}>
		<option value="---">---</option>
		{#each PLACE.select_lists[4].options as i}
		<option value={i.slug}>{i.display_name} {#if i.volume_count_inclusive != 0}({i.volume_count_inclusive}){/if}</option>
		{/each}
	</select>
</div>
<TitleBar TITLE={PLACE.display_name} SIDE_LINKS={sideLinks} ICON_LINKS={[]}/>
<div style="display:flex; justify-content: space-between;">
	<div style="width:30%">
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
		<h4>Sub-locales</h4>
		<input style="margin-left: 0px;" type='checkbox' bind:checked={onlySLMaps} /><span><em>only show those with maps</em></span>
		{#if PLACE.descendants.length > 0 && PLACE.descendants.filter(function (i) {return i.volume_count_inclusive != 0}).length > 0}
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
	</div>
	<div style="width:60%">
		<h3>Maps</h3>
		{#if PLACE.volumes.length > 0}
		<ul class="sub-list">
			{#each PLACE.volumes as v}
			<li><a href="/loc/{v.identifier}">{v.year}{#if v.volume_no}&nbsp;vol. {v.volume_no}{/if}</a></li>
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
	flex-wrap: wrap;
	padding: 10px 0px;
	font-size: .95em;
}
.breadcrumbs-select-row select {
	/* min-width: 35px; */
	margin-right: 3px;
	/* background: none; */
	/* border: none; */
	color: #2c689c;
	cursor: pointer;
}
.breadcrumbs-select-row select:disabled {
	cursor: default;
}
.sub-list {
	padding: 0;
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
</style>
