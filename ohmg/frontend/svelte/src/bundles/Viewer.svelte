<script>
	import Viewer from "@components/interfaces/Viewer.svelte";

	export let PLACE;
	export let MAPBOX_API_KEY;
	export let VOLUMES;
	export let TITILER_HOST;
	export let ON_MOBILE;
</script>
<Viewer {PLACE} {MAPBOX_API_KEY} {VOLUMES} {TITILER_HOST} {ON_MOBILE} />