<script>
    import Question from 'phosphor-svelte/lib/Question';

    import {getModal} from '../Modal.svelte';

    export let modalName;
</script>

<button on:click={()=>getModal(modalName).open()} title="More info">
    <Question weight={'regular'}/>
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