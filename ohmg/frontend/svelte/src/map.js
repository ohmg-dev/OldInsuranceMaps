import '@src/css/shared.css';
import '@src/css/interface.css';

import Map from '@src/lib/components/overviews/Map.svelte';
import '@src/css/ol-overrides.css'

const map = new Map({
	target: document.getElementById("map-target"),
	props: JSON.parse(document.getElementById("map-props").textContent),
});

export default map;