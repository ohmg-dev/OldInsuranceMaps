<script>
  import Resource from "@components/overviews/Resource.svelte";

  export let ROUTES;
  export let CSRFTOKEN;
  export let USER;
  export let RESOURCE;
  export let VOLUME;
  export let SPLIT_SUMMARY;
  export let GEOREFERENCE_SUMMARY;
  export let MAPBOX_API_KEY;
  export let TITILER_HOST;
</script>

<Resource {ROUTES} {CSRFTOKEN} {USER} {RESOURCE} {VOLUME} {SPLIT_SUMMARY} {GEOREFERENCE_SUMMARY} {MAPBOX_API_KEY} {TITILER_HOST} />