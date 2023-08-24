<script>
    import Icon from 'svelte-icons-pack';
    import FiChevronsLeft from 'svelte-icons-pack/fi/FiChevronsLeft'
    import FiChevronsRight from 'svelte-icons-pack/fi/FiChevronsRight'

    export let loading = false;
    export let currentOffset = 0;
    export let apiLimit = 100;
    export let total = 0;
    export let getPrevious = () => {}
    export let getNext = () => {}
</script>

<div class="btn-container">
    <button disabled={currentOffset < apiLimit || loading} on:click={getPrevious}>
        <Icon src={FiChevronsLeft} />
        newer
    </button>
    <span>{currentOffset} - {currentOffset + apiLimit < total ? currentOffset + apiLimit : total} ({total})</span>
    <button disabled={currentOffset + apiLimit >= total || loading} on:click={getNext}>
        older
        <Icon src={FiChevronsRight} />
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