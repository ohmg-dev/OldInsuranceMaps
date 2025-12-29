import MousePosition from 'ol/control/MousePosition';
import ScaleLine from 'ol/control/ScaleLine';
import { createStringXY } from 'ol/coordinate';
import { containsXY } from 'ol/extent';

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
