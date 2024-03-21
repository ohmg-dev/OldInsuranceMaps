<script>
import {onMount} from 'svelte';

import IconContext from 'phosphor-svelte/lib/IconContext';

import OpenModalButton from "@components/base/OpenModalButton.svelte"
import BasemapToggleButton from "./buttons/BasemapToggleButton.svelte"
import ExpandElement from "./buttons/ExpandElement.svelte"
import FullExtentButton from "./buttons/FullExtentButton.svelte"

import LegendModal from "./modals/LegendModal.svelte"

import 'ol/ol.css';
import Map from 'ol/Map';
import {createEmpty, extend} from 'ol/extent';
import {transformExtent} from 'ol/proj';
import {OSM, XYZ} from 'ol/source';

import {
	Tile as TileLayer,
	Group as LayerGroup,
} from 'ol/layer';

import '@src/css/map-panel.css';
import {
	iconProps,
	makeLayerGroupFromAnnotationSet,
} from '@lib/utils';

export let CONTEXT;
export let ANNOTATION_SETS;

let map;

const baseGroup = new LayerGroup();
let currentBasemap;

function getClass(n) {
	if (n == 100) {
		return "full-circle"
	} else if (n == 0) {
		return "empty-circle"
	} else {
		return "half-circle"
	}
}

function toggleBasemap() {
	baseGroup.getLayers().forEach( function(layer) {
		layer.setVisible(!layer.getVisible())
		if (layer.getVisible() == true) {
			currentBasemap = layer.get('name')
		}
	})
}

function toggleTransparency(inTrans) {
	let outTrans;
	if (inTrans == 100) {
		outTrans = 0
	} else if (inTrans == 0) {
		outTrans = 50
	} else {
		outTrans = 100
	}
	return outTrans
}

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
ANNOTATION_SETS.sort((a, b) => zIndexLookup[a.id] - zIndexLookup[b.id]);

function initMap() {
	map = new Map({ 
		target: "map",
		maxTilesLoading: 50,
	});
	const osmLayer = new TileLayer({
		source: new OSM(),
		zIndex: 0,
	});
	osmLayer.setVisible(false)
	osmLayer.set('name', 'Open Street Map')
	
	const imageryLayer = new TileLayer({
		source: new XYZ({
			url: 'https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v10/tiles/{z}/{x}/{y}?access_token='+CONTEXT.mapbox_api_token,
			tileSize: 512,
		})
	});
	imageryLayer.setVisible(true)
	imageryLayer.set('name', 'Mapbox Imagery')
	currentBasemap = imageryLayer.get('name')
	
	baseGroup.getLayers().push(osmLayer)
	baseGroup.getLayers().push(imageryLayer)
	map.addLayer(baseGroup);	
};

const annotationSets = {};
let annotationSetList = [];

$: {
	Object.entries(annotationSets).forEach( function ([key, item]) {
		setVisibility(item.layerGroup, item.opacity)
	})
}

const fullExtent = createEmpty();

function createAnnotationSets() {

	ANNOTATION_SETS.forEach( function( aSet ){
		if (aSet.annotations.length > 0) {
			const layerGroup = makeLayerGroupFromAnnotationSet({
				annotationSet: aSet,
				zIndex: zIndexLookup[aSet.id],
				titilerHost: CONTEXT.titiler_host,
				applyMultiMask: true,
			})
			const extent3857 = transformExtent(aSet.extent, "EPSG:4326", "EPSG:3857")
			extend(fullExtent, extent3857)
			const setDef = {
				id: aSet.id,
				name: aSet.name,
				layerGroup: layerGroup,
				sortOrder: zIndexLookup[aSet.id],
				opacity: 100,
				layerCt: aSet.annotations.length,
				extent: extent3857
			}
			annotationSets[aSet.id] = setDef
			annotationSetList.push(aSet.id)
			map.addLayer(setDef.layerGroup)
		}
	})
}

onMount(() => {
	initMap();
	createAnnotationSets();
	map.getView().fit(fullExtent)
});

</script>

<IconContext values={iconProps}>
<LegendModal id={"modal-legend"} legendUrl={"/static/img/key-nola-1940.png"} legendAlt={"Sanborn Map Key"} />
<div id="map-container" class="map-container"  style="display:flex; justify-content: center; height:550px">
	<div id="map-panel">
		<div id="map" style="height: 100%;"></div>
	</div>
	<div id="layer-panel" style="display: flex;">
		<div class="layer-section-header" style="border-top-width: 1px;">
			<FullExtentButton action={() => {map.getView().fit(fullExtent)}} />
			<OpenModalButton style="tool-ui" icon="article" modalId={"modal-legend"} />
			<ExpandElement elementId={'map-container'} maps={[map]} />
		</div>
		<div id="layer-list" style="flex:2;">
			<div class="layer-section-header">
				<span>Basemap</span>
				<BasemapToggleButton action={toggleBasemap} />
			</div>
			<div class="layer-section-subheader">
				{currentBasemap}
			</div>
			{#each annotationSetList as id}
				{#if annotationSets[id].layerCt > 0}
				<div class="layer-section-header">
					<button class="layer-entry" on:click={() => map.getView().fit(annotationSets[id].extent)} on:focus={null}>
						<span>{annotationSets[id].name}</span>
					</button>
					<span style="color:grey">({annotationSets[id].layerCt})</span>
				</div>
				<div class="layer-section-subheader">
					<div style="display:flex; align-items:center;">
						<input class="slider" type=range bind:value={annotationSets[id].opacity} min=0 max=100>
						<button class="transparency-toggle" on:click={() => {annotationSets[id].opacity = toggleTransparency(annotationSets[id].opacity)}}>
							<i class="{getClass(annotationSets[id].opacity)}" />
						</button>
					</div>
				</div>
				{/if}
			{/each}
		</div>
	</div>
</div>
</IconContext>

<style>
	button.layer-entry {
		cursor: pointer;
		border: none;
		background: none;
	}
	button.layer-entry:hover {
		color: #1b4060;
	}
</style>
