<script>
    import '../../css/shared.css';
    import SvelteMarkdown from 'svelte-markdown'

    import Link from './Link.svelte'

    export let source = '*add your markdown here*';
    export let isHtml = false;
    export let MAKE_TOC = true

    function slugify(str) {
        return str
            .toLowerCase()
            .trim()
            .replace(/[^\w\s-]/g, "")
            .replace(/[\s_-]+/g, "-")
            .replace(/^-+|-+$/g, "");
    }

    $: headings = []
    function handleParsed(event) {
        event.detail.tokens.forEach(element => {
            if (element.type === "heading") {
                headings = [...headings, element]
            }
        });
    }

</script>

<main>
    {#if isHtml}
        {@html source}
    {:else}
        <div class="content">
            <div>
                <SvelteMarkdown {source} on:parsed={handleParsed}/>
            </div>
            {#if MAKE_TOC}
            <div id="side-panel">
                <div id="toc">
                    <ul>
                        {#each headings as heading}
                            <li><Link href="#{slugify(heading.text)}">{heading.text}</Link></li>
                        {/each}
                    </ul>
                </div>
            </div>
            {/if}
        </div>
    {/if}
</main>

<style>

    main {
        display: flex;
        flex-direction: column;
    }

    .content {
        display: flex;
        flex-direction: row;
    }

    #side-panel {
        min-width: 300px;
        padding-top: 10px;
        padding-left: 15px;
    }

    #toc > ul {
        padding: 0px;
    }
    #toc > ul > li {
        list-style: none;
    }

    @media (max-width: 760px) {
        .content {
            display: flex;
            flex-direction: column-reverse;
        }
        #side-panel {
            padding-left: 0px;
        }
    }

</style>