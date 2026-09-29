import Layers from './components/tables/Layers.svelte';

export default new Layers({
  target: document.getElementById('layers-target'),
  props: JSON.parse(document.getElementById('layers-props').textContent),
});
