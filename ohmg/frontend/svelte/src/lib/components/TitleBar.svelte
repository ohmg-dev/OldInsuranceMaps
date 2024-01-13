<script>
    import IconContext from 'phosphor-svelte/lib/IconContext';
    import { iconProps } from "../../js/utils"
    import ArrowSquareOut from "phosphor-svelte/lib/ArrowSquareOut";

    export let TITLE;
    export let IMG_URL = null;
    export let SIDE_LINKS = [];
    export let ICON_LINKS = [];
</script>

<IconContext values={iconProps}>
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
        <a href="{link.url}" title={link.alt} name={link.alt} style="{link.enabled ? '' : 'cursor:default; pointer-events:none;'}">
            <i class="i-{link.iconClass} i-{link.iconClass}-sm" style="display:block; {link.enabled ? '' : 'background:grey;'}"></i>
        </a>
        {/if}
        {/each}
    </div>
    {/if}
    {#if SIDE_LINKS.length > 0}
    <div class="link-box">
        {#each SIDE_LINKS as link}
            <a href={link.url} title={link.alt ? link.alt : link.display} target={link.external ? "_blank" : "_self"}>{link.display} {#if link.external}<ArrowSquareOut />{:else}&rarr;{/if}</a>
        {/each}
    </div>
    {/if}
</div>
</IconContext>

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

    .title-bar div.link-box {
        display: flex;
        flex-direction: column;
        align-items: end;
        background: #e6e6e6;
        padding: 10px;
        box-shadow: gray 0px 0px 5px;
        border-radius: 4px;
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
    .title-bar div.icon-box i {
        display: block;
        background: #2c689c;
    }
    .title-bar div.icon-box i:hover {
        background: #1b4060;
    }
</style>