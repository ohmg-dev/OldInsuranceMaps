<script>

	import ArrowRight from "phosphor-svelte/lib/ArrowRight";

    export let PLACE;
    export let update;
    
</script>

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

<style>
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

    @media (max-width: 768px) {

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