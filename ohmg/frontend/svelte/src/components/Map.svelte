<script>
    import Map from '@/overviews/Map.svelte';

	export let CONTEXT;
	export let MAP;
	export let LOCALE;
	export let SESSION_SUMMARY;
	export let LAYERSETS;
	export let LAYERSET_CATEGORIES;
	export let userFilterItems;
</script>

<Map {CONTEXT} {MAP} {LOCALE} {SESSION_SUMMARY} {LAYERSETS} {LAYERSET_CATEGORIES} {userFilterItems} />
