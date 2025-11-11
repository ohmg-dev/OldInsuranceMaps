import './css/shared.css';
import './css/interface.css';

import Map from './components/Map.svelte';
import './css/ol-overrides.css';

export default new Map({
  target: document.getElementById('map-target'),
  props: JSON.parse(document.getElementById('map-props').textContent),
});
