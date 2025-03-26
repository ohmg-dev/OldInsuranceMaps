<script>
    import ArrowRight from "phosphor-svelte/lib/ArrowRight";

	import Link from '@/base/Link.svelte';

    export let LOCALE;
    export let MAP;

    let currentIdentifier = MAP.identifier
	function goToItem() {
		window.location = "/map/" + currentIdentifier
	}
	let currentDoc = "---";
	function goToDocument() {
		window.location = "/document/" + currentDoc
	}
</script>


<section>
    <div style="flex-wrap:wrap">
        <i class="fancy fancy-xs i-pin" style="margin-top: -5px;"></i>
        {#each LOCALE.breadcrumbs as bc, n}
        <Link href="/{bc.slug}">{bc.name}</Link>
        {#if n != LOCALE.breadcrumbs.length-1}
        <span class="arrow">
            <ArrowRight size={12} />
        </span>
        {/if}
        {/each}
        <span class="arrow hideable">
            <ArrowRight size={12} />
        </span>
    </div>
    <div>
        <i class="fancy fancy-xs i-volume"></i>
        <select bind:value={currentIdentifier} on:change={goToItem}>
            {#each LOCALE.maps as m}
            <option value={m.identifier}>{m.title}</option>
            {/each}
        </select>
        <span class="arrow hideable">
            <ArrowRight size={12} />
        </span>
    </div>
    <div>
        <i class="fancy fancy-xs i-document"></i>
        <select bind:value={currentDoc} on:change={goToDocument}>
            <option value="---">document</option>
            {#each MAP.documents as d}
            <option value={d.id}>{d.nickname}</option>
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

    span.arrow {
        margin: 0px 2px;
    }

    i {
        background-color: #2c689c;
        margin-right: 2px;
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