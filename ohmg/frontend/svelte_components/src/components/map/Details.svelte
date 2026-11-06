<script>
    import Link from "../base/Link.svelte";
    import SvelteMarkdown from 'svelte-markdown';

    export let MAP;
    export let SESSION_SUMMARY;
</script>

<div style="padding: .5em 0;">
    <h4 class="dl-title">Record</h4>
    <dl>
        <dt>Title</dt>
        <dd>{MAP.title}</dd>
        <dt>Year</dt>
        <dd>{MAP.year}</dd>
        <dt>Publisher</dt>
        <dd>{MAP.publisher ?? "---"}</dd>
        <dt>Locale</dt>
        <dd><Link href="/{MAP.locale.slug}">{MAP.locale.display_name}</Link></dd>
        <dt>Source</dt>
        <dd>
            {#if MAP.source}
            <Link href="{MAP.source.url}" external={true}>{MAP.source.name}</Link>
                {#if MAP.source_item_url}
                <br/>Item url: <Link href="{MAP.source_item_url}" external={true}>{MAP.source_item_url}</Link>
                {/if}
            {:else}
            ---
            {/if}
        </dd>
        {#if MAP.source && MAP.source.note}
        <dt>Source note</dt>
        <dd>
        <SvelteMarkdown source={MAP.source.note}/>
        </dd>
        {/if}
        {#if MAP.external_links.length > 0}
        <dt>See also...</dt>
        <dd>
            <ul>
                {#each MAP.external_links as link}
                <li>{link.title}: <Link href="{link.url}" external={true}>{link.url}</Link></li>
                {/each}
            </ul>
        </dd>
        {/if}
    </dl>
    {#if MAP.progress.loaded_pages}
    <hr style="border-top: dashed grey 1px; background:none; margin: 1em 0;">
    <p style="margin:0;"><em>added to OldInsuranceMaps.net by <Link href={MAP.loaded_by.profile}>{MAP.loaded_by.name}</Link>,
        {MAP.loaded_by.date};
        {SESSION_SUMMARY.prep_ct} document{#if SESSION_SUMMARY.prep_ct != 1}s{/if} prepared{#if SESSION_SUMMARY.prep_ct > 0}&nbsp;by
            {#each SESSION_SUMMARY.prep_contributors as c, n}<Link href="/profile/{c.name}">{c.name}</Link> ({c.ct}){#if n != SESSION_SUMMARY.prep_contributors.length - 1},
                {/if}{/each}{/if};
        {SESSION_SUMMARY.georef_ct} georeferencing session{#if SESSION_SUMMARY.georef_ct != 1}s{/if}{#if SESSION_SUMMARY.georef_ct > 0}&nbsp;by
            {#each SESSION_SUMMARY.georef_contributors as c, n}<Link href="/profile/{c.name}">{c.name}</Link> ({c.ct}){#if n != SESSION_SUMMARY.georef_contributors.length - 1},
                {/if}{/each}{/if}
    </em>
    </p>
    {/if}
</div>
<style>
    h4.dl-title {
        margin: 0;
        padding: .4em;
        color: white;
        background-color: var(--bulma-scheme-main);
    }
    dl {
        background-color: #ffffff;
    }
    dt, dd {
        padding-top: .25em;
        padding-bottom: .25em;
    }
    dt {
        font-weight: 700;
        font-size: .85em;
        background-color: #f6f6f6;
        padding-left: .5em;
    }
    dd {
        padding-left: 1em;
    }
</style>