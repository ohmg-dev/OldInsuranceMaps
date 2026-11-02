import MousePosition from 'ol/control/MousePosition';
import ScaleLine from 'ol/control/ScaleLine';
import { createStringXY } from 'ol/coordinate';
import { containsXY } from 'ol/extent';

import { toLonLat, transformExtent } from 'ol/proj';
import ContextMenu from 'ol-contextmenu';

export class LyrMousePosition {
  constructor(elementId, className) {
    const control = new MousePosition({
      projection: 'EPSG:4326',
      coordinateFormat: createStringXY(6),
      placeholder: 'n/a',
      className: className,
    });
    if (elementId) {
      control.setTarget(document.getElementById(elementId));
    }
    return control;
  }
}

export class DocMousePosition {
  constructor(extent, elementId, className) {
    function coordinateFormat(coordinate) {
      if (containsXY(extent, coordinate[0], coordinate[1])) {
        const x = Math.round(coordinate[0]);
        const y = -Math.round(coordinate[1]);
        return `${x}, ${y}`;
      } else {
        return 'n/a';
      }
    }
    const control = new MousePosition({
      coordinateFormat: coordinateFormat,
      placeholder: 'n/a',
      className: className,
    });
    if (elementId) {
      control.setTarget(document.getElementById(elementId));
    }

    return control;
  }
}

export class MapScaleLine {
  constructor() {
    return new ScaleLine({
      units: 'us',
    });
  }
}

export class ContextMenuControl {
  constructor(map) {
    const view = map.getView();
    const contextmenu = new ContextMenu({
        width: 200,
        defaultItems: false,
    });
    contextmenu.on('open', async (evt) => {

      const [lon, lat] = toLonLat(contextmenu.coordinate)
      const lonLatStr = `${lat.toFixed(5)}, ${lon.toFixed(5)}`
      const copyLonLat = () => {
        const el = document.getElementsByClassName("copyable-coords")[0]
        navigator.clipboard.writeText(el.textContent);
        alert("Coordinates copied to clipboard (lat, long)")
      }
      const zoom = view.getZoom();
      const extent = view.calculateExtent(map.getSize());
      const bboxLatLon = transformExtent(extent, 'EPSG:3857', 'EPSG:4326');
      const bboxStr = bboxLatLon.map(coord => coord.toFixed(3));
      const copyBbox = () => {
        const el = document.getElementsByClassName("copyable-bbox")[0]
        navigator.clipboard.writeText(el.textContent);
        alert("Bounding box copied to clipboard")
      }

      contextmenu.clear()
      contextmenu.extend(contextmenu.getDefaultItems());
      contextmenu.extend([
        {
          text: 'Center map here',
          callback: (obj, map) => {
              view.animate({
                center: obj.coordinate,
                duration: 1000
              });
          },
        },
        "-",
        {
          text: "View in Mapillary &nearr;",
          callback: (obj, map) => {
            const url = `https://www.mapillary.com/app/?lat=${lat}&lng=${lon}&z=${zoom}`;
            window.open(url, '_blank');
          }
        },
        {
          text: "View in OpenHistoricalMap &nearr;",
          callback: (obj, map) => {
            const url = `https://www.openhistoricalmap.org/#map=${zoom}/${lat}/${lon}`;
            window.open(url, '_blank');
          }
        },
        "-",
        {
          text: lonLatStr,
          callback: copyLonLat,
          classname: "copyable-coords"
        },
        {
          text: bboxStr,
          callback: copyBbox,
          classname: "copyable-bbox"
        }
      ]);
    });
    return contextmenu
  }
}