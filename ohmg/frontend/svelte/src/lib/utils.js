import VectorSource from 'ol/source/Vector';
import ImageStatic from 'ol/source/ImageStatic';
import OSM from 'ol/source/OSM';
import XYZ from 'ol/source/XYZ';
import TileWMS from 'ol/source/TileWMS';

import MousePosition from 'ol/control/MousePosition';
import {createStringXY} from 'ol/coordinate';

import GeoJSON from 'ol/format/GeoJSON';

import {transformExtent} from 'ol/proj';

import Feature from 'ol/Feature';
import Polygon from 'ol/geom/Polygon';
import Point from 'ol/geom/Point';

import Style from 'ol/style/Style';
import Fill from 'ol/style/Fill';
import Stroke from 'ol/style/Stroke';
import RegularShape from 'ol/style/RegularShape';

import {Modify} from 'ol/interaction';

import TileLayer from 'ol/layer/Tile';
import VectorLayer from 'ol/layer/Vector';
import LayerGroup from 'ol/layer/Group';
import MapboxVector from 'ol/layer/MapboxVector';

import Crop from 'ol-ext/filter/Crop';
import { extendFlatCoordinates, containsXY } from 'ol/extent';

export function makeTitilerXYZUrl (options) {
	// options must be an object with the following properties:
	// {
	//	 host: full address to titiler instance, e.g. https://titiler.oldinsurancemaps.net
	//	 url: url for resource to tile
	//	 doubleEncode: true/false for whether to double encode the returned url (default false)
	//	 colorMapName: name of pre-made colormap to use
	//	 bandNumber: band number to use for colormap
	//	 colorMap: a full custom colormap object to pass through the colormap param
	// }

	// colorMap='{"0": "#e5f5f9","10": "#99d8c9","200": "#2ca25f"}'
	// colorMapParam=`&bidx=1&colormap=${encodeURIComponent(colorMap)}`

	let finalUrl = options.host;
	if (String(options.url).endsWith(".json")) {
		finalUrl += "/mosaicjson/tiles/{z}/{x}/{y}.png?TileMatrixSetId=WebMercatorQuad";
	} else {
		finalUrl += "/cog/tiles/{z}/{x}/{y}.png?TileMatrixSetId=WebMercatorQuad";
	}
	
	const encodedUrl = encodeURIComponent(options.url)
	finalUrl += `&url=${encodedUrl}`

	if (options.colorMapName) {
		finalUrl += `&colormap_name=${options.colorMapName}`
	}
	if (options.bandNumber) {
		finalUrl += `&bidx=${options.bandNumber}`
	}
	if (options.colorMap) {
		const colorMap = encodeURIComponent(options.colorMap)
		finalUrl += `&colormap=${colorMap}`
	}
	if (options.doubleEncode) {
		finalUrl = encodeURIComponent(finalUrl)
	}

	return finalUrl
}

export function makeSatelliteLayer (apiKey) {
	return new TileLayer({
		source: new XYZ({
		url: 'https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v10/tiles/{z}/{x}/{y}?access_token='+apiKey,
		tileSize: 512,
		attributions: [
			`© <a href="https://www.mapbox.com/about/maps/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> <strong><a href="https://www.mapbox.com/map-feedback/" target="_blank">Improve this map</a></strong>`
		]
		})
	});
}

// EXPERIMENTAL vector basemap, not in use
export function makeMapboxStreetsLayer (apiKey) {
	//return new TileLayer({
	//	source: new XYZ({
	//		url: 'https://api.mapbox.com/styles/v1/legiongis/ckihiobcu0m3319sz4i5djtaj/tiles/{z}/{x}/{y}?access_token='+apiKey,
	//		tileSize: 512,
	//		attributions: [
	//			`© <a href="https://www.mapbox.com/about/maps/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> <strong><a href="https://www.mapbox.com/map-feedback/" target="_blank">Improve this map</a></strong>`
	//	]
	//})
	//	});
	return new MapboxVector({
	//		styleUrl: 'mapbox://styles/legiongis/ckihiobcu0m3319sz4i5djtaj',
		styleUrl: 'mapbox://styles/mapbox/streets-v11',
		accessToken: apiKey,
		zIndex: 0,
		// declutter false keeps the labels with the rest of the style instead of
		// placing them above all other layers. However, it causes a lot of clutter.
		declutter: false,
	})
}
	
export function makeOSMLayer () {
	return new TileLayer({
		source: new OSM({
		attributions: [
			`© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors.`
		]
		}),
	})
}

export function makeBasemaps (mapboxKey) {
	return [
		{ 
			id: "osm",
			layer: makeOSMLayer(),
			label: "Streets"
		},
		{
			id: "satellite",
			layer: makeSatelliteLayer(mapboxKey),
			label: "Streets+Satellite"
		},
	]
}

export function makeModifyInteraction(hitDetection, source, targetElement, style) {
	const modify = new Modify({
		hitDetection: hitDetection,
		source: source,
		style: style,
	});

	modify.on(['modifystart', 'modifyend'], function (e) {
		targetElement.style.cursor = e.type === 'modifystart' ? 'grabbing' : 'pointer';
	});

	let overlaySource = modify.getOverlay().getSource();
	overlaySource.on(['addfeature', 'removefeature'], function (e) {
		targetElement.style.cursor = e.type === 'addfeature' ? 'pointer' : '';
	});
	return modify
}

export function makeLayerGroupFromAnnotationSet (options) {
	// options must be an object with the following properties:
	// {
	//	annotationSet: serialized item (this includes layers, extent, etc.)
	//	titilerHost: full address to titiler instance, e.g. https://titiler.oldinsurancemaps.net
	//	zIndex: optional zIndex to apply to the returned LayerGroup
	//	excludeLayerId: the id of a single layer that should be omitted from the LayerGroup
	//  applyMultiMask: if a MultiMask is present in the Annotation Set, apply it
	// }

	const lyrGroup = new LayerGroup();
	options.annotationSet.annotations.forEach( function(annotation) {
		if (annotation.slug != options.excludeLayerId && annotation.extent) {

			const lyrExtent = transformExtent(annotation.extent, "EPSG:4326", "EPSG:3857")

			// create the actual ol layers and add to group.
			let newLayer = new TileLayer({
				source: new XYZ({
				url: makeTitilerXYZUrl({
						host: options.titilerHost,
						url: annotation.urls.cog,
					}),
				}),
				extent: lyrExtent
			});

			lyrGroup.getLayers().push(newLayer)

			if (options.applyMultiMask && options.annotationSet.multimask_geojson) {
				options.annotationSet.multimask_geojson.features.forEach( function(f) {
					if (f.properties.layer == annotation.slug) {
						const feature = new GeoJSON().readFeature(f.geometry)
						feature.getGeometry().transform("EPSG:4326", "EPSG:3857")
						const crop = new Crop({
							feature: feature,
							wrapX: true,
							inner: false
						});
						newLayer.addFilter(crop);
					}
				});
			}
		}
	});

	options.zIndex && lyrGroup.setZIndex(options.zIndex)
	return lyrGroup
}

export function makeLayerGroupFromLayerSet (options) {
	// options must be an object with the following properties:
	// {
	//	annotationSet: serialized item (this includes layers, extent, etc.)
	//	titilerHost: full address to titiler instance, e.g. https://titiler.oldinsurancemaps.net
	//	zIndex: optional zIndex to apply to the returned LayerGroup
	//	excludeLayerId: the id of a single layer that should be omitted from the LayerGroup
	//  applyMultiMask: if a MultiMask is present in the Annotation Set, apply it
	// }

	const lyrGroup = new LayerGroup();
	options.annotationSet.layers.forEach( function(layer) {
		if (layer.slug != options.excludeLayerId && layer.extent) {

			const lyrExtent = transformExtent(layer.extent, "EPSG:4326", "EPSG:3857")

			// create the actual ol layers and add to group.
			let newLayer = new TileLayer({
				source: new XYZ({
				url: makeTitilerXYZUrl({
						host: options.titilerHost,
						url: layer.urls.cog,
					}),
				}),
				extent: lyrExtent
			});

			lyrGroup.getLayers().push(newLayer)

			if (options.applyMultiMask && options.annotationSet.multimask_geojson) {
				options.annotationSet.multimask_geojson.features.forEach( function(f) {
					if (f.properties.layer == layer.slug) {
						const feature = new GeoJSON().readFeature(f.geometry)
						feature.getGeometry().transform("EPSG:4326", "EPSG:3857")
						const crop = new Crop({
							feature: feature,
							wrapX: true,
							inner: false
						});
						newLayer.addFilter(crop);
					}
				});
			}
		}
	});

	options.zIndex && lyrGroup.setZIndex(options.zIndex)
	return lyrGroup
}

export function generateFullMaskLayer (map) {
	let projExtent = map.getView().getProjection().getExtent()
	const polygon = new Polygon([[
		[projExtent[0], projExtent[1]],
		[projExtent[2], projExtent[1]],
		[projExtent[2], projExtent[3]],
		[projExtent[0], projExtent[3]],
		[projExtent[0], projExtent[1]],
	]])	
	const layer = new VectorLayer({
		source: new VectorSource({
			features: [ new Feature({ geometry: polygon }) ]
		}),
		style: new Style({
			fill: new Fill({ color: 'rgba(255, 255, 255, 0.5)' }),
		}),
		zIndex: 500,
	});
	layer.setVisible(false);
	return layer
}

export function makeRotateCenterLayer () {
	const feature = new Feature()
	const pointStyle = new Style({
		image: new RegularShape({
			radius1: 10,
			radius2: 1,
			points: 4,
			rotateWithView: true,
			fill: new Fill({color: "#FF0000" }),
			stroke: new Stroke({
				color: "#FF0000", width: 2
			})
		})
	})
	const layer = new VectorLayer({
		source: new VectorSource({
			features: [ feature ]
		}),
		style: pointStyle,
		zIndex: 501,
	});
	return {
		layer: layer,
		feature: feature,
	}
}

export function showRotateCenter (map, layer, feature) {
	if (map && layer && feature) {
		const centerCoords = map.getView().getCenter();
		const point = new Point(centerCoords)
		feature.setGeometry(point)
		layer.setVisible(true)
	}
}

export function removeRotateCenter (layer) {
	if (layer) {
		layer.setVisible(false)
	}
}

export function setMapExtent(map, extent4326) {
	if (map) {
		const extent3857 = transformExtent(extent4326, "EPSG:4326", "EPSG:3857");
		map.getView().fit(extent3857);
	}
}
