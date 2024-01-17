<script>
    import '@src/css/map-panel.css';

    import CornersOut from "phosphor-svelte/lib/CornersOut";

    export let action;
</script>

<button class="control-btn tool-ui" title="Go to full extent" on:click={action}>
    <CornersOut />
</button>