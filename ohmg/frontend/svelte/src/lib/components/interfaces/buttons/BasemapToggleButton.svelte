<script>
    import '@src/css/map-panel.css';

    import MapTrifold from "phosphor-svelte/lib/MapTrifold";

    export let action;
</script>

<button class="control-btn tool-ui" title="Change basemap" on:click={action}>
    <MapTrifold />
</button>