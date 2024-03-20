<script>
    import Modal from "@components/base/Modal.svelte"
    import SingleLayerViewer from "../SingleLayerViewer.svelte"

    export let id;
    export let LAYER_URL;
    export let EXTENT;
    export let MAPBOX_API_KEY;
    export let TITILER_HOST;
    
</script>

<Modal id={id}>
	<SingleLayerViewer LAYER_URL={LAYER_URL} EXTENT={EXTENT} MAPBOX_API_KEY={MAPBOX_API_KEY} TITILER_HOST={TITILER_HOST} />
</Modal>