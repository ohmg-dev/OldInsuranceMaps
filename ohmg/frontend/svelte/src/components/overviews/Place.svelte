<script>
	import TitleBar from '@components/layout/TitleBar.svelte';
	import PlaceBreadcrumbsSelect from '@components/layout/PlaceBreadcrumbsSelect.svelte';
	import Maps from '@components/lists/Maps.svelte';

	import IconContext from 'phosphor-svelte/lib/IconContext';
	import { iconProps } from "@lib/utils"

export let CONTEXT;
export let PLACE;

let reList = false
function reinitList() {reList = !reList}

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
			reinitList();
	})
}

$: VIEWER_LINK = PLACE.volumes.length > 0 ? `/viewer/${PLACE.slug}/` : '';

</script>

<IconContext values={iconProps} >
<PlaceBreadcrumbsSelect bind:PLACE {update} />
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
		<div style="display:flex; justify-content:space-between; align-items:center;">
			<h4>Sub-locales</h4>
			<label title="Show all sub-locales, even those without maps">show all<input type='checkbox' bind:checked={showAllSublocales} /></label>
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
		{#key reList}
		<Maps {CONTEXT} PLACE_SLUG={PLACE.slug} PLACE_INCLUSIVE={true} />
		{/key}
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
  }
</style>
