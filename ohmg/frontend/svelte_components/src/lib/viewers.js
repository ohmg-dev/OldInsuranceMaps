import Map from 'ol/Map';
import ZoomToExtent from 'ol/control/ZoomToExtent';
import Snap from 'ol/interaction/Snap';
import Link from 'ol/interaction/Link.js';
import VectorSource from 'ol/source/Vector';
import VectorLayer from 'ol/layer/Vector';
import GeoJSON from 'ol/format/GeoJSON';

import { toGeometry } from 'ol/render/Feature';

import { containsXY } from 'ol/extent';

import { snapVertexStyle } from '../lib/ol-styles';

import { makeBasemaps } from './utils';

export class MapViewer {
  interactions = {};
  currentBasemap = null;
  // snapCandidates = []

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

    const collapseNestedCoordinates = (array, outCoords) => {
      if (!outCoords) { outCoords = [] }
      // if the first item in the list is not an array, then this is a coord
      if (!Array.isArray(array[0])) {
        outCoords.push(array)
      } else {
        array.forEach((a) => collapseNestedCoordinates(a, outCoords))
      }
      return outCoords
    }

    // this.map.on("moveend", () => {
    //   getTilesInCurrentView()
    // })

    // const self = this;
    // function getTilesInCurrentView() {
    //   const zoom = Math.floor(self.getZoom()); // Get current integer zoom level
    //   const tileGrid = layer.getSource().getTileGrid(); // Get the tile grid from the source
    //   // console.log(extent)
    //   // console.log(tileGrid)
    //   const tiles = [];
      
    //   const [minX, minY, maxX, maxY] = self.map.getView().calculateExtent(self.map.getSize())
    //   const cornerCoords = [[minX, minY], [maxX, minY], [minX, maxY], [maxX, maxY]]
    //   cornerCoords.forEach((coord) => {
    //     const tc = tileGrid.getTileCoordForCoordAndZ([coord[0], coord[1]], zoom)
    //     const tile = layer.getSource().getTile(tc[0], tc[1], tc[2], 1, layer.getSource().getProjection())

    //   });
    //   // const blTc = tileGrid.getTileCoordForCoordAndZ([extent[0], extent[1]], zoom)
    //   // const tlTc = tileGrid.getTileCoordForCoordAndZ([extent[0], extent[1]], zoom)
      
    //   // const tileCoord = tileGrid.getTileCoordForCoordAndZ([extent[0], extent[1]], zoom)
    //   // console.log(tile)


    //   console.log(`Tiles intersecting view at zoom ${zoom}:`, tiles);
    //   return tiles;
    // }

    // layer.getSource().on("tileloadend", (evt) => {
    //   evt.tile.getFeatures().forEach((f) => {
    //     const featCoords = collapseNestedCoordinates(toGeometry(f).getCoordinates());
    //     const featCoordsInTileExtent = featCoords.filter(i => containsXY(evt.tile.extent, i[0], i[1]))
    //     self.snapCandidates.push(...featCoordsInTileExtent)
    //   });
    // })

    const refreshSnapSource = () => {
      snapSource.clear();
      if (this.getZoom() >= snapMinZoom && layer.getVisible()) {

        const currentExtent = this.map.getView().calculateExtent()

        const usedCoords = []

        // method 1: pull from all points that have been loaded and add those in view
        // this.snapCandidates.forEach((coord) => {
        //   const coordRnd = [parseFloat(coord[0].toFixed(6)), parseFloat(coord[1].toFixed(6))]
        //   const coordStr = coordRnd.toString()
        //     if (!usedCoords.includes(coordStr)) {
        //       if (containsXY(currentExtent, coord[0], coord[1])) {
        //         const geoJsonGeom = { coordinates: coordRnd, type: 'Point' };
        //         const pnt = new GeoJSON().readFeature(geoJsonGeom, {
        //           dataProjection: 'EPSG:3857',
        //         });
        //         snapSource.addFeature(pnt);
        //         usedCoords.push(coordStr)
        //       }
        //     }
        // })

        // method 2: iterate visible features and only add points that are within view
        layer.getFeaturesInExtent(currentExtent).forEach((f) => {
          const featCoords = collapseNestedCoordinates(toGeometry(f).getCoordinates());
          featCoords.forEach((coord) => {
            const coordRnd = [parseFloat(coord[0].toFixed(6)), parseFloat(coord[1].toFixed(6))]
            const coordStr = coordRnd.toString()
            if (!usedCoords.includes(coordStr)) {
              if (containsXY(currentExtent, coord[0], coord[1])) {
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
