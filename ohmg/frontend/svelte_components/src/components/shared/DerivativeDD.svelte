<script lang="ts">
    import CopyableText from "./buttons/CopyableText.svelte";
    import Link from "../base/Link.svelte";

    export let linkLabel: string | undefined = undefined;
    export let linkTitle: string | undefined = undefined;
    export let linkUrl: string | undefined = undefined;
    export let linkType: string = "default";
    export let naMessage: string = "not available";

    const useLabel = linkLabel ? linkLabel : linkUrl;
    const useTitle = linkTitle ? linkLabel : linkUrl;
</script>

<dd>
    {#if linkUrl}
        <!-- <span style="font-family:'Fira Code' !important;"> -->
        {#if linkType == "copytext"}
            <CopyableText text={linkUrl} />
        {:else if linkType == "download"}
            <Link
                href={linkUrl}
                title={useTitle}
                download={true}>
                    {useLabel}
            </Link>
        {:else if linkType == "external"}
            <Link
                href={linkUrl}
                title={useTitle}
                external={true}>
                    {useLabel}
            </Link>
        {/if}
        <!-- </span> -->
    {:else}
        <span class="na-message">{naMessage}</span>
    {/if}
</dd>

<style>
    dd {
        padding: .25em .5em .25em 1em;
    }
    .na-message {
        font-size: .8em;
    }
    .na-message::before {
        content: "-- "
    }
</style>