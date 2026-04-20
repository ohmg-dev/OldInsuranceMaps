<script>
    import { getFromAPI } from "../../lib/requests";
    import { submitPostRequest } from "../../lib/requests";
    import MultiMask from "../interfaces/MultiMask.svelte";

    export let CONTEXT;
    export let mapId;
    export let multimaskKey;
    export let reinitMultimask = () => {};
    export let userCanEdit;

    let dirty = false;

    let currentLayerSetId = "main-content";
    let layerSetLookup = {};
    $: currentLayerSet = layerSetLookup[currentLayerSetId]

    const initLayersets = () => {
        getFromAPI(`/api/beta2/layersets/?map=${mapId}`, CONTEXT.ohmg_api_headers, (response) => {
            layerSetLookup = {};
            response.forEach(function (ls) {
                layerSetLookup[ls.id] = ls
            });
        });
    }
    initLayersets()

    function handleMultimaskSubmitResponse(response) {
        if (response.success) {
            window.alert('Masks saved successfully.');
            dirty = false;
            initLayersets();
        } else {
            let errMsg = 'Error! MultiMask not saved. You must remove and remake the following masks:\n';
            errMsg += response.message;
            alert(errMsg);
        }
    }

    function submit(geojson) {
        submitPostRequest(
        '/layerset/',
        CONTEXT.ohmg_post_headers,
        'set-mask',
        {
            'multimask-geojson': geojson,
            'map-id': mapId,
            category: currentLayerSetId,
        },
        handleMultimaskSubmitResponse,
        );
    }
</script>
<span>
    Select which multimask to work on:
</span>
<select
    class="item-select"
    bind:value={currentLayerSetId}
    on:change={(e) => {
        reinitMultimask();
    }}
>
    {#each Object.entries(layerSetLookup) as [id, ls]}
    {#if ls.layers}
        <option value={id}>{`${ls.name} (${ls.layers_masked_ct}/${ls.layers.length})`}</option>
    {/if}
    {/each}
</select>
{#if currentLayerSet}
    {#key multimaskKey}
        <MultiMask
            {CONTEXT}
            LAYERS={currentLayerSet.layers}
            DISABLED={!userCanEdit}
            handleSubmit={submit}
            bind:dirty
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