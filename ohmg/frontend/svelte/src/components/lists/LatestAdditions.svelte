<script>
    import LoadingEllipsis from "../base/LoadingEllipsis.svelte";
	import Link from '@components/base/Link.svelte';

	export let CONTEXT;

	let loadingItems = false;
	let latestItems = [];

	function getInitialResults() {
		loadingItems = true;
		fetch(CONTEXT.urls.get_maps+"?limit=6&sort=load_date", {
			headers: CONTEXT.ohmg_api_headers,
		})
		.then(response => response.json())
		.then(result => {
			latestItems = result;
			loadingItems = false;
		});
	}
	getInitialResults()
</script>

<div>
	{#if loadingItems}
	<LoadingEllipsis />
	{:else}
	{#each latestItems as v}
	<div class="list-item-container">
		<Link href={v.urls.summary} title="{v.title} summary">{v.title} ({v.sheet_ct})</Link> &mdash; 
		<Link href="{v.loaded_by.profile_url}">{v.loaded_by.username}</Link> &mdash; 
		{v.load_date}
	</div>
	{/each}
	{/if}
</div>
<style>
.list-item-container {
	padding: 3px;
}

@media only screen and (max-width: 480px) {
	.list-item-container {
		flex-direction: column;
	}
}
</style>
