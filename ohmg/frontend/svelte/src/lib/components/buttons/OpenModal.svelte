<script>
    import Question from 'phosphor-svelte/lib/Question';
    import Lock from 'phosphor-svelte/lib/Lock';

    import {getModal} from '../modals/Base.svelte';

    export let modalName;
    export let icon = "question";
</script>

<button on:click={()=>getModal(modalName).open()} title="More info">
    {#if icon == "question"}
    <Question weight={'regular'}/>
    {:else if icon == "lock"}
    <Lock weight={'regular'}/>
    {/if}
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