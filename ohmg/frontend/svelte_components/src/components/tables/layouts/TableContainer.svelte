<script>
    export let items = [];
    export let loading = false;
</script>

<div style="overflow-y: auto">
    {#if items.length > 0}
    <table>
        <thead>
            <tr>
                <slot name="header-row"></slot>
            </tr>
        </thead>
        <tbody>
            {#each items as item}
                <tr style="height:38px; vertical-align: center;">
                    <slot name="data-row" {item} />
                </tr>
            {/each}
      </tbody>
    </table>
    {:else}
    <div class="level" style="background: white;">
        <div class="level-item" style="margin:5px 0;">
        <em>{loading ? 'loading...' : 'no results'}</em>
        </div>
    </div>
    {/if}
</div>