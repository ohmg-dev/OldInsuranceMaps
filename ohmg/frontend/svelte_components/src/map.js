import Map from './components/map/Map.svelte';

export default new Map({
  target: document.getElementById('map-target'),
  props: JSON.parse(document.getElementById('map-props').textContent),
});
