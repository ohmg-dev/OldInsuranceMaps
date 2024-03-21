<script>
    import Map from '@components/overviews/Map.svelte';

	export let CONTEXT;
	export let VOLUME;
	export let ANNOTATION_SETS;
</script>

<Map {CONTEXT} {VOLUME} {ANNOTATION_SETS} />
