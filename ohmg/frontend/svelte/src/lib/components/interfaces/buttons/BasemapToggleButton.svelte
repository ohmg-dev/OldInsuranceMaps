<script>
    import IconButton from '@components/base/IconButton.svelte'
    import '@src/css/map-panel.css';

    import MapTrifold from "phosphor-svelte/lib/MapTrifold";

    export let action;
</script>

<IconButton style="tool-ui" title="Change basemap" action={action}>
    <MapTrifold />
</IconButton>