import Map from 'ol/Map';
import ZoomToExtent from 'ol/control/ZoomToExtent';
import Snap from 'ol/interaction/Snap';
import Link from 'ol/interaction/Link.js';
import VectorSource from 'ol/source/Vector';
import VectorLayer from 'ol/layer/Vector';
import GeoJSON from 'ol/format/GeoJSON';
import { inflateCoordinatesArray } from 'ol/geom/flat/inflate';

import { containsXY } from 'ol/extent';

import { snapVertexStyle } from '../lib/ol-styles';

import { makeBasemaps } from './utils';

export class MapViewer {
  interactions = {};
  currentBasemap = null;

  constructor(elementId, maxTilesLoading) {
    if (!maxTilesLoading) {
      maxTilesLoading = 32;
    }
    const targetElement = document.getElementById(elementId);
    const map = new Map({
      target: targetElement,
      maxTilesLoading: maxTilesLoading,
      pixelRatio: 2,
    });

    // add transition actions to the map element, used in Georeferencing interface
    function updateMapSize() {
      map.updateSize();
    }
    targetElement.style.transition = 'width .5s';
    targetElement.addEventListener('transitionend', updateMapSize);

    this.map = map;
    this.element = targetElement;
  }

  setDefaultExtent(extent) {
    this.defaultExtent = extent;
  }
  resetExtent() {
    this.map.getView().setRotation(0);
    this.setExtent(this.defaultExtent);
  }
  setExtent(extent) {
    this.map.getView().fit(extent, { padding: [25, 25, 25, 25] });
  }
  setLayers(layersArr) {
    this.map.setLayers(layersArr);
  }
  setView(view) {
    this.map.setView(view);
  }
  setBasemap(basemapId) {
    const useLayer = this.basemaps.filter((item) => item.id == basemapId);
    if (useLayer) {
      this.map.getLayers().removeAt(0);
      this.map.getLayers().insertAt(0, useLayer[0].layer);
      this.currentBasemap = useLayer;
    }
  }
  toggleBasemap() {
    this.currentBasemap.id == 'satellite' ? this.setBasemap('osm') : this.setBasemap('satellite');
  }

  addBasemaps(mapboxApiKey, defaultId) {
    this.basemaps = makeBasemaps(mapboxApiKey);
    const defaultBasemap = defaultId == 'satellite' ? this.basemaps[1] : this.basemaps[0];
    this.map.getLayers().insertAt(0, defaultBasemap.layer);
    this.currentBasemap = defaultBasemap;
  }
  addControl(control) {
    this.map.addControl(control);
  }
  addLayer(layer) {
    this.map.addLayer(layer);
  }
  addLayers(layerArray) {
    const self = this;
    layerArray.forEach(function (layer) {
      self.map.addLayer(layer);
    });
  }
  addOverlay(overlay) {
    this.map.addOverlay(overlay);
  }
  addZoomToExtentControl(extent, elementId) {
    this.map.addControl(
      new ZoomToExtent({
        extent: extent,
        label: document.getElementById(elementId),
      }),
    );
  }

  addInteraction(id, interaction) {
    this.map.addInteraction(interaction);
    this.interactions[id] = interaction;
  }
  clearNonBasemapLayers() {
    // iterate down the list of layers (by index number) and remove down to 0
    const lyrCt = this.map.getLayers().getArray().length;
    Array.from({ length: lyrCt }, (e, i) => i)
      .reverse()
      .forEach((i) => {
        // don't remove the 0 index layer as that's the basemap
        if (i != 0) {
          this.map.getLayers().removeAt(i);
        }
      });
  }

  getZoom() {
    return Math.round(this.map.getView().getZoom() * 10) / 10;
  }

  addSnappableVectorLayer(layer, visMinZoom, snapMinZoom, activeStyle, inactiveStyle) {

    const snapSource = new VectorSource({
      overlaps: false,
    });
    const snapLayer = new VectorLayer({
      source: snapSource,
      zIndex: layer.get("zIndex") + 1,
      style: snapVertexStyle,
    });

    const snap = new Snap({
      source: snapSource,
    });
    this.addInteraction('parcelSnap', snap);

    const refreshSnapSource = () => {
      snapSource.clear();
      const usedCoords = []
      const mapExtent = this.map.getView().calculateExtent()
      if (this.getZoom() >= snapMinZoom) {
        const features = layer.getFeaturesInExtent(mapExtent);
        features.forEach((feature) => {
          // IDEA: used these later to check and exclude exact corner coords
          // (i.e. corners of the actual vector tiles)
          // ref: https://github.com/openlayers/openlayers/issues/17328
          // const [minX, minY, maxX, maxY] = feature.getExtent()
          // const cornerCoords = [[minX, minY], [maxX, minY], [minX, maxY], [maxX, maxY]]
          const coordsArray = inflateCoordinatesArray(
            feature.getFlatCoordinates(), // flat coordinates
            0, // offset
            feature.getEnds(), // geometry end indices
            2, // stride
          );
          coordsArray.forEach((lineCoords) => {
            lineCoords.forEach((coord) => {
              const coordRnd = [parseFloat(coord[0].toFixed(6)), parseFloat(coord[1].toFixed(6))]
              const coordStr = coordRnd.toString()
              if (!usedCoords.includes(coordStr)) {
                if (containsXY(mapExtent, coordRnd[0], coordRnd[1])) {
                  const geoJsonGeom = { coordinates: coordRnd, type: 'Point' };
                  const pnt = new GeoJSON().readFeature(geoJsonGeom, {
                    dataProjection: 'EPSG:3857',
                  });
                  snapSource.addFeature(pnt);
                  usedCoords.push(coordStr)
                }
              }
            });
          });
        });
      }
    }

    this.map.on('moveend', () => {
      refreshSnapSource()
    });

    layer.on('change:visible', () => {
      if (layer.getVisible()) {
        layer.once('postrender', () => {
          setTimeout(refreshSnapSource, 500)
        })
      } else {
        snapSource.clear()
      }
    })

    this.map.getView().on('change:resolution', () => {
      const currentZoom = this.getZoom();
      // first handle the presence of this layer at all
      if (currentZoom < visMinZoom) {
        this.map.removeLayer(layer)
      } else {
        if (!this.map.getLayers().getArray().includes(layer)) {
          this.map.addLayer(layer)
        }
      }
      // now handle style based on whether it is snappable or not
      if (currentZoom < snapMinZoom) {
        layer.setStyle(inactiveStyle)
      } else {
        layer.setStyle(activeStyle)
        if (!this.map.getLayers().getArray().includes(snapLayer)) {
          this.map.addLayer(snapLayer)
        }
      }
    });
  }
}
