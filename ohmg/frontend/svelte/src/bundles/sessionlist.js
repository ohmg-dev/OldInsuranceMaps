import '../css/interface.css';
import SessionList from '../components/lists/SessionList.svelte';
import '../css/ol-overrides.css';

const app = new SessionList({
  target: document.getElementById('sessionlist-target'),
  props: JSON.parse(document.getElementById('sessionlist-props').textContent),
});

export default app;
