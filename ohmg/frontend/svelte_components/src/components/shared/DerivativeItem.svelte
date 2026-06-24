<script>
    export let title;
    export let dateTimestamp = null;
    export let dateString = null;
    export let isStale = false;

    let dateClass = isStale ? "timestamp stale" : "timestamp";
</script>


<dt>
    <span>{title}</span>
    {#if dateTimestamp}
    <span class={dateClass}>{new Date(dateTimestamp * 1000).toLocaleString()}</span>
    {:else if dateString}
    <span class={dateClass}>{dateString}</span>
    {/if}
</dt>
<dd>
    <slot />
</dd>

<style>

    dt, dd {
        padding: .25em .5em;
    }
    dt {
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        font-weight: 700;
        font-size: .85em;
        background-color: #f6f6f6;
    }
    dd {
        padding-left: 1em;
    }
    dt > span.timestamp {
        color: grey;
    }
    dt > span.timestamp::before {
        content: "["
    }
    dt > span.timestamp::after {
        content: "]"
    }
    dt > span.timestamp.stale {
        color: red;
    }
    .na-message {
        /* color: grey; */
        font-size: .8em;
    }
    .na-message::before {
        content: "-- "
    }
</style>