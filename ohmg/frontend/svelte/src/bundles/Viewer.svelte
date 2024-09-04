<script>
	import Viewer from "@components/interfaces/Viewer.svelte";

	export let CONTEXT
	export let PLACE;
	export let MAPS;
</script>
<Viewer {CONTEXT} {PLACE} {MAPS} />