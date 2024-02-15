<script>
    import Modal from '@components/base/Modal.svelte';

    export let id;
    export let legendUrl;
    export let legendAlt;
</script>

<Modal id={id} full={true}>
    <img src={legendUrl} alt={legendAlt} />
</Modal>