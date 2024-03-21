<script>
	import Viewer from "@components/interfaces/Viewer.svelte";

	export let CONTEXT
	export let PLACE;
	export let VOLUMES;
</script>
<Viewer {CONTEXT} {PLACE} {VOLUMES} />