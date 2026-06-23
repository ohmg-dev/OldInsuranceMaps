import Jobs from './components/tables/Jobs.svelte';

export default new Jobs({
  target: document.getElementById('jobs-target'),
  props: JSON.parse(document.getElementById('jobs-props').textContent),
});
