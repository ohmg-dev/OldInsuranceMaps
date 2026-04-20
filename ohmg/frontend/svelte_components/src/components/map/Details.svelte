<script>
    import Link from "../base/Link.svelte";

    export let MAP;
    export let SESSION_SUMMARY;
</script>

<div class="fixed-grid has-12-cols has-1-cols-mobile">
<div class="grid">
<div class="cell is-col-span-5">
    <h3>Record</h3>
    <table>
    <tbody>
        <tr>
        <td>Title</td>
        <td>Sanborn Map of {MAP.title}</td>
        </tr>
        <tr>
        <td>Year</td>
        <td>{MAP.year}</td>
        </tr>
        <tr>
        <td>Locale</td>
        <td><Link href="/{MAP.locale.slug}">{MAP.locale.display_name}</Link></td>
        </tr>
        <tr>
        <td>Source</td>
        <td
            ><Link href="https://loc.gov/item/{MAP.identifier}" external={true}
            >loc.gov/item/{MAP.identifier}</Link
            ></td
        >
        </tr>
    </tbody>
    </table>
</div>
<div class="cell is-col-span-7">
    <h3>Contributors & Attribution</h3>
    <table>
    <thead>
        <tr>
        <td>Initial load</td>
        <td>
            {#if MAP.progress.loaded_pages}
            loaded by <Link href={MAP.loaded_by.profile}>{MAP.loaded_by.name}</Link> - {MAP.loaded_by.date}<br
            />
            {:else}--{/if}
        </td>
        </tr>
        <tr>
        <td>Prep</td>
        <td>
            {SESSION_SUMMARY.prep_ct} document{#if SESSION_SUMMARY.prep_ct != 1}s{/if} prepared{#if SESSION_SUMMARY.prep_ct > 0}&nbsp;by
            {#each SESSION_SUMMARY.prep_contributors as c, n}<Link href="/profile/{c.name}">{c.name}</Link> ({c.ct}){#if n != SESSION_SUMMARY.prep_contributors.length - 1},
                {/if}{/each}{/if}
        </td>
        </tr>
        <tr>
        <td>Georef</td>
        <td>
            {SESSION_SUMMARY.georef_ct} georeferencing session{#if SESSION_SUMMARY.georef_ct != 1}s{/if}{#if SESSION_SUMMARY.georef_ct > 0}&nbsp;by
            {#each SESSION_SUMMARY.georef_contributors as c, n}<Link href="/profile/{c.name}">{c.name}</Link> ({c.ct}){#if n != SESSION_SUMMARY.georef_contributors.length - 1},
                {/if}{/each}{/if}
        </td>
        </tr>
        <tr>
        <td>Credit line:</td>
        <td>Library of Congress, Geography and Map Division, Sanborn Maps Collection.</td>
        </tr>
    </thead>
    </table>
</div>
</div>
</div>