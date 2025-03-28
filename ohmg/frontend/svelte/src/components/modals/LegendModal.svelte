<script>
    import Modal from './BaseModal.svelte';

    export let id;
    export let legendUrl;
    export let legendAlt;
</script>

<Modal id={id} full={true}>
    <img src={legendUrl} alt={legendAlt} />
</Modal>