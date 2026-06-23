<script>
    import { openModal } from "../base/Modal.svelte";
    import { getFromAPI } from "../../lib/requests";
    import { submitPostRequest } from "../../lib/requests";
    import MultiMask from "../interfaces/MultiMask.svelte";
    import ModalInfo from "../base/ModalInfo.svelte";

    export let CONTEXT;
    export let mapId;
    export let multimaskKey;
    export let reinitMultimask = () => {};
    export let userCanEdit;

    let dirty = false;

    let errMsg;

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
            openModal("modal-save-success")
            dirty = false;
            initLayersets();
        } else {
            errMsg = response.message;
            openModal("modal-save-error");
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
<ModalInfo id="modal-save-success">
    <p>Masks saved successfully.</p>
</ModalInfo>
<ModalInfo id="modal-save-error">
    <p>Error! MultiMask not saved. The following layers have errors:</p>
    <p>{@html errMsg}</p>
    <p>You must fix these errors before you can save your work. Keep in mind it is
        sometimes easier to remove and recreate a mask than track down and fix
        specific issues.</p>
</ModalInfo>
<p>
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
</p>
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