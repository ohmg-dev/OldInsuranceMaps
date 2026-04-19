<script>
    import { getFromAPI } from "../../lib/requests";
    import MultiMask from "../interfaces/MultiMask.svelte";

    export let CONTEXT;
    export let mapId;
    export let multimaskKey;
    export let reinitMultimask = () => {};
    export let reinitPreview = () => {};
    export let userCanEdit;

    let currentLayerSet = "main-content";
    let layerSetLookup = {};

    getFromAPI(`/api/beta2/layersets/?map=${mapId}`, CONTEXT.ohmg_api_headers, (response) => {
        layerSetLookup = {};
        response.forEach(function (ls) {
            layerSetLookup[ls.id] = ls
        });
    });
</script>

<select
    class="item-select"
    bind:value={currentLayerSet}
    on:change={(e) => {
        reinitMultimask();
    }}
>
    {#each Object.entries(layerSetLookup) as [id, ls]}
    {#if ls.layers}
        <option value={id}>{ls.name}</option>
    {/if}
    {/each}
</select>
{#if layerSetLookup[currentLayerSet]}
<span>
    Masked layers:
    {#if layerSetLookup[currentLayerSet].multimask_geojson}
    {layerSetLookup[currentLayerSet].multimask_geojson.features.length}/{layerSetLookup[currentLayerSet].layers
        .length}
    {:else}
    0/{layerSetLookup[currentLayerSet].layers.length}
    {/if}
</span>
{/if}
<span>
    <em
    >&mdash; <strong>Important:</strong> Do not work on a multimask while there is other work in progress on this
    map (you could lose work).</em
    >
</span>
{#if layerSetLookup[currentLayerSet]}
{#key multimaskKey}
    <MultiMask
    LAYERSET={layerSetLookup[currentLayerSet]}
    {CONTEXT}
    DISABLED={!userCanEdit}
    resetMosaic={reinitPreview}
    />
{/key}
{/if}

<style>
  select.item-select {
    margin-right: 3px;
    color: #2c689c;
    cursor: pointer;
  }
</style>