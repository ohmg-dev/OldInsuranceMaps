import Profiles from './components/tables/Profiles.svelte';

export default new Profiles({
  target: document.getElementById('profiles-target'),
  props: JSON.parse(document.getElementById('profiles-props').textContent),
});
