<script>
    import ArrowSquareOut from "phosphor-svelte/lib/ArrowSquareOut";

    export let href;
    export let external = false;
    export let title = "";
</script>

{#if external}
<a href={href} target="_blank" title={title}>
    <slot></slot> <ArrowSquareOut />
</a>
{:else}
<a href={href} title={title}>
    <slot></slot>
</a>
{/if}