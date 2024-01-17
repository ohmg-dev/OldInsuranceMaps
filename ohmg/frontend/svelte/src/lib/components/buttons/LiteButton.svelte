<script>
    import Wrench from 'phosphor-svelte/lib/Wrench';

    import {getModal} from '../modals/Base.svelte';

    export let action;
    export let title;
</script>

<button on:click={action} title={title}>
    <Wrench weight={'regular'}/>
</button>

<style>
    button {
        background: none;
        border: none;
        color:#2c689c;
        vertical-align: middle;
        font-size: 1.7em;
        display: flex;
        align-items: center;
    }
    button:hover {
        color:#123B4F;
    }
</style>