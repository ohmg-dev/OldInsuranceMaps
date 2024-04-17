<script>
    import Modal from "@components/base/Modal.svelte"
    export let id;
</script>

<Modal id={id}>
	<h3>Georeferencing Overview</h3>
	<p>The <strong>Georeferencing Overview</strong> provides a per-document summary and access point to the entire georeferencing process for this item's content. As documents are processed, they will move through the sections from top to bottom.</p>
</Modal>