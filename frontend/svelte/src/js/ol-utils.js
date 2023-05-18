import VectorSource from 'ol/source/Vector';
import ImageStatic from 'ol/source/ImageStatic';
import OSM from 'ol/source/OSM';
import XYZ from 'ol/source/XYZ';
import TileWMS from 'ol/source/TileWMS';

import {transformExtent} from 'ol/proj';

import Feature from 'ol/Feature';
import Polygon from 'ol/geom/Polygon';
import Point from 'ol/geom/Point';

import Style from 'ol/style/Style';
import Fill from 'ol/style/Fill';
import Stroke from 'ol/style/Stroke';
import RegularShape from 'ol/style/RegularShape';

import TileLayer from 'ol/layer/Tile';
import VectorLayer from 'ol/layer/Vector';
import LayerGroup from 'ol/layer/Group';
import MapboxVector from 'ol/layer/MapboxVector';

function makeSatelliteLayer (apiKey) {
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

function makeMapboxStreetsLayer (apiKey) {
//  return new TileLayer({
//    source: new XYZ({
//      url: 'https://api.mapbox.com/styles/v1/legiongis/ckihiobcu0m3319sz4i5djtaj/tiles/{z}/{x}/{y}?access_token='+apiKey,
//      tileSize: 512,
//      attributions: [
//        `© <a href="https://www.mapbox.com/about/maps/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> <strong><a href="https://www.mapbox.com/map-feedback/" target="_blank">Improve this map</a></strong>`
//      ]
//    })
//  });
  return new MapboxVector({
//    styleUrl: 'mapbox://styles/legiongis/ckihiobcu0m3319sz4i5djtaj',
    styleUrl: 'mapbox://styles/mapbox/streets-v11',
    accessToken: apiKey,
    zIndex: 0,
    // declutter false keeps the labels with the rest of the style instead of
    // placing them above all other layers. However, it causes a lot of clutter.
    declutter: false,
  })
}

function makeOSMLayer () {
  return new TileLayer({
    source: new OSM({
      attributions: [
        `© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors.`
      ]
    }),
  })
}

export function makeGroupLayerFromVolume(volume, layerSet, titilerHost, excludeLayerId) {

  const lyrGroup = new LayerGroup();

  let layerDefs = [];
  if (layerSet === "main") {
    layerDefs = volume.sorted_layers.main;
  } else if (layerSet === "key-map") {
    layerDefs = volume.sorted_layers.key_map
  } else {
    console.log("invalid layerSet requested:" + layerSet)
    return
  }

  if (layerDefs.length === 0) { return false }

  layerDefs.forEach( function(layerDef) {

    if (layerDef.id == excludeLayerId) { return }

    // create the actual ol layers and add to group.
    const u = new Utils()
    let newLayer = new TileLayer({
      source: new XYZ({
        url: u.makeTitilerXYZUrl(titilerHost, layerDef.urls.cog),
      }),
      extent: transformExtent(layerDef.extent, "EPSG:4326", "EPSG:3857")
    });

    lyrGroup.getLayers().push(newLayer)

    if (volume.multimask) {
      Object.entries(volume.multimask).forEach(kV => {
        if (kV[0] == layerDef.slug) {
          const feature = new GeoJSON().readFeature(kV[1])
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
  });

  return lyrGroup
}

class Utils {

  generateFullMaskLayer = function (map) {
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

  makeRotateCenterLayer = function () {
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

  showRotateCenter = function (map, layer, feature) {
    if (map && layer && feature) {
      const centerCoords = map.getView().getCenter();
      const point = new Point(centerCoords)
      feature.setGeometry(point)
      layer.setVisible(true)
    }
  }

  removeRotateCenter = function (layer) {
    if (layer) {
      layer.setVisible(false)
    }
  }

  makeBasemaps = function (mapboxKey) {
    const osmLayer = makeOSMLayer();
    //const osmLayer = makeMapboxStreetsLayer(mapboxKey);
    const satelliteLayer = makeSatelliteLayer(mapboxKey)
    return [
      { id: "osm", layer: osmLayer, label: "Streets" },
      { id: "satellite", layer: satelliteLayer, label: "Streets+Satellite" },
    ]
  }

  makeTitilerXYZUrl = function (host, cogUrl, doubleEncode) {
    const encodedCog = encodeURIComponent(cogUrl)
    let finalURL;
    if (String(cogUrl).endsWith(".json")) {
      finalURL = host +"/mosaicjson/tiles/{z}/{x}/{y}.png?TileMatrixSetId=WebMercatorQuad&url=" + encodedCog;
    } else {
      finalURL = host +"/cog/tiles/{z}/{x}/{y}.png?TileMatrixSetId=WebMercatorQuad&url=" + encodedCog;
    }
    if (doubleEncode) {
      return encodeURIComponent(finalURL)
    } else {
      return finalURL
    }
  }

  makeLayerGroupFromVolume = function(volume, layerSet, excludeId) {
    return makeLayerGroupFromVolume(volume, layerSet, excludeId)
  }

}

export default Utils
