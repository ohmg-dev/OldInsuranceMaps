<script>
    import Map from '@components/overviews/Map.svelte';

	export let CONTEXT;
	export let MAP;
	export let LOCALE;
	export let SESSION_SUMMARY;
	export let ANNOTATION_SETS;
	export let ANNOTATION_SET_OPTIONS
</script>

<Map {CONTEXT} {MAP} {LOCALE} {SESSION_SUMMARY} {ANNOTATION_SETS} {ANNOTATION_SET_OPTIONS} />
