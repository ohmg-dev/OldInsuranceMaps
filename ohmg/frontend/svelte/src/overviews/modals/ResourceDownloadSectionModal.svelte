<script>
    import Modal from "@/base/Modal.svelte";
    import HowToUseXyz from "../sections/HowToUseXYZ.svelte";

    export let id;
</script>

<Modal id={id}>
	<h3>Download & Web Services</h3>
    <HowToUseXyz />
</Modal>