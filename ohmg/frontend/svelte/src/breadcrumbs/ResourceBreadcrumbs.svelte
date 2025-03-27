<script>
    import ArrowRight from "phosphor-svelte/lib/ArrowRight";

    import Link from '@/base/Link.svelte';

    export let LOCALE;
    export let MAP;
    export let RESOURCE

    let currentDoc = RESOURCE.type == "document" ? RESOURCE.id : RESOURCE.document.id;
    function goToDocument() {
        window.location = "/document/" + currentDoc
    }
    let currentReg;
    if (RESOURCE.type == "document") {
        currentReg = "---";
    } else if (RESOURCE.type == "region") {
        currentReg = RESOURCE.id;
    } else if (RESOURCE.type == "layer") {
        currentReg = RESOURCE.region.id;
    }
    function goToRegion() {
        window.location = "/region/" + currentReg
    }
</script>

<section class="breadcrumbs">
    <div style="flex-wrap:wrap">
        <i class="fancy fancy-xs i-pin" style="margin-top: -5px;"></i>
        {#each LOCALE.breadcrumbs as bc, n}
        <Link href="/{bc.slug}">{bc.name}</Link>{#if n != LOCALE.breadcrumbs.length-1}<ArrowRight size={12} />{/if}
        {/each}
        <span class="arrow hideable">
            <ArrowRight size={12} />
        </span>
    </div>
    <div>
        <Link href={`/map/${MAP.identifier}`}>
            <span style="display:flex;">
                <i class="fancy fancy-xs i-volume"></i>
                <span>{MAP.title}</span>
            </span>
        </Link>
        <span class="arrow hideable">
            <ArrowRight size={12} />
        </span>
    </div>
    <div>
        <Link href={`/document/${currentDoc}`}>
            <span style="display:flex;">
                <i class="fancy fancy-xs i-document"></i>
            </span>
        </Link>
        <select class="item-select" bind:value={currentDoc} on:change={goToDocument}>
            <option value="---" disabled>document</option>
            {#each MAP.documents as d}
            <option value={d.id}>{d.nickname}</option>
            {/each}
        </select>
        <span class="arrow hideable">
            <ArrowRight size={12} />
        </span>
    </div>
    <div>
        <i class="fancy fancy-xs i-layer {RESOURCE.regions.length == 0 ? 'disabled':''}" ></i>
        <select disabled={RESOURCE.regions.length == 0} class="item-select" bind:value={currentReg} on:change={goToRegion}>
            <option value="---" disabled>region/layer</option>
            {#each RESOURCE.regions as r}
            <option value={r.id}>{r.nickname}</option>
            {/each}
        </select>
    </div>
</section>

<style>

    section {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        padding: 5px 0px;
        font-size: .95em;
        border-bottom: none;
    }

    section > div {
        display: flex;
        align-items: center;
    }

    select {
        margin-right: 3px;
        color: #2c689c;
        cursor: pointer;
        padding: 5px 0px 4px 5px;
    }

    select:disabled {
        color: #717070;
        cursor: default;
    }

    span.arrow {
        margin: 0px 2px;
    }

    i {
        background-color: #2c689c;
        margin-right: 2px;
    }

    i.disabled {
        background-color: #717070;
    }

    @media (max-width: 768px) {

        section {
            flex-direction: column;
        }
        select {
            margin-bottom: 2px;
            width: 100%;
        }
        section > div {
            width: 100%;
        }
        .hideable {
            display: none;
        }
    }
</style>