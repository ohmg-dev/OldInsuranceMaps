<script>
    import Icon from 'svelte-icons-pack/Icon.svelte';
    import FiChevronsRight from 'svelte-icons-pack/fi/FiChevronsRight';
    import FiChevronsDown from 'svelte-icons-pack/fi/FiChevronsDown';

    export let down;
    export let size;

    let em = "1em";
    if (size == "lg") {
        em = "1.5em";
    } else if (size == "md") {
        em = "1.3em";
    }
</script>
{#if down}
<Icon src={FiChevronsDown} size={em} />
{:else}
<Icon src={FiChevronsRight} size={em} />
{/if}
