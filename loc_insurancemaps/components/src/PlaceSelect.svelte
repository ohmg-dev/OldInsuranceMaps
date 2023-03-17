<script>
export let VOLUME;

let editing = false;

let breadCrumbs = []
$: {
	if (VOLUME.locale) {
		fetch("/place-lookup/"+VOLUME.locale.slug, {
			// method: 'POST',
			// headers: {
			// 'Content-Type': 'application/json;charset=utf-8',
			// 'X-CSRFToken': CSRFTOKEN,
			// },
			// body: JSON.stringify({"multiMask": multiMask}),
		}).then(response => response.json())
			.then(result => {
				breadCrumbs = result.breadcrumbs
		})
	}
}

</script>

<div style="font-style:italic;">
	{#if editing}
		<p>editing</p>
	{:else}
		{#if VOLUME.locale}
		{#each breadCrumbs as bc, n}
		<a href="/{bc.slug}">{bc.name}</a>{#if n != breadCrumbs.length-1}&nbsp;&rarr;&nbsp;{/if}
		{/each}
		{:else}
		<p>No locale defined.</p>
		{/if}
	{/if}
	<!-- <button on:click={() => {editing=!editing}}>{editing ? "Save" : "Change"}</button> -->
</div>

<style>

</style>
