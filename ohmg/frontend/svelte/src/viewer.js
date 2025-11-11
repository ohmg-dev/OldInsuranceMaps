import Viewer from './components/Viewer.svelte';

export default new Viewer({
  target: document.getElementById('viewer-target'),
  props: JSON.parse(document.getElementById('viewer-props').textContent),
});
