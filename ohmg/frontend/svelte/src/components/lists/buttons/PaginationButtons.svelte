<script>
    import CaretDoubleLeft from 'phosphor-svelte/lib/CaretDoubleLeft'
    import CaretDoubleRight from 'phosphor-svelte/lib/CaretDoubleRight'

    export let loading = false;
    export let currentOffset = 0;
    export let apiLimit = 100;
    export let total = 0;
    export let getPrevious = () => {}
    export let getNext = () => {}
</script>

<div class="btn-container">
    <button disabled={currentOffset < apiLimit || loading} on:click={getPrevious}>
        <CaretDoubleLeft />
        newer
    </button>
    <span>{currentOffset} - {currentOffset + apiLimit < total ? currentOffset + apiLimit : total} ({total})</span>
    <button disabled={currentOffset + apiLimit >= total || loading} on:click={getNext}>
        older
        <CaretDoubleRight />
    </button>
</div>

<style>
    button {
        display:flex;
        align-items:center;
    }
    .btn-container {
        display:flex;
        align-items:center;
    }
</style>