<script>
    import Faders from "phosphor-svelte/lib/Faders";

    export let showFilters = false;
</script>

<button
    class={`button is-link ${showFilters ? '' : 'is-light'}`}
    style="max-height: 42px;"
    title={showFilters ? 'Hide filters' : 'Show filters'}
        on:click={() => {
        showFilters = !showFilters;
        }}
>
    <span style="margin-right: .25em;">
        {showFilters ? 'Filters' : 'Filters'}
    </span>
    <Faders />
</button>