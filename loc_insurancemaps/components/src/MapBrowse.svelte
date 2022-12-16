<script>
import {onMount} from 'svelte';

import {fromLonLat} from 'ol/proj';
import Overlay from 'ol/Overlay';

import 'ol/ol.css';
import Map from 'ol/Map';
import View from 'ol/View';

import GeoJSON from 'ol/format/GeoJSON';

import OSM from 'ol/source/OSM';
import VectorSource from 'ol/source/Vector';

import TileLayer from 'ol/layer/Tile';
import VectorLayer from 'ol/layer/Vector';

import Styles from './js/ol-styles';
const styles = new Styles();

export let PLACES_GEOJSON;

const osmLayer = new TileLayer({ source: new OSM() });

let mapView;
let container;
let content;
let closer;
let overlay;
function MapViewer (elementId) {

	const targetElement = document.getElementById(elementId);

	container = document.getElementById('popup');
	content = document.getElementById('popup-content');
	closer = document.getElementById('popup-closer');
	overlay = new Overlay({
		element: container,
		autoPan: {
			animation: {
			duration: 250,
			},
		},
	});

	// create map
	const map = new Map({
		target: targetElement,
		maxTilesLoading: 50,
		overlays: [overlay],
		view: new View({
			zoom: 7,
			center: fromLonLat([-92.036, 31.16]),
		})
	});
	// map.getView().fit(transformExtent([-94, 28, -88, 33], "EPSG:4326", "EPSG:3857"))

	// if (homeExtent) {map.getView().fit(homeExtent)}
	const placeLayer = new VectorLayer({
		source: new VectorSource({
			features: new GeoJSON().readFeatures(PLACES_GEOJSON, {
				dataProjection: "EPSG:4326",
				featureProjection: "EPSG:3857",
			})
		}),
		style: styles.browseMapStyle,
		zIndex: 500,
	});

	map.addLayer(osmLayer);
	map.addLayer(placeLayer);

	map.on('pointermove', function (event) {
		let hit = false;
		map.forEachFeatureAtPixel(
			event.pixel,
			function (feature) {
				if (hit) return // only hover on one point at a time
				 hit = true;
			},
			{
			hitTolerance: 2,
			}
		);
		if (!hit) {document.body.style.cursor = 'default'} else {document.body.style.cursor = 'pointer'}
	});

	map.on('singleclick', function (event) {
		let hit = false;
		map.forEachFeatureAtPixel(
			event.pixel,
			function (feature) {
				if (hit) return // only hover on one point at a time
				const props = feature.getProperties();
				const volList = []
				props.volumes.forEach( function(vol) {
					volList.push(`<a title="${vol.title}" href="Summary of ${vol.url}">${vol.year}</a>`)
				})
				const volListStr = volList.join(" • ")
				const popupContent = `
					<h4><a title="Show in viewer" href="${props.place.url}">${props.place.name}</a></h4>
					<p>
					${volListStr}
					</p>
				`
				content.innerHTML = popupContent;
				overlay.setPosition(feature.getGeometry().getCoordinates());
				hit = true;
			},
			{
			hitTolerance: 2,
			}
		);
		if (!hit) {overlay.setPosition(undefined);}
	});

	closer.onclick = function () {
		overlay.setPosition(undefined);
		closer.blur();
		return false;
	};

	this.map = map;
}

onMount(() => {
	mapView = new MapViewer("map");
});


</script>
<div id="map"></div>
<div id="popup" class="ol-popup" style="">
	<a href="#" title="Close popup" id="popup-closer" class="ol-popup-closer"></a>
	<div id="popup-content"></div>
</div>
<style>

#map {
	height: 600px;
	width: 100%;
	/* position: absolute; */
}

.ol-popup {
	position: absolute;
	background-color: white;
	box-shadow: 0 1px 4px rgba(0,0,0,0.2);
	padding: 15px;
	border-radius: 10px;
	border: 1px solid #cccccc;
	bottom: 12px;
	left: -50px;
	min-width: 280px;
	z-index: 1000000000;
}
.ol-popup:after, .ol-popup:before {
	top: 100%;
	border: solid transparent;
	content: " ";
	height: 0;
	width: 0;
	position: absolute;
	pointer-events: none;
}
.ol-popup:after {
	border-top-color: white;
	border-width: 10px;
	left: 48px;
	margin-left: -10px;
}
.ol-popup:before {
	border-top-color: #cccccc;
	border-width: 11px;
	left: 48px;
	margin-left: -11px;
}
.ol-popup-closer {
	text-decoration: none;
	position: absolute;
	top: 2px;
	right: 8px;
}
.ol-popup-closer:after {
	content: "✖";
}

</style>
