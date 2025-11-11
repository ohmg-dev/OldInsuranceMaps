import './css/interface.css';
import Browse from './components/overviews/Browse.svelte';

export default new Browse({
  target: document.getElementById('browse-target'),
  props: JSON.parse(document.getElementById('browse-props').textContent),
});
