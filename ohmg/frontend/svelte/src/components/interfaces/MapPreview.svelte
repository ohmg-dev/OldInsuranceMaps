<script>
	import 'ol/ol.css';
	import '@src/css/map-panel.css';

	import {onMount} from 'svelte';

	import CornersOut from 'phosphor-svelte/lib/CornersOut';
	import Article from 'phosphor-svelte/lib/Article';
	import MapTrifold from "phosphor-svelte/lib/MapTrifold";

	import ToolUIButton from "@components/base/ToolUIButton.svelte";
	import {getModal} from "@components/base/Modal.svelte";

	import ExpandElement from "./buttons/ExpandElement.svelte"
	import MapboxLogoLink from "./buttons/MapboxLogoLink.svelte"

	import LegendModal from "./modals/LegendModal.svelte"

	import {createEmpty, extend} from 'ol/extent';
	import {transformExtent} from 'ol/proj';

	import { makeLayerGroupFromLayerSet } from '@lib/utils';
	import { LyrMousePosition } from "@lib/controls";
	import { MapViewer } from "@lib/viewers";
    import TransparencySlider from './buttons/TransparencySlider.svelte';

	export let CONTEXT;
	export let LAYERSETS;

	let mapViewer;
	let currentZoom;

	let currentBasemap = 'satellite';
	const fullExtent = createEmpty();
	const layerSets = {};
	let layerSetList = [];

	function setVisibility(group, vis) {
		if (vis == 0) {
			group.setVisible(false)
		} else {
			group.setVisible(true)
			group.setOpacity(vis/100)
		}
	}

	const zIndexLookup = {
		"graphic-map-of-volumes": 10,
		"key-map": 15,
		"congested-district-map": 20,
		"main-content": 25,
	}

	$: {
		Object.entries(layerSets).forEach( function ([key, ls]) {
			setVisibility(ls.layerGroup, ls.opacity)
		})
	}

	$: {
		if (mapViewer) {mapViewer.setBasemap(currentBasemap)}
	}

	let layers = LAYERSETS.map((ls) => {
		if (ls.layers.length > 0) {
			const layerGroup = makeLayerGroupFromLayerSet({
				layerSet: ls,
				zIndex: zIndexLookup[ls.id],
				titilerHost: CONTEXT.titiler_host,
				applyMultiMask: true,
			})
			let extent3857;
			if (ls.extent) {
				extent3857 = transformExtent(ls.extent, "EPSG:4326", "EPSG:3857")
				extend(fullExtent, extent3857)
			}
			const setDef = {
				id: ls.id,
				name: ls.name,
				layerGroup: layerGroup,
				sortOrder: zIndexLookup[ls.id],
				opacity: 100,
				layerCt: ls.layers.length,
				extent: extent3857
			}
			layerSets[ls.id] = setDef
			layerSetList.push(ls.id)
			return layerGroup
		}
	})
	layers = layers.filter(item => item);
	layers.sort((a, b) => zIndexLookup[a.id] - zIndexLookup[b.id]);

	onMount(() => {

		mapViewer = new MapViewer('map')
		mapViewer.addBasemaps(CONTEXT.mapbox_api_token, 'satellite')
		mapViewer.addControl(new LyrMousePosition('pointer-coords-preview', null));
		mapViewer.addZoomToExtentControl(fullExtent, 'extent-icon-preview')
		mapViewer.setDefaultExtent(fullExtent)
		mapViewer.resetExtent()
		currentZoom = mapViewer.getZoom()
		layers.forEach(function(lyr) {mapViewer.addLayer(lyr)})

		mapViewer.map.getView().on('change:resolution', () => {
			currentZoom = mapViewer.getZoom()
		})
	});

</script>

<LegendModal id={"modal-legend"} legendUrl={"/static/img/key-nola-1940.png"} legendAlt={"Sanborn Map Key"} />
<div id="map-container" class="map-container"  style="display:flex; justify-content: center; height:550px">
	<div id="map-panel">
		<div id="map" style="height: 100%;"></div>
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
			{#each layerSetList as id}
				{#if layerSets[id].layerCt > 0}
				<div class="layer-section-header">
					<button class="layer-entry" on:click={() => mapViewer.setExtent(layerSets[id].extent)} on:focus={null}>
						<span>{layerSets[id].name}</span>
					</button>
					<span style="color:grey">({layerSets[id].layerCt})</span>
				</div>
				<div class="layer-section-subheader">
					<TransparencySlider bind:opacity={layerSets[id].opacity} />
				</div>
				{/if}
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
