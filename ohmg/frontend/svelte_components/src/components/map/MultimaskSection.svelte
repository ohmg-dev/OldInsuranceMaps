<script>
    import SigninReminder from "../common/SigninReminder.svelte";
    import MultiMask from "../interfaces/MultiMask.svelte";

    export let CONTEXT;
    export let LAYERSETS;
    export let layerSetLookup;
    export let multimaskKey;
    export let reinitMultimask = () => {};
    export let reinitPreview = () => {};
    export let userCanEdit;

    
    
    let currentLayerSet = "main-content";
</script>


{#if !CONTEXT.user.is_authenticated}
    <SigninReminder csrfToken={CONTEXT.csrf_token} />
{/if}
<select
    class="item-select"
    bind:value={currentLayerSet}
    on:change={(e) => {
        reinitMultimask();
    }}
>
    {#each LAYERSETS as ls}
    {#if ls.layers}
        <option value={ls.id}>{ls.name}</option>
    {/if}
    {/each}
</select>
<span>
    Masked layers:
    {#if layerSetLookup[currentLayerSet].multimask_geojson}
    {layerSetLookup[currentLayerSet].multimask_geojson.features.length}/{layerSetLookup[currentLayerSet].layers
        .length}
    {:else}
    0/{layerSetLookup[currentLayerSet].layers.length}
    {/if}
</span>
<span>
    <em
    >&mdash; <strong>Important:</strong> Do not work on a multimask while there is other work in progress on this
    map (you could lose work).</em
    >
</span>
{#key multimaskKey}
    <MultiMask
    LAYERSET={layerSetLookup[currentLayerSet]}
    {CONTEXT}
    DISABLED={!userCanEdit}
    resetMosaic={reinitPreview}
    />
{/key}

<style>
  select.item-select {
    margin-right: 3px;
    color: #2c689c;
    cursor: pointer;
  }
</style>