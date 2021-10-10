<script>
import {onMount} from 'svelte';

export let DOC_TITLE;
export let DOC_IMG_URL;

export let SPLIT_URL;
export let IS_GEOREFERENCED;
export let GEOREFERENCE_URL;

</script>

<h1>{DOC_TITLE}</h1>
<div class="main" style="display:flex; flex-direction:row; justify-content:space-between;">
  <div class="item">
    <h2>Splitting</h2>
    <p>If this map has insets, or covers more than one area, it must be split into separate documents 
      so each one can be georeferenced individually. Once it has been split, you will find all of the pieces here.
    </p>
    <a href="{SPLIT_URL}">Split this document.</a>
    <h2>Georeferencing</h2>
    {#if IS_GEOREFERENCED}
    <p>This document has been already been georeferenced, but you can <a href="{GEOREFERENCE_URL}">improve the georeferencing</a> if you want.</p>
    {:else}
    <a href="{GEOREFERENCE_URL}">Georeference this document.</a>
    {/if}
    <h2>Trimming</h2>
    {#if IS_GEOREFERENCED}
    <a href="{GEOREFERENCE_URL}">Georeference this document.</a>
    {:else}
    <pdfdf></pdfdf>
    {/if}
  </div>
  <div class="item">
    <img src="{DOC_IMG_URL}" height="400px" alt="{DOC_TITLE}"/>
  </div>
</div>

<style>

.main {
  display: flex;
  justify-content: space-between;
  flex-direction: row;
}

</style>
