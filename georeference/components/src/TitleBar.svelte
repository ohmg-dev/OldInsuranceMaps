<script>
    export let TITLE;
    export let BOTTOM_LINKS;
    export let SIDE_LINKS;
</script>

<div class="title-bar">
    <div>
        <h1>{ TITLE }</h1>
        {#if BOTTOM_LINKS && BOTTOM_LINKS.length > 0}
        <p>
        {#each BOTTOM_LINKS as link, n}
            {#if n != 0}&nbsp;&bullet;&nbsp;{/if}
            {#if link.url}<a href={link.url} title={link.alt ? link.alt : link.display}>{link.display}</a>{:else}{link.display}{/if}
        {/each}
        </p>
        {/if}
    </div>
    <div class="link-box">
        {#each SIDE_LINKS as link}
            <a href={link.url} title={link.alt ? link.alt : link.display} target={link.external ? "_blank" : "_self"}>{link.display} {#if link.external}<i class="fa fa-external-link"></i>{:else}&rarr;{/if}</a>
        {/each}
    </div>
</div>

<style>
    .title-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 10px 0px 15px 0px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgb(149, 149, 149);
    }

    .title-bar div {
        display: flex;
        flex-direction: column;
    }

    .title-bar div h1 {
        margin: 10px 0px;
        font-size: 2em;
    }

    .title-bar div.link-box {
        display: flex;
        flex-direction: column;
        align-items: end;
        background: #e6e6e6;
        padding: 10px;
        margin: 10px;
        box-shadow: gray 0px 0px 5px;
        border-radius: 4px;
    }
</style>