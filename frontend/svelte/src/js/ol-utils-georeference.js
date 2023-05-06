import VectorSource from 'ol/source/Vector';
import ImageStatic from 'ol/source/ImageStatic';
import OSM from 'ol/source/OSM';
import XYZ from 'ol/source/XYZ';
import TileWMS from 'ol/source/TileWMS';

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

function makeSatelliteLayer (apiKey) {
  return new TileLayer({
    source: new XYZ({
      url: 'https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v10/tiles/{z}/{x}/{y}?access_token='+apiKey,
      tileSize: 512,
    })
  });
}

function makeOSMLayer () {
  return new TileLayer({
    source: new OSM(),
  })
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
    const satelliteLayer = makeSatelliteLayer(mapboxKey)
    return [
      { id: "osm", layer: osmLayer, label: "Streets" },
      { id: "satellite", layer: satelliteLayer, label: "Streets+Satellite" },
    ]
  }

}

export default Utils