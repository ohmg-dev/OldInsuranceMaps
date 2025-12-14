import Sessions from './components/tables/Sessions.svelte';

export default new Sessions({
  target: document.getElementById('sessions-target'),
  props: JSON.parse(document.getElementById('sessions-props').textContent),
});
