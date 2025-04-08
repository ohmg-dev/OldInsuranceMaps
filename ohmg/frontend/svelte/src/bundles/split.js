import '../css/interface.css';
import Splitter from '../components/Splitter.svelte';
import '../css/ol-overrides.css';

const app = new Splitter({
  target: document.getElementById('split-target'),
  props: JSON.parse(document.getElementById('split-props').textContent),
});

export default app;
