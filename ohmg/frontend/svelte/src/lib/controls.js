import MousePosition from 'ol/control/MousePosition';
import {createStringXY} from 'ol/coordinate';

import { containsXY } from 'ol/extent';

export class LyrMousePosition {
	constructor(elementId) {
		return new MousePosition({
			projection: 'EPSG:4326',
			coordinateFormat: createStringXY(6),
			placeholder: 'n/a',
			target: document.getElementById(elementId),
			className: null,
		});
	}
}

export class DocMousePosition {
	constructor(elementId, extent, projection) {

		function coordinateFormat(coordinate) {
			if (containsXY(extent, coordinate[0], coordinate[1])) {  
				const x = Math.round(coordinate[0]);
				const y = -Math.round(coordinate[1]);
				return `${x}, ${y}`
			} else {
				return 'n/a'
			}
		}

		return new MousePosition({
			coordinateFormat: coordinateFormat,
			projection: projection,
			placeholder: 'n/a',
			target: document.getElementById(elementId),
			className: null,
		});
	}
}

