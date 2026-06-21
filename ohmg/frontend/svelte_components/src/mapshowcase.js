import MapShowcase from './components/home/MapShowcase.svelte';

export default new MapShowcase({
  target: document.getElementById('mapshowcase-target'),
  props: JSON.parse(document.getElementById('mapshowcase-props').textContent),
});
