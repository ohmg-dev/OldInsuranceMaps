<script>
export let PLACE;

import TitleBar from "../../../georeference/components/src/TitleBar.svelte";
console.log(PLACE)
</script>
<TitleBar TITLE={PLACE.display_name} SIDE_LINKS={[]} ICON_LINKS={[]}/>
<div style="font-style:italic;">
	{#each PLACE.breadcrumbs as bc, n}
	<a href="/{bc.slug}">{bc.name}</a>{#if n != PLACE.breadcrumbs.length-1}&nbsp;&rarr;&nbsp;{/if}
	{/each}
</div>
<div style="display:flex;">
	<div style="width:50%">
		<h2>Locales</h2>
		{#if PLACE.descendants.length > 0}
		<ul style="padding-left:20px">
			{#each PLACE.descendants as d}
			<li><a href="/{d.slug}">{d.display_name}</a></li>
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

</style>
