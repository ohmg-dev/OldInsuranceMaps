<script>
    import SVGButton from "@components/base/SVGButton.svelte";
    import ArrowSquareOut from "phosphor-svelte/lib/ArrowSquareOut";

    export let TITLE;
    export let IMG_URL = null;
    export let ICON_LINKS = [];
    export let VIEWER_LINK = null;
</script>

<div class="title-bar">
    <div style="display:flex; flex-direction:row; justify-content:left; align-items:center;">
        {#if IMG_URL}
        <img height="40px" style="border-radius:5px; margin-right:10px;" src="{IMG_URL}" alt="{TITLE}" />
        {/if}
        <h1 style="margin-bottom:0px;">{ TITLE }</h1>
    </div>
    {#if ICON_LINKS.length > 0}
    <div class="icon-box">
        {#each ICON_LINKS as link}
            {#if link.visible}
            <SVGButton icon={link.iconClass} title={link.alt} size="md" action={() => {location.href = link.url}} disabled={!link.enabled} />
            {/if}
        {/each}
    </div>
    {/if}
    {#if VIEWER_LINK}
    <div class="icon-box">
        <SVGButton icon="camera" title="Open in main viewer" size="md" action={() => {window.open(VIEWER_LINK,'_blank');}}></SVGButton>
    </div>
    {/if}
</div>

<style>
    .title-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 7px 0px;
        border-bottom: 1px solid rgb(149, 149, 149);
    }

    .title-bar div {
        display: flex;
        flex-direction: column;
    }

    .title-bar div h1 {
        margin: 0px;
    }

    .title-bar div.icon-box {
        display: flex;
        flex-direction: row;
        align-items: center;
        background: #e6e6e6;
        padding: 2px;
        box-shadow: gray 0px 0px 5px;
        border-radius: 4px;
    }
</style>