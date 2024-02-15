<script>
    // import '@src/css/map-panel.css';

    import IconButton from "@components/base/IconButton.svelte"

    import ArrowsInSimple from "phosphor-svelte/lib/ArrowsInSimple";
    import ArrowsOutSimple from "phosphor-svelte/lib/ArrowsOutSimple";

    export let elementId;
    export let maps = [];

    let ffs = false;
    function handleFfs(elementId) {
        ffs = !ffs
        document.getElementById(elementId).classList.toggle('ffs');
        maps.forEach((map) => map && map.updateSize());
    }

    function handleKeydown(e) {
        // only allow these shortcuts if the maps have focus,
        // so shortcuts aren't activated while typing a note.
        if (document.activeElement.id == "") {
            switch(e.key) {
            case "Escape":
                handleFfs('map-container')
                break;
            }
        }
    }
</script>

<svelte:window on:keydown={handleKeydown} />
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