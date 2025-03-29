<script>
    import Modal from "./BaseModal.svelte";
    import HowToUseXyz from "../overviews/sections/HowToUseXYZ.svelte";

    export let id;
</script>

<Modal id={id}>
	<h3>Download & Web Services</h3>
    <HowToUseXyz />
</Modal>