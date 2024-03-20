<script>
    import Map from '@components/overviews/Map.svelte';

	export let VOLUME;
	export let ANNOTATION_SETS;
	export let CSRFTOKEN;
	export let USER;
	export let MAPBOX_API_KEY;
	export let TITILER_HOST;
	export let ROUTES;
</script>

<Map {VOLUME} {ANNOTATION_SETS} {CSRFTOKEN} {USER} {MAPBOX_API_KEY} {TITILER_HOST} {ROUTES} />
