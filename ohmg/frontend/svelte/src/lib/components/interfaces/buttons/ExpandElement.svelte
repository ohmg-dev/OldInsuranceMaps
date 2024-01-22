<script>
    // import '@src/css/map-panel.css';

    import IconButton from "@components/base/IconButton.svelte"

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

<IconButton style="tool-ui" title={ffs ? "Reduce" : "Expand"} action={() => {handleFfs(elementId)}}>
    {#if ffs}
    <ArrowsInSimple />
    {:else}
    <ArrowsOutSimple />
    {/if}
</IconButton>

<style>
:global(.ffs) {
    position: fixed !important;
    width: 100%;
    top: 60px;
    height: calc(100vh - 60px) !important;
    left: 0;
}
</style>