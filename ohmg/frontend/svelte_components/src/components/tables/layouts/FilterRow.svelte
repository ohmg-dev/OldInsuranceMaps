<script>
    import { slide } from 'svelte/transition';

    import LimitSelect from '../widgets/LimitSelect.svelte';

    export let currentLimit = "25";
    export let showFilters = false;
</script>

{#if showFilters}
<div transition:slide class="level" style="margin:.5em 0;">
    <div class="filter-level level-left">
        <slot />
    </div>
    <div class="filter-level level-right">
        <LimitSelect bind:value={currentLimit} />
    </div>
</div>
{/if}