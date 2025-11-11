import './css/shared.css';
import Place from './components/overviews/Place.svelte';

export default new Place({
  target: document.getElementById('place-target'),
  props: JSON.parse(document.getElementById('place-props').textContent),
});
