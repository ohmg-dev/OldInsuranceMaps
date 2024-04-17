<script>

    import X from "phosphor-svelte/lib/X";
    import Check from "phosphor-svelte/lib/Check";
    import CropIcon from "phosphor-svelte/lib/Crop";
    import Trash from "phosphor-svelte/lib/Trash";

    import Modal from "@components/base/Modal.svelte"
    export let id;
</script>

<Modal id={id}>
	<h3>MultiMask</h3>
	<p>The <strong>MultiMask</strong> is a mechanism for trimming the margins from every layer in a way that guarantees a seamless mosaic across this item's content.<p>
	<h4>How to create a MultiMask</h4>
	<ul>
		<li>Use <CropIcon /> to start a mask for a particular layer.</li>
		<li>Use <Trash /> to delete an existing mask.</li>
		<li>Use <Check /> to save your work (do this often!).</li>
		<li>Use <X /> to discard all changes since the last save.</li>
	</ul>
	<h4>Important Notes</h4>
	<ul>
		<li>You must be signed in to save your work, so don't get started before you are signed in!</li>
		<li>The vertices of every adjacent mask should be snapped together</li>
		<li>You can drag existing vertices to snap them to others, but this is sometimes "sticky" and takes a couple of tries.</li>
		<li>If a mosaic is generated for this item, only layers that have been masked will be included in the mosaic.</li>
	</ul>
</Modal>