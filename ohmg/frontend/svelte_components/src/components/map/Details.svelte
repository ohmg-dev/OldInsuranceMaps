<script>
    import Link from "../base/Link.svelte";

    export let MAP;
    export let SESSION_SUMMARY;
</script>

<div style="padding: .5em 0;">
    <h4 class="dl-title">Record</h4>
    <dl>
        <dt>Title</dt>
        <dd>Sanborn Map of {MAP.title}</dd>
        <dt>Year</dt>
        <dd>{MAP.year}</dd>
        <dt>Locale</dt>
        <dd><Link href="/{MAP.locale.slug}">{MAP.locale.display_name}</Link></dd>
        <dt>Source</dt>
        <dd><Link href="https://loc.gov/item/{MAP.identifier}" external={true}
            >loc.gov/item/{MAP.identifier}</Link></dd>
        <dt>Credit line</dt>
        <dd>Library of Congress, Geography and Map Division, Sanborn Maps Collection.</dd>
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