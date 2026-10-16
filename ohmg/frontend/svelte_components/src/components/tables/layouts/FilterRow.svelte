<script>
    import { slide } from 'svelte/transition';

    import LimitSelect from '../widgets/LimitSelect.svelte';

    export let currentLimit = "25";
    export let showFilters = false;
</script>

{#if showFilters}
<div transition:slide class="filter-row">
    <div class="filter-row-left">
        <slot />
    </div>
    <div class="filter-row-right">
        <LimitSelect bind:value={currentLimit} />
    </div>
</div>
{/if}

<style>
    .filter-row {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        gap: .5em;
        margin:.5em 0;
    }
    .filter-row-left, .filter-row-right {
        display: flex;
        gap: .5em;
    }
    @media (min-width: 769px) {
        .filter-row-left {
            max-width: 90%;
        }
    }
    @media screen and (max-width: 768px) {
        .filter-row-left {
            flex-direction: row;
            flex-wrap: wrap;
            width: 100%;
        }
        :global(.filter-row-left > *) {
            max-width: calc(50% - .25em) !important;
        }
        :global(.date-filter),
        :global(button.date-field) {
            width: 100% !important;
        }
    }
</style>