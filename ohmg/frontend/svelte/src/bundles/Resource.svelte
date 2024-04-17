<script>
  import Resource from "@components/overviews/Resource.svelte";

  export let CONTEXT;
  export let RESOURCE;
  export let VOLUME;
  export let SPLIT_SUMMARY;
  export let GEOREFERENCE_SUMMARY;
</script>

<Resource {CONTEXT} {RESOURCE} {VOLUME} {SPLIT_SUMMARY} {GEOREFERENCE_SUMMARY} />