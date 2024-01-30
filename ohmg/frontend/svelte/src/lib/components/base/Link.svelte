<script>
    import ArrowSquareOut from "phosphor-svelte/lib/ArrowSquareOut";

    export let href;
    export let external = false;
    export let title = "";
    export let classes = [];
    export let download = null;

    const classStr = classes.join(" ")

</script>

{#if external}
<span>
    <a href={href} class={classStr} target="_blank" title={title} {download}>
        <slot></slot>
        <ArrowSquareOut />
    </a>
</span>
{:else}
<a href={href} class={classStr} title={title} {download}>
    <slot></slot>
</a>
{/if}
    
<style>
    span {
        display: inline-flex;
    }
    span > a {
        margin-right: 2px;
    }
</style>