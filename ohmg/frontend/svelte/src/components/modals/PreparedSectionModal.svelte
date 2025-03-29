<script>
    import Modal from "./BaseModal.svelte"
    export let id;
</script>

<Modal id={id}>
	<h3>Prepared</h3>
	<p>Content in the <strong>Prepared</strong> section is ready to be georeferenced. You can also decide here if a particular document should be moved to the <strong>Non-map Content</strong> section, for example if it is a title page or text index (this designation can be easily reversed).</p>
</Modal>