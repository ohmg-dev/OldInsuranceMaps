<script>
    import Modal from "./Base.svelte";
    import SingleDocumentViewer from "../interfaces/SingleDocumentViewer.svelte";

    export let id;
    export let LAYER_URL;
    export let IMAGE_SIZE;
    export let reinit = [{}];
</script>

<Modal id={id} full={true}>
    {#each reinit as key (key)}
	<SingleDocumentViewer LAYER_URL={LAYER_URL} IMAGE_SIZE={IMAGE_SIZE} />
    {/each}
</Modal>