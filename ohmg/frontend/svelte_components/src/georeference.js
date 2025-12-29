import Georeferencer from './components/Georeferencer.svelte';

export default new Georeferencer({
  target: document.getElementById('georeference-target'),
  props: JSON.parse(document.getElementById('georeference-props').textContent),
});
