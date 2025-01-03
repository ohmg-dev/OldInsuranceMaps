import Map from 'ol/Map';
import ZoomToExtent from 'ol/control/ZoomToExtent';

import { makeBasemaps } from '@lib/utils';

export class MapViewer {

  constructor (elementId) {
    const targetElement = document.getElementById(elementId);
    this.map = new Map({
      target: targetElement,
    });
  }

  setLayers(layersArr) {
    this.map.setLayers(layersArr)
  }
  setExtent(extent) {
    this.map.getView().fit(extent)
  }
  setView(view) {
    this.map.setView(view)
  }

  addBasemaps(mapboxApiKey, defaultId) {
    this.basemaps = makeBasemaps(mapboxApiKey)
    const defaultBasemap = defaultId == "satellite" ? this.basemaps[1] : this.basemaps[0]
    this.addLayer(defaultBasemap.layer)
  }
  addControl(control) {
    this.map.addControl(control)
  }
  addLayer(layer) {
    this.map.addLayer(layer)
  }
  addZoomToExtentControl(extent, elementId) {
    this.map.addControl(new ZoomToExtent({
      extent: extent,
      label: document.getElementById(elementId),
    }))
  }

  getZoom() {
    return Math.round(this.map.getView().getZoom() * 10) / 10
  }
}
