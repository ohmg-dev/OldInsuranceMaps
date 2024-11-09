<script>
    import Map from '@components/overviews/Map.svelte';

	export let CONTEXT;
	export let MAP;
	export let LOCALE;
	export let SESSION_SUMMARY;
	export let LAYERSETS;
	export let LAYERSET_CATEGORIES
</script>

<Map {CONTEXT} {MAP} {LOCALE} {SESSION_SUMMARY} {LAYERSETS} {LAYERSET_CATEGORIES} />
