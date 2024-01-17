<script>
    import Modal from '@components/modals/Base.svelte';

    export let id;
    export let legendUrl;
    export let legendAlt;
</script>

<Modal id={id}>
    <img src={legendUrl} alt={legendAlt} />
</Modal>