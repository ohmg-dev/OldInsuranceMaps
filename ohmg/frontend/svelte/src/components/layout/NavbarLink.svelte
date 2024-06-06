<script>
    import ArrowSquareOut from "phosphor-svelte/lib/ArrowSquareOut";

    export let title;
    export let href;
    export let isExternal = false;
</script>

{#if isExternal}
<a class="navbar-item" href={href}>
    <span style="margin-right:5px;">{title}</span><ArrowSquareOut />
</a>
{:else}
<a class="navbar-item" href={href} target="_blank">
    {title}
</a>
{/if}