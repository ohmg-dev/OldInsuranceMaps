import Maps from './components/tables/Maps.svelte';

export default new Maps({
  target: document.getElementById('maps-target'),
  props: JSON.parse(document.getElementById('maps-props').textContent),
});
