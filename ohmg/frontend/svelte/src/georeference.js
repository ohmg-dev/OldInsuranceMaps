import './css/interface.css';
import Georeferencer from './components/Georeferencer.svelte';
import './css/ol-overrides.css';

export default new Georeferencer({
  target: document.getElementById('georeference-target'),
  props: JSON.parse(document.getElementById('georeference-props').textContent),
});
