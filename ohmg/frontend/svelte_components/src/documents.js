import Documents from './components/tables/Documents.svelte';

export default new Documents({
  target: document.getElementById('documents-target'),
  props: JSON.parse(document.getElementById('documents-props').textContent),
});
