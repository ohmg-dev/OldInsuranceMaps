<script>
    import '@src/css/map-panel.css';

    import ArrowsInSimple from "phosphor-svelte/lib/ArrowsInSimple";
    import ArrowsOutSimple from "phosphor-svelte/lib/ArrowsOutSimple";

    export let elementId;
    export let map = null;

    let ffs = false;
    function handleFfs(elementId) {
        ffs = !ffs
        document.getElementById(elementId).classList.toggle('ffs');
        map && map.updateSize();
    }
</script>

<button class="control-btn tool-ui" title={ffs ? "Reduce" : "Expand"} on:click={() => {handleFfs(elementId)}}>
    {#if ffs}
    <ArrowsInSimple />
    {:else}
    <ArrowsOutSimple />
    {/if}
</button>

<style>
:global(.ffs) {
    position: fixed !important;
    width: 100%;
    top: 60px;
    height: calc(100vh - 60px) !important;
    left: 0;
}
</style>