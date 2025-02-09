<script>
	import 'ol/ol.css';
	import '@/css/map-panel.css';

	import {onMount} from 'svelte';

	import CornersOut from 'phosphor-svelte/lib/CornersOut';
	import Article from 'phosphor-svelte/lib/Article';
	import MapTrifold from "phosphor-svelte/lib/MapTrifold";

	import ToolUIButton from "@/base/ToolUIButton.svelte";
	import {getModal} from "@/base/Modal.svelte";

	import ExpandElement from "./buttons/ExpandElement.svelte";
	import MapboxLogoLink from "./buttons/MapboxLogoLink.svelte";
	import RefreshMapButton from './buttons/RefreshMapButton.svelte';

	import LegendModal from "./modals/LegendModal.svelte";

	import {createEmpty, extend} from 'ol/extent';
	import {transformExtent} from 'ol/proj';

	import { makeLayerGroupFromLayerSet } from '@lib/utils';
	import { LyrMousePosition } from "@lib/controls";
	import { MapViewer } from "@lib/viewers";
	import { getFromAPI } from "@lib/requests";
    import TransparencySlider from './buttons/TransparencySlider.svelte';

	export let CONTEXT;
	export let mapId;
	export let mapExtent;
	export let refreshable = false;

	let mapViewer;
	let currentZoom;

	const mapExtent3857 = transformExtent(mapExtent, "EPSG:4326", "EPSG:3857")

	let currentBasemap = 'satellite';
	let layerSetLookup = new Object ();

	const zIndexLookup = {
		"graphic-map-of-volumes": 10,
		"key-map": 15,
		"congested-district-map": 20,
		"skeleton-map": 23,
		"main-content": 25,
	}

	$: layerIdList = Object.keys(layerSetLookup).sort((a, b) => zIndexLookup[a] - zIndexLookup[b])

	function updateLayersets(layerSets) {
		const newExtent = createEmpty();
		const newLookup = {};
		layerSets.forEach((ls) => {
			let extent3857;
			if (ls.extent) {
				extent3857 = transformExtent(ls.extent, "EPSG:4326", "EPSG:3857")
				extend(newExtent, extent3857)
			}
			const setDef = {
				id: ls.id,
				name: ls.name,
				layerGroup: makeLayerGroupFromLayerSet({
					layerSet: ls,
					zIndex: zIndexLookup[ls.id],
					titilerHost: CONTEXT.titiler_host,
					applyMultiMask: true,
				}),
				opacity: 100,
				layerCt: ls.layers.length,
				extent: extent3857
			}
			newLookup[ls.id] = setDef
		})
		layerSetLookup = newLookup;
		updateMapViewer()
		mapViewer.setDefaultExtent(newExtent)
	}

	function updateMapViewer() {
		mapViewer.clearNonBasemapLayers()
		for (const [key, value] of Object.entries(layerSetLookup)) {
			mapViewer.addLayer(value.layerGroup);
		}
	}

	function setVisibility(group, vis) {
		if (vis == 0) {
			group.setVisible(false)
		} else {
			group.setVisible(true)
			group.setOpacity(vis/100)
		}
	}

	$: {
		Object.entries(layerSetLookup).forEach( function ([key, ls]) {
			setVisibility(ls.layerGroup, ls.opacity)
		})
	}

	$: {
		if (mapViewer) {mapViewer.setBasemap(currentBasemap)}
	}

	function fetchLayerSets() {
		getFromAPI(`/api/beta2/layersets/?map=${mapId}`,
			CONTEXT.ohmg_api_headers,
			(response) => {
				updateLayersets(response)
				refreshable = false;
			}
		);
	}

	onMount(() => {
		mapViewer = new MapViewer('map')
		mapViewer.addBasemaps(CONTEXT.mapbox_api_token, 'satellite');
		mapViewer.addControl(new LyrMousePosition('pointer-coords-preview', null));
		mapViewer.setDefaultExtent(mapExtent3857);
		mapViewer.addZoomToExtentControl(mapExtent3857, 'extent-icon-preview');
		mapViewer.resetExtent();

		currentZoom = mapViewer.getZoom();
		mapViewer.map.getView().on('change:resolution', () => {
			currentZoom = mapViewer.getZoom();
		})

		fetchLayerSets()
	});

</script>

<LegendModal id={"modal-legend"} legendUrl={"/static/img/key-nola-1940.png"} legendAlt={"Sanborn Map Key"} />
<div id="map-container" class="map-container"  style="display:flex; justify-content: center; height:550px">
	<div id="map-panel">
		{#if refreshable}
			<RefreshMapButton handleRefresh={fetchLayerSets} />
		{/if}
		<div id="map" style="height: 100%;" style:margin-top={refreshable ? "-2em" : ""}></div>
		<i id='extent-icon-preview'><CornersOut size={'20px'} /></i>
		{#if currentBasemap == "satellite"}
			<MapboxLogoLink />
		{/if}
	</div>
	<div id="layer-panel" style="display: flex;">
		<div class="layer-section-header" style="border-top-width: 1px;">
			<ToolUIButton action={() => {getModal('modal-legend').open()}}>
				<Article />
			</ToolUIButton>
			<ExpandElement elementId={'map-container'} />
		</div>
		<div id="layer-list" style="flex:2;">
			<div class="layer-section-header">
				<span>Basemap</span>
				<ToolUIButton action={() => {currentBasemap = currentBasemap == "osm" ? "satellite" : "osm"}} title="change basemap">
					<MapTrifold />
				</ToolUIButton>
			</div>
			<div class="layer-section-subheader">
				{currentBasemap == 'satellite' ? 'Mapbox Imagery' : 'Open Street Map'}
			</div>
			{#each layerIdList as id}
				<div class="layer-section-header">
					<button class="layer-entry" on:click={() => mapViewer.setExtent(layerSetLookup[id].extent)} on:focus={null}>
						<span>{layerSetLookup[id].name}</span>
					</button>
					<span style="color:grey">({layerSetLookup[id].layerCt})</span>
				</div>
				<div class="layer-section-subheader">
					<TransparencySlider bind:opacity={layerSetLookup[id].opacity} />
				</div>
			{/each}
		</div>
		<div id="info-box">
			<span>z: {currentZoom}</span>
			<span id="pointer-coords-preview"></span>
		</div>
	</div>
</div>

<style>
	#info-box {
		position: relative;
		display: flex;
		flex-direction: column;
		background-color: rgba(255,255,255,.6);
		align-items: end;
		padding: 0 10px;
		font-size: .8em;
	}
</style>
