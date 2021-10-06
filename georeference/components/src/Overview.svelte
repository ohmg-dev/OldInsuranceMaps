<script>
  import {onMount} from 'svelte';

  export let DOC_TITLE;


  </script>
  
  <h1>Split, Georeference, Trim</h1>
  {#if (!DOC_TITLE)}
  <p>This module provides tools that facilitate the transformation of Documents into Layers</p>
  {:else}
  {DOC_TITLE}
  {/if}
  <style>
  
  
  </style>
  