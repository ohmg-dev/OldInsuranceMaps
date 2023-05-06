<script>
export let PLACE;

import TitleBar from './TitleBar.svelte';

function update(place_slug) {
	fetch(`/${place_slug}?f=json`, {
	}).then(response => response.json())
		.then(result => {
			PLACE = result;
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

</script>
<TitleBar TITLE={PLACE.display_name} SIDE_LINKS={sideLinks} ICON_LINKS={[]}/>
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
</style>
