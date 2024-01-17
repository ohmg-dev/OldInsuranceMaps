<script>
    import '@src/css/map-panel.css';

    import Modal, {getModal}  from "@components/modals/Base.svelte";
    import Article from "phosphor-svelte/lib/Article";

    export let id;
</script>

<button class="control-btn tool-ui" title="Show legend" on:click={getModal(id).open()}>
    <Article />
</button>