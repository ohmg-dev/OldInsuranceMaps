import Splitter from './components/interfaces/Splitter.svelte';

export default new Splitter({
  target: document.getElementById('split-target'),
  props: JSON.parse(document.getElementById('split-props').textContent),
});
