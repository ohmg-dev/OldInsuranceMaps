import Map from 'ol/Map';
import ZoomToExtent from 'ol/control/ZoomToExtent';
import Draw from 'ol/interaction/Draw';
import Link from 'ol/interaction/Link.js';

import { makeBasemaps } from './utils';

export class MapViewer {
  interactions = {};
  currentBasemap = null;

  constructor(elementId) {
    const targetElement = document.getElementById(elementId);
    const map = new Map({
      target: targetElement,
      maxTilesLoading: 32,
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
}
