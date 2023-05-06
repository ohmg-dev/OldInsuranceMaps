<script>
export let ITEM_API_URL;
export let OHMG_API_KEY;

let loadingItems = false;
let latestItems = [];

function getInitialResults() {
	loadingItems = true;
	fetch(ITEM_API_URL+"?limit=10&sort=load_date", {
		headers: {
			'X-API-Key': OHMG_API_KEY,
		}
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
	<div style="height: 300px; overflow-y:auto; border:1px solid grey; border-radius:4px; background:white;">
		{#if loadingItems}
		<div class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
		{:else}
		{#each latestItems as v}
		<div class="list-item-container">
			<a href={v.urls.summary} alt="Go to item summary" title="Go to summary">{v.title} ({v.sheet_ct})</a>
			<span>loaded by <a href="{v.loaded_by.profile_url}">{v.loaded_by.username}</a> &mdash; {v.load_date}</span>
		</div>
		{/each}
		{/if}
	</div>
</div>
<style>
.list-item-container {
	display:flex;
	justify-content: space-between;
	padding: 5px;
}

@media only screen and (max-width: 480px) {
	.list-item-container {
		flex-direction: column;
	}
}
</style>
