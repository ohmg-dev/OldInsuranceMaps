<script>
    import Icon from 'svelte-icons-pack/Icon.svelte';
    import FiInfo from 'svelte-icons-pack/fi/FiInfo';

    import Modal, {getModal} from '../Modal.svelte';

    export let modalName;
</script>

<button on:click={()=>getModal(modalName).open()}>
    <Icon src={FiInfo} />
</button>

<style>
    button {
        background: none;
        border: none;
        color:#2c689c;
        vertical-align: middle;
        font-size: 1.5em;
        display: flex;
        align-items: center;
    }
    button:hover {
        color:#123B4F;
    }
</style>