import Resource from './components/resource/Resource.svelte';

export default new Resource({
  target: document.getElementById('resource-target'),
  props: JSON.parse(document.getElementById('resource-props').textContent),
});
