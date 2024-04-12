<script>
    import Map from '@components/overviews/Map.svelte';

	export let CONTEXT;
	export let VOLUME;
	export let ANNOTATION_SETS;
	export let ANNOTATION_SET_OPTIONS
</script>

<Map {CONTEXT} {VOLUME} {ANNOTATION_SETS} {ANNOTATION_SET_OPTIONS} />
