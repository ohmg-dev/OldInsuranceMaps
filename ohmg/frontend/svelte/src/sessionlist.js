import SessionList from './components/lists/SessionList.svelte';

export default new SessionList({
  target: document.getElementById('sessionlist-target'),
  props: JSON.parse(document.getElementById('sessionlist-props').textContent),
});
