<script>
    import Link from "../../base/Link.svelte";
    export let job;
    export let maskDate;

    const stale = maskDate > job.date_started;
    const dateDisplay = new Date(job.date_started * 1000).toLocaleString()
    const title = `latest build: ${dateDisplay}`

</script>

{#if job.stage == "completed"}
    {#if stale}
    <div class="tag is-danger" title={title}>
        stale
    </div>
    {:else}
    <div class="tag is-success" title={title}>
        up-to-date
    </div>
    {/if}
{:else}
    <div class={`tag ${job.stage == "queued" ? 'is-info' : 'is-warning'}`} title={title}>
        <Link href="/jobs" style="color:black;" external={true} title="Open running jobs page...">{job.stage}</Link>
    </div>
{/if}